"""Draeven Core: tool-first orchestration above the model Front Door."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
import json
import re
import threading
import time
import uuid

import service_connections


@dataclass
class CoreReply:
    answer: str
    route: str
    mode: str = "read-only"
    receipt: dict | None = None
    confirm_id: str | None = None


class DraevenCore:
    """Routes verified tools before models and keeps a bounded local conversation."""
    def __init__(self, history_path: Path):
        self.history_path = history_path
        self.lock = threading.RLock()
        self.history = deque(maxlen=40)
        self.pending = {}
        self._load()

    def _load(self):
        try:
            data = json.loads(self.history_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                self.history.extend(item for item in data[-40:] if isinstance(item, dict))
        except (OSError, ValueError):
            pass

    def _save(self):
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.history_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(list(self.history), ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.history_path)

    def remember(self, role: str, text: str, route: str = ""):
        with self.lock:
            self.history.append({"role":role, "text":text[:12000], "route":route, "time":int(time.time())})
            self._save()

    def context(self) -> str:
        with self.lock:
            recent = list(self.history)[-8:]
        return "\n".join(f"{item.get('role','user')}: {item.get('text','')[:1200]}" for item in recent)

    def status(self) -> dict:
        return {
            "name":"Draeven Core", "ready":True, "conversation_turns":len(self.history),
            "routing":"tool-first", "cost_policy":"local and deterministic tools before one cloud model call",
            "tools":[
                {"name":"shopify.catalog", "mode":"read", "ready":True},
                {"name":"shopify.products", "mode":"read", "ready":True},
                {"name":"shopify.product_status", "mode":"approval-gated write", "ready":True},
                {"name":"etsy.listings", "mode":"read", "ready":True},
                {"name":"vault.status", "mode":"read", "ready":True},
                {"name":"repositories", "mode":"read and approval-gated write", "ready":True},
                {"name":"wright", "mode":"verified service", "ready":True},
                {"name":"email", "mode":"unavailable until OAuth is connected", "ready":False},
            ],
        }

    @staticmethod
    def _shopify_request(text: str) -> bool:
        return bool(re.search(r"\bshopify\b", text, re.I) and
                    re.search(r"\b(card|cards|catalog|products?|listings?|available|inventory|how many|count|store)\b", text, re.I))

    @staticmethod
    def _etsy_request(text: str) -> bool:
        return bool(re.search(r"\betsy\b", text, re.I) and
                    re.search(r"\b(listings?|drafts?|active|inactive|sold|expired|shop|how many|count)\b", text, re.I))

    def respond(self, text: str, agent: str | None, upstream) -> CoreReply:
        self.remember("Semaj", text)
        try:
            if (re.search(r"\bshopify\b", text, re.I)
                    and re.search(r"\b(publish|activate|set|make|change|move|archive)\b", text, re.I)
                    and re.search(r"\b(active|draft|archive|archived)\b", text, re.I)):
                catalog = service_connections.shopify_products()
                low = text.lower()
                matches = [item for item in catalog["products"]
                           if item.get("title", "").lower() in low or item.get("handle", "").lower() in low]
                if len(matches) != 1:
                    reply = CoreReply("Name the exact Shopify product title you want to change and whether it should be active, draft, or archived.",
                                      "Draeven approval gate", "needs-detail")
                else:
                    target = matches[0]
                    status = "ARCHIVED" if re.search(r"\barchive|archived\b", text, re.I) else "DRAFT" if re.search(r"\bdraft\b", text, re.I) else "ACTIVE"
                    confirm_id = "core-" + uuid.uuid4().hex[:12]
                    self.pending[confirm_id] = {"tool":"shopify.product_status", "product_id":target["id"],
                                                "title":target["title"], "status":status}
                    reply = CoreReply(f"Ready to change Shopify product “{target['title']}” from {target['status'].lower()} to {status.lower()}. Nothing has changed yet.",
                                      "Draeven approval gate", "approval-required", confirm_id=confirm_id)
            elif self._shopify_request(text):
                summary = service_connections.shopify_catalog_summary()
                answer = (f"I checked Shopify live. You have {summary['active_greeting_cards']} active greeting-card listings "
                          f"and {summary['active_products']} active products in total. "
                          f"{summary['digital_inventory_note']}")
                reply = CoreReply(answer, "Shopify live read", receipt={"source":"Shopify Admin GraphQL", "verified":True})
            elif self._etsy_request(text):
                summary = service_connections.etsy_listing_summary()
                counts = summary["counts"]
                answer = ("I checked Etsy live. Your shop currently has "
                          f"{counts['active']} active, {counts['draft']} draft, {counts['inactive']} inactive, "
                          f"{counts['sold_out']} sold-out, and {counts['expired']} expired listings.")
                reply = CoreReply(answer, "Etsy private live read", receipt={"source":"Etsy API v3", "verified":True})
            elif re.search(r"\b(email|gmail|inbox)\b", text, re.I) and re.search(r"\b(connect|check|read|messages?|setup|set up)\b", text, re.I):
                answer = ("Email is not connected to Draeven yet. I can use Shopify, Etsy, the vault, repositories, and Wright, "
                          "but email requires a separate OAuth connection before I can read or draft against a real inbox.")
                reply = CoreReply(answer, "Draeven capability registry")
            else:
                context = self.context()
                data = upstream('/ask', {'text':text, 'agent':agent, 'context':context}, timeout=720)
                answer = data.get('answer')
                if not isinstance(answer, str) or not answer.strip():
                    raise ValueError("The response model returned an empty answer.")
                route = data.get('route', 'Draeven model route')
                executable = bool(data.get('confirm_id') and 'repository worker' in route)
                if data.get('confirm_id') and not executable:
                    answer = answer.strip() + "\n\nThis is a proposal only. Draeven Core has no registered executor for this action, so no approval button was created."
                reply = CoreReply(answer.strip(), route, mode='approval-gated' if executable else 'advice',
                                  confirm_id=data.get('confirm_id') if executable else None)
        except service_connections.ConnectionError as exc:
            reply = CoreReply(f"The connected service could not complete that read: {exc}", "Draeven tool error", "error")
        self.remember("Draeven", reply.answer, reply.route)
        return reply

    def confirm(self, confirm_id: str) -> CoreReply | None:
        action = self.pending.pop(confirm_id, None)
        if not action:
            return None
        if action["tool"] == "shopify.product_status":
            result = service_connections.shopify_set_product_status(action["product_id"], action["status"])
            product = result["product"]
            answer = f"Shopify verified that “{product['title']}” is now {product['status'].lower()}."
            receipt = {"id":"shopify-" + uuid.uuid4().hex[:12], "status":"executed", "executed":True,
                       "source":"Shopify Admin GraphQL", "product_id":product["id"], "verified":True}
            self.remember("Draeven", answer, "Shopify approved write")
            return CoreReply(answer, "Shopify approved write", "executed", receipt=receipt)
        raise service_connections.ConnectionError("The approved Draeven tool is not registered.")
