#!/usr/bin/env python3
"""Wright Connector demo-call control plane (Phase 3 vertical slice, HVAC only).

Isolated from control_plane.py/card_orchestrator.py (O&L) -- separate venture,
separate job-id prefix, no shared state. Mirrors their job.json/audit_log
conventions on purpose. See "Wright Connector - Phase 2 Design.md" in the
vault for the approved data model and tool contracts this implements.

Demo-only: no real dispatch, no real emergency claims, no invented
appointment availability, no duplicate SMS. See
"Wright Connector Demo - Build Brief.md" for the full safety rules.
"""
from __future__ import annotations

import datetime as dt
import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).parent
JOBS = ROOT / "jobs"
PROFILES = ROOT / "wright_profiles"

TRUTHFUL_STATUSES = {"received", "captured", "simulated", "sent", "failed", "needs_human_review"}
TWILIO_CREDENTIAL_TARGET = "Draeven/Twilio/Connection"

CALL_FORWARD: dict[str, set[str]] = {
    "CALL_RECEIVED": {"PROFILE_LOADED"},
    "PROFILE_LOADED": {"LEAD_CAPTURING", "ESCALATED"},
    "LEAD_CAPTURING": {"LEAD_CAPTURED", "ESCALATED", "NEEDS_HUMAN_REVIEW", "FAILED"},
    "LEAD_CAPTURED": {"APPOINTMENT_CHECKING", "NOTIFYING"},
    "APPOINTMENT_CHECKING": {"APPOINTMENT_SIMULATED", "APPOINTMENT_UNAVAILABLE", "FAILED"},
    "APPOINTMENT_SIMULATED": {"NOTIFYING"},
    "APPOINTMENT_UNAVAILABLE": {"NOTIFYING"},
    "NOTIFYING": {"RECEIPT_RECORDED"},
    "ESCALATED": {"RECEIPT_RECORDED"},
    "NEEDS_HUMAN_REVIEW": {"RECEIPT_RECORDED"},
    "FAILED": {"RECEIPT_RECORDED"},
    "RECEIPT_RECORDED": set(),
}


class ControlPlaneError(RuntimeError):
    pass


class _Credential(ctypes.Structure):
    _fields_ = [("Flags",wintypes.DWORD),("Type",wintypes.DWORD),("TargetName",wintypes.LPWSTR),
        ("Comment",wintypes.LPWSTR),("LastWritten",wintypes.FILETIME),("CredentialBlobSize",wintypes.DWORD),
        ("CredentialBlob",ctypes.POINTER(ctypes.c_ubyte)),("Persist",wintypes.DWORD),
        ("AttributeCount",wintypes.DWORD),("Attributes",ctypes.c_void_p),("TargetAlias",wintypes.LPWSTR),
        ("UserName",wintypes.LPWSTR)]


def twilio_credentials() -> dict[str, str]:
    pointer = ctypes.POINTER(_Credential)()
    api = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    read = api.CredReadW
    read.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p)
    read.restype = wintypes.BOOL
    free = api.CredFree
    free.argtypes = (ctypes.c_void_p,)
    if read(TWILIO_CREDENTIAL_TARGET, 1, 0, ctypes.byref(pointer)):
        try:
            item = pointer.contents
            raw = ctypes.string_at(item.CredentialBlob, item.CredentialBlobSize).decode("utf-16-le")
            value = json.loads(raw)
            if isinstance(value, dict):
                return {str(k): str(v) for k, v in value.items()}
        except (ValueError, UnicodeError):
            pass
        finally:
            free(pointer)
    return {
        "account_sid": os.environ.get("TWILIO_ACCOUNT_SID", ""),
        "auth_token": os.environ.get("TWILIO_AUTH_TOKEN", ""),
        "from_number": os.environ.get("TWILIO_FROM_NUMBER", ""),
        "owner_number": os.environ.get("TWILIO_OWNER_NUMBER", ""),
    }


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def job_id_for(call_id: str) -> str:
    return f"WRIGHT-CALL-{call_id}"


def job_path(call_id: str) -> Path:
    if not call_id or any(ch in call_id for ch in "\\/:"):
        raise ControlPlaneError("call_id must be a non-empty safe folder name.")
    return JOBS / job_id_for(call_id) / "job.json"


def load(call_id: str) -> dict[str, Any]:
    path = job_path(call_id)
    if not path.is_file():
        raise ControlPlaneError(f"No call job for {call_id}. Call load_industry_profile first.")
    return json.loads(path.read_text(encoding="utf-8"))


