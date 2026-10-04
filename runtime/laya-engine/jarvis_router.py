"""JARVIS router: uses the REAL Laya model to decide, for any request,
which business it belongs to, which tool should handle it, and whether it
needs Semaj's approval. Laya only decides; the chosen tool does the work.

CLI:   python jarvis_router.py "make a birthday card for Crystal"
       python jarvis_router.py --test          (runs 8 sample requests, writes router_test_result.txt)
Code:  from jarvis_router import route; route("...")
If the engine server (start-laya-engine.bat, port 8090) is running it is used; otherwise
the model loads in-process (~35 s first time).
"""
import json, sys, urllib.request

ENGINE = "http://127.0.0.1:8090"

JARVIS_QUESTIONS = {
    "business": {
        "type": "choice",
        "instructions": "Which of Semaj's businesses or projects is `request` about?",
        "criteria": {
            "out_and_legendary": "Out & Legendary: LGBTQIA+ greeting cards, celebration packets, keepsakes, Etsy or Shopify listings",
            "digital_planners": "digital planners, Quest Log planner, Kindle Scribe or Goodnotes planner files",
            "wright_connector": "AI receptionist, missed calls, GoHighLevel, Twilio, websites or SMS for HVAC, plumbing and other trades",
            "soulsmith": "custom 3D printed tabletop miniatures, HeyGears G1X, STL files, Kickstarter",
            "narrative_platform": "serialized web narrative platform, interactive story app",
            "fusion_writing": "FUSION book series: canon, characters, scenes, manuscript, worldbuilding",
            "publishing": "Amazon KDP, ASL or Deaf education books, Mystic Hands",
            "jarvis_system": "JARVIS itself: Obsidian vault, Claude Code, hooks, Ollama, Laya, automation setup",
            "other": "none of the other options fits",
        },
    },
    "is_code_or_files": {"type": "noul", "instructions": "Does `request` ask to build, fix or change code, scripts, hooks, files or software?"},
    "is_image": {"type": "noul", "instructions": "Does `request` need a picture, card artwork, logo or other visual created or edited?"},
    "is_routine": {"type": "noul", "instructions": "Is `request` a small routine text chore like summarizing, tagging or reformatting existing notes?"},
    "is_payment_or_credentials": {"type": "noul", "instructions": "Does `request` involve paying, invoices, bank or card details, passwords, logins or signing documents?"},
    "is_customer_or_public": {"type": "noul", "instructions": "Does `request` involve replying to a customer, a refund, publishing a listing, or anything the public will see?"},
    "difficulty": {
        "type": "score",
        "instructions": "How hard is `request`?",
        "criteria": ["trivial lookup", "easy", "several steps", "long multi-step or specialist work"],
    },
    "is_urgent": {
        "type": "noul",
        "instructions": "Does `request` mention a deadline, an angry customer, or something broken right now?",
    },
}

_local = None

_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # never send localhost via a system proxy
USED = {"engine": 0, "local": 0}

def _predict(state, questions):
    body = json.dumps({"state": state, "questions": questions}).encode()
    try:
        req = urllib.request.Request(ENGINE + "/predict", body, {"Content-Type": "application/json"})
        with _opener.open(req, timeout=60) as r:
            USED["engine"] += 1
            return json.loads(r.read())
    except Exception as e:
        sys.stderr.write(f"[jarvis_router] engine unavailable ({e!r}); loading model locally\n")
        global _local
        if _local is None:
            import laya
            _local = laya.Router(preload=False)
        USED["local"] += 1
        return _local.predict(state, questions)

def route(request: str) -> dict:
    res = _predict({"request": request}, JARVIS_QUESTIONS)
    a = res["answers"]
    p = lambda k: float(a[k]["noul"])
    money, public = p("is_payment_or_credentials"), p("is_customer_or_public")
    code, image, routine = p("is_code_or_files"), p("is_image"), p("is_routine")
    if money >= 0.5:
        handler = "semaj_only"
    elif image >= 0.5:
        handler = "chatgpt_images"
    elif code >= 0.5:
        handler = "claude_code"
    elif routine >= 0.5:
        handler = "ollama_local"
    else:
        handler = "claude_reasoning"
    return {
        "request": request,
        "business": a["business"]["choice"],
        "business_confidence": round(float(a["business"]["confidence"]), 2),
        "handler": handler,
        "needs_approval": money >= 0.5 or public >= 0.5,
        "difficulty": round(float(a["difficulty"]["score"]), 1),
        "urgent": p("is_urgent") >= 0.5,
        "signals": {k: round(v, 2) for k, v in
                    {"code": code, "image": image, "routine": routine, "money": money, "public": public}.items()},
    }

SAMPLES = [
    "Make a Level 50 Gay Wizard birthday card for Crystal",
    "Customer on Etsy says the planner links don't work in Goodnotes and wants a refund",
    "Fix the SessionStart hook so it loads the boot brief",
    "Write the next scene where Eli meets The First",
    "An HVAC company in Towson asked for a demo of the AI receptionist",
    "Summarize today's daily note into three bullets",
    "Pay the Twilio invoice",
    "Should SoulSmith be self-serve or a commission service?",
]

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        lines = [json.dumps(route(s)) for s in SAMPLES]
        out = "\n".join(lines)
        open("router_test_result.txt", "w", encoding="utf-8").write(out + f"\nDONE via {USED}\n")
        print(out)
    elif len(sys.argv) > 1:
        print(json.dumps(route(" ".join(sys.argv[1:])), indent=2))
    else:
        print(__doc__)