def save(job: dict[str, Any]) -> None:
    path = job_path(job["call_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(job, indent=2) + "\n", encoding="utf-8")


def event(job: dict[str, Any], actor: str, action: str, detail: str) -> None:
    job["audit_log"].append({"at": now(), "actor": actor, "action": action, "detail": detail})


def transition(job: dict[str, Any], to: str) -> None:
    old = job["state"]
    if to not in CALL_FORWARD.get(old, set()):
        raise ControlPlaneError(f"Illegal transition {old} -> {to}.")
    job["state"] = to
    event(job, "Jarvis", "STATE_TRANSITION", f"{old} -> {to}")


def already_done(job: dict[str, Any], action_type: str) -> bool:
    """Idempotency guard for genuinely side-effecting actions (appointments,
    SMS sends). Read-only/accumulating actions don't call this."""
    key = f"{job['call_id']}:{action_type}"
    return key in job["idempotency_keys_seen"]


def load_profile(industry_or_id: str) -> dict[str, Any]:
    needle = industry_or_id.strip().lower()
    if not PROFILES.is_dir():
        raise ControlPlaneError("No industry profiles directory found.")
    for path in sorted(PROFILES.glob("*.json")):
        profile = json.loads(path.read_text(encoding="utf-8"))
        if needle in (profile.get("id", "").lower(), profile.get("industry", "").lower()):
            return profile
    raise ControlPlaneError(f"No industry profile matches '{industry_or_id}'.")


def new_job(call_id: str) -> dict[str, Any]:
    return {
        "call_id": call_id,
        "job_id": job_id_for(call_id),
        "venture": "wright-connector",
        "lane": "demo-call",
        "industry_profile": None,
        "state": "CALL_RECEIVED",
        "caller_fields": {},
        "appointment": None,
        "notifications": [],
        "escalation": None,
        "idempotency_keys_seen": [],
        "idempotency_results": {},
        "evidence_receipt": None,
        "audit_log": [],
    }


# ---- Twilio (real send only if configured; otherwise clearly logged as skipped) ----

def send_sms(to_number: str, body: str) -> dict[str, Any]:
    credentials = twilio_credentials()
    sid = credentials.get("account_sid")
    token = credentials.get("auth_token")
    from_number = credentials.get("from_number")
    if not (sid and token and from_number and to_number):
        return {"sent": False, "reason": "twilio_not_configured"}
    try:
        from twilio.rest import Client  # imported lazily so the module loads without the package
        client = Client(sid, token)
        message = client.messages.create(body=body, from_=from_number, to=to_number)
        return {"sent": True, "sid": message.sid, "twilio_status": message.status}
    except Exception as exc:  # Twilio errors, network errors, bad numbers, etc.
        # A transport error can happen after Twilio accepted the message. Do not
        # blindly retry: a human must reconcile the provider console first.
        return {"sent": False, "outcome_unknown": True, "reason": str(exc)}


def _prior_sms_result(job: dict[str, Any], action_type: str) -> dict[str, Any]:
    prior = job.get("idempotency_results", {}).get(action_type)
    if prior and prior.get("status") == "sent":
        return {"status": "sent", "note": "provider accepted the earlier send; not duplicated",
                "detail": prior.get("detail", {})}
    if prior and prior.get("status") == "failed":
        return {"status": "failed", "note": "earlier attempt failed before provider acceptance; not duplicated",
                "detail": prior.get("detail", {})}
    return {"status": "needs_human_review",
            "note": "an earlier attempt may have reached the provider; reconcile before retrying"}


def _record_sms_result(job: dict[str, Any], action_type: str, status: str,
                       detail: dict[str, Any]) -> None:
    key = f"{job['call_id']}:{action_type}"
    if key not in job["idempotency_keys_seen"]:
        job["idempotency_keys_seen"].append(key)
    job.setdefault("idempotency_results", {})[action_type] = {"status": status, "detail": detail}


def _clear_sms_attempt(job: dict[str, Any], action_type: str) -> None:
    key = f"{job['call_id']}:{action_type}"
    job["idempotency_keys_seen"] = [item for item in job["idempotency_keys_seen"] if item != key]
    job.setdefault("idempotency_results", {}).pop(action_type, None)


# ---- Tool implementations (one per Build Brief tool) ----

def tool_load_industry_profile(call_id: str, industry: str) -> dict[str, Any]:
    path = job_path(call_id)
    job = load(call_id) if path.is_file() else new_job(call_id)
    try:
        profile = load_profile(industry)
    except ControlPlaneError:
        event(job, "Jarvis", "PROFILE_LOAD_FAILED", f"No profile for '{industry}'")
        save(job)
        return {"status": "failed", "reason": f"no profile configured for '{industry}' yet"}
    job["industry_profile"] = profile["id"]
    if job["state"] == "CALL_RECEIVED":
        transition(job, "PROFILE_LOADED")
    event(job, "Jarvis", "PROFILE_LOADED", profile["id"])
    save(job)
    return {
        "status": "received",
        "industry_profile": profile["id"],
        "greeting": profile["greeting"],
        "demonstration_disclaimer": profile["demonstration_disclaimer"],
        "required_caller_fields": profile["required_caller_fields"],
    }


def tool_get_business_information(call_id: str, question: str) -> dict[str, Any]:
    job = load(call_id)
    if not job["industry_profile"]:
        raise ControlPlaneError("No industry profile loaded for this call yet.")
    profile = load_profile(job["industry_profile"])
    q = question.lower()
    for prohibited in profile["prohibited_claims"]:
        if prohibited.lower() in q:
            return {
                "status": "received",
                "answer": "A dispatcher will confirm exact specifics -- I can't quote that on this demo call.",
            }
    matches = [s for s in profile["services"] if s.lower() in q or q in s.lower()]
    if matches:
        return {"status": "received", "answer": f"Yes, we handle {', '.join(matches)}."}
    return {"status": "received", "answer": "; ".join(profile["services"])}


def tool_capture_lead(call_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    job = load(call_id)
    if not job["industry_profile"]:
        raise ControlPlaneError("No industry profile loaded for this call yet.")
    profile = load_profile(job["industry_profile"])
    if job["state"] == "PROFILE_LOADED":
        transition(job, "LEAD_CAPTURING")
    allowed = set(profile["required_caller_fields"]) | set(profile["optional_caller_fields"])
    job["caller_fields"].update({k: v for k, v in fields.items() if k in allowed})
    event(job, "Jarvis", "LEAD_FIELDS_UPDATED", ", ".join(fields.keys()))
    missing = [f for f in profile["required_caller_fields"] if not job["caller_fields"].get(f)]
    if missing:
        save(job)
        return {"status": "received", "missing_fields": missing}
    if job["state"] == "LEAD_CAPTURING":
        transition(job, "LEAD_CAPTURED")
    save(job)
    return {"status": "captured", "caller_fields": job["caller_fields"]}


def tool_check_demo_availability(call_id: str, preferred_time: str) -> dict[str, Any]:
    job = load(call_id)
    profile = load_profile(job["industry_profile"])
    if job["state"] == "LEAD_CAPTURED":
        transition(job, "APPOINTMENT_CHECKING")
    urgency = str(job["caller_fields"].get("urgency", "")).lower()
    is_urgent = urgency in {"urgent", "emergency", "high"}
    rules = profile["appointment_rules"]
    if is_urgent and rules.get("same_day_if_urgent"):
        offered = "today, as soon as a technician is available (simulated)"
    else:
        start, end = rules.get("offer_window_hours", [9, 17])
        offered = f"next business day between {start}:00 and {end}:00 (simulated)"
    event(job, "Jarvis", "AVAILABILITY_CHECKED", f"requested={preferred_time!r} offered={offered!r}")
    save(job)
    return {"status": "simulated", "offered_window": offered}


def tool_request_demo_appointment(call_id: str, confirmed_time: str) -> dict[str, Any]:
    job = load(call_id)
    if job["appointment"] is not None:
        return {"status": "simulated", "appointment": job["appointment"], "note": "already recorded, not duplicated"}
    if job["state"] == "APPOINTMENT_CHECKING":
        transition(job, "APPOINTMENT_SIMULATED")
    job["appointment"] = {"requested_time": confirmed_time, "status": "simulated", "at": now()}
    event(job, "Jarvis", "APPOINTMENT_SIMULATED", confirmed_time)
    save(job)
    return {"status": "simulated", "appointment": job["appointment"]}


def tool_send_demo_customer_sms(call_id: str) -> dict[str, Any]:
    job = load(call_id)
    profile = load_profile(job["industry_profile"])
    if already_done(job, "send_demo_customer_sms"):
        return _prior_sms_result(job, "send_demo_customer_sms")
    if not job["caller_fields"].get("sms_consent"):
        return {"status": "received", "note": "skipped -- no SMS consent on file"}
    phone = job["caller_fields"].get("callback_number")
    time_str = (job["appointment"] or {}).get("requested_time", "your requested time")
    body = profile["sms_wording"]["customer"].format(time=time_str)
    _record_sms_result(job, "send_demo_customer_sms", "in_progress", {})
    save(job)  # crash-safe guard: uncertain in-flight attempts must not be repeated
    result = send_sms(phone, body)
    job["notifications"].append({"type": "customer_sms", "at": now(), **result})
    if result.get("sent"):
        _record_sms_result(job, "send_demo_customer_sms", "sent", result)
        status = "sent"
    elif result.get("outcome_unknown"):
        _record_sms_result(job, "send_demo_customer_sms", "needs_human_review", result)
        status = "needs_human_review"
    else:
        # No provider call occurred (for example, credentials are absent), so a
        # corrected configuration may safely retry later.
        _clear_sms_attempt(job, "send_demo_customer_sms")
        status = "failed"
    if status == "sent" and job["state"] in ("APPOINTMENT_SIMULATED", "APPOINTMENT_UNAVAILABLE", "LEAD_CAPTURED"):
        transition(job, "NOTIFYING")
    save(job)
    return {"status": status, "detail": result}


def tool_send_demo_owner_alert(call_id: str, reason: str) -> dict[str, Any]:
    job = load(call_id)
    profile = load_profile(job["industry_profile"])
    if already_done(job, "send_demo_owner_alert"):
        return _prior_sms_result(job, "send_demo_owner_alert")
    owner_number = twilio_credentials().get("owner_number")
    _record_sms_result(job, "send_demo_owner_alert", "in_progress", {})
    save(job)
    result = send_sms(owner_number, profile["sms_wording"]["owner"])
    job["notifications"].append({"type": "owner_alert", "at": now(), "reason": reason, **result})
    event(job, "Jarvis", "OWNER_ALERT", reason)
    if result.get("sent"):
        _record_sms_result(job, "send_demo_owner_alert", "sent", result)
        status = "sent"
    elif result.get("outcome_unknown"):
        _record_sms_result(job, "send_demo_owner_alert", "needs_human_review", result)
        status = "needs_human_review"
    else:
        _clear_sms_attempt(job, "send_demo_owner_alert")
        status = "failed"
    save(job)
    return {"status": status, "detail": result}


def tool_escalate_to_demo_human(call_id: str, reason: str) -> dict[str, Any]:
    job = load(call_id)
    job["escalation"] = {"reason": reason, "at": now()}
    target = "ESCALATED" if job["state"] not in ("LEAD_CAPTURING",) else "NEEDS_HUMAN_REVIEW"
    if target in CALL_FORWARD.get(job["state"], set()):
        transition(job, target)
    event(job, "Jarvis", "ESCALATED", reason)
    save(job)
    alert = tool_send_demo_owner_alert(call_id, reason)
    return {"status": "needs_human_review", "alert": alert}


def tool_record_demo_receipt(call_id: str) -> dict[str, Any]:
    job = load(call_id)
    if job["evidence_receipt"] is not None:
        return {"status": job["evidence_receipt"]["final_status"], "evidence_receipt": job["evidence_receipt"]}
    receipt = {
        "call_id": call_id,
        "industry_profile": job["industry_profile"],
        "timestamp": now(),
        "captured_fields": job["caller_fields"],
        "actions_attempted": [e["action"] for e in job["audit_log"]],
        "notifications": job["notifications"],
        "appointment_result": job["appointment"],
        "escalation_result": job["escalation"],
        "final_status": (
            "needs_human_review" if job["escalation"] or any(n.get("outcome_unknown") for n in job["notifications"])
            else "failed" if any(n.get("sent") is False for n in job["notifications"])
            else "captured"
        ),
    }
    job["evidence_receipt"] = receipt
    if job["state"] in CALL_FORWARD and "RECEIPT_RECORDED" in CALL_FORWARD.get(job["state"], set()):
        transition(job, "RECEIPT_RECORDED")
    else:
        job["state"] = "RECEIPT_RECORDED"
        event(job, "Jarvis", "STATE_TRANSITION", "forced -> RECEIPT_RECORDED (receipt recorded from an unexpected state)")
    save(job)
    return {"status": receipt["final_status"], "evidence_receipt": receipt}
