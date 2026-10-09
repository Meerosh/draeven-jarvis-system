"""JARVIS front door (v2, 2026-10-05) - one place to talk to JARVIS.

Flow for every request (same pattern as the Jev/Jarvis demo, using the free local Laya model):
  1. Quick vault search (ms)               -> candidate notes
  2. Laya REFLEX (decisions, ~0.3-1 s)     -> lane, business, complete, stakes, vault_has_it, routine
  3. Act on the decision:
       vault_has_it  -> answer from the notes (no tools, cheap)
       routine       -> Ollama (local, free) if running, else Claude
       stakes high   -> DRAFT ONLY, show a Confirm button; nothing is done until Semaj confirms
       everything else -> Claude Code headless (`claude -p`) run inside the vault, so CLAUDE.md,
                          the boot brief and your whole vault are available (uses your Claude subscription)
  4. Every exchange is logged to the vault: 00 - Inbox\\JARVIS Log\\YYYY-MM-DD.md

Open http://127.0.0.1:4719 . Standard library only.
"""
import datetime, json, os, re, shutil, subprocess, sys, tempfile, threading, time, urllib.request, uuid, logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import socket as _socket
from provider_gateway import ProviderGateway, ProviderGatewayError
from shared_context import shared_context_status, with_shared_context
from repository_worker import RepositoryWorker, RepositoryWorkerError, format_result, parse_repository_request

# Configure structured logging
def _setup_logging(log_dir):
    """Setup Python logging with file and console handlers."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"frontdoor-{datetime.datetime.now().strftime('%Y-%m-%d')}.log")

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger = logging.getLogger('jarvis.frontdoor')
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()  # Remove any existing handlers

    # File handler
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler (stderr)
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

class XServer(ThreadingHTTPServer):
    """Refuses to share its port (Windows would otherwise let a 2nd copy bind too)."""
    allow_reuse_address = False
    def server_bind(self):
        if hasattr(_socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(_socket.SOL_SOCKET, _socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

PORT = int(os.getenv("JARVIS_FRONTDOOR_PORT", "4719"))
VAULT = os.getenv("JARVIS_VAULT", r"C:\Users\Arach\Documents\Jarvis")
HERE = os.path.dirname(os.path.abspath(__file__))
LAYA_ENGINE = os.getenv("JARVIS_LAYA_ENGINE", "http://127.0.0.1:8090")
OLLAMA = os.getenv("JARVIS_OLLAMA", "http://127.0.0.1:11434")
NOPROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))
GATEWAY = ProviderGateway(HERE)
SKIP_DIRS = {".obsidian", ".git", ".claude", ".codex", ".copilot", ".opencode", ".agents",
             "__pycache__", "07 - Archive", "node_modules", "tmp_pdf_read", "Claude outputs"}

# Setup logging
LOGGER = _setup_logging(os.path.join(HERE, "logs"))

# Thread-safe data structures with TTL support for PENDING
class PendingGate:
    """Thread-safe pending confirmations with automatic TTL cleanup."""
    def __init__(self, ttl_seconds=1800):
        self.data = {}
        self.timestamps = {}
        self.ttl_seconds = ttl_seconds
        self.lock = threading.RLock()

    def set(self, confirm_id, request):
        with self.lock:
            self.data[confirm_id] = request
            self.timestamps[confirm_id] = time.time()
            self._cleanup()

    def get(self, confirm_id):
        with self.lock:
            self._cleanup()
            return self.data.get(confirm_id)

    def pop(self, confirm_id, default=None):
        with self.lock:
            self._cleanup()
            self.timestamps.pop(confirm_id, None)
            return self.data.pop(confirm_id, default)

    def _cleanup(self):
        """Remove expired entries (called within lock)."""
        now = time.time()
        expired = [cid for cid, ts in self.timestamps.items() if now - ts > self.ttl_seconds]
        for cid in expired:
            self.data.pop(cid, None)
            self.timestamps.pop(cid, None)
            if expired:
                LOGGER.debug(f"Cleaned up expired pending entry: {cid}")

PENDING = PendingGate(ttl_seconds=int(os.getenv("JARVIS_PENDING_TTL", "1800")))
HISTORY_LOCK = threading.RLock()
HISTORY = []  # recent exchanges, restored in the page after a reload
REPOSITORIES = RepositoryWorker()
COUNCIL = {
    "lucien": ("claude", "sonnet", "You are Lucien Voss, strategy and research counsel. Test assumptions, compare options, and give a clear recommendation."),
    "garrick": ("codex", None, "You are Garrick Thorne, operations and delivery counsel. Find blockers, dependencies, and the shortest verified path to completion."),
    "vaelis": ("claude", "haiku", "You are Vaelis Nightweave, creative and storytelling counsel. Develop distinctive concepts that follow Semaj's approved source material."),
    "azrath": ("hermes", "ornith-final", "You are Azrath Veyr, systems and automation counsel. Diagnose connections and require evidence before declaring a system working."),
}

REFLEX = {
    "business": {"type": "choice", "instructions": "Which of Semaj's businesses or projects is `request` about?",
        "criteria": {
            "out_and_legendary": "Out & Legendary: LGBTQIA+ greeting cards, celebration packets, keepsakes, Etsy or Shopify listings",
            "digital_planners": "digital planners, Quest Log planner, Kindle Scribe or Goodnotes planner files",
            "wright_connector": "AI receptionist, missed calls, GoHighLevel, Twilio, websites or SMS for HVAC, plumbing and other trades",
            "soulsmith": "custom 3D printed tabletop miniatures, HeyGears G1X, STL files, Kickstarter",
            "narrative_platform": "serialized web narrative platform, interactive story app",
            "fusion": "FUSION book series: canon, characters, scenes, manuscript, worldbuilding",
            "publishing": "Amazon KDP, ASL or Deaf education books, Mystic Hands",
            "jarvis_system": "JARVIS itself: Obsidian vault, Claude Code, hooks, Ollama, Laya, automation setup",
            "other": "none of the other options fits"}},
    "stakes": {"type": "noul", "instructions": "Would acting on `request` send, post, publish, call, delete, pay or spend, or contact a customer?"},
    "is_code": {"type": "noul", "instructions": "Does `request` ask to build, fix or change code, scripts, hooks, files or software?"},
    "is_image": {"type": "noul", "instructions": "Does `request` need a picture, card artwork, logo or other visual created or edited?"},
    "routine": {"type": "noul", "instructions": "Is `request` a small routine text chore like summarizing, tagging or reformatting existing notes?"},
}
VAULT_Q = {"answers": {"type": "noul", "instructions": "Does `note` contain the answer to `request`?"}}

# ---------------- vault search ----------------
_index, _index_time = [], 0

def build_index():
    global _index, _index_time
    items = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if f.lower().endswith(".md"):
                p = os.path.join(root, f)
                try:
                    txt = open(p, encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                items.append((os.path.relpath(p, VAULT), f[:-3].lower(), txt, txt.lower()))
    _index, _index_time = items, time.time()

STOP = set("the a an and or to of for in on is are was be me my i you it this that with what how can please jarvis do does about from at".split())

def search(q, k=5):
    if time.time() - _index_time > 120:
        build_index()
    terms = [t for t in re.findall(r"[a-z0-9&']+", q.lower()) if t not in STOP and len(t) > 1]
    if not terms:
        return []
    scored = []
    for rel, name, txt, low in _index:
        s = sum(5 * name.count(t) + min(low.count(t), 20) for t in terms)
        if s:
            scored.append((s, rel, txt))
    scored.sort(reverse=True)
    out = []
    for s, rel, txt in scored[:k]:
        i = max(0, min((txt.lower().find(t) for t in terms if t in txt.lower()), default=0) - 200)
        low = txt.lower()
        cov = sum(1 for t in terms if t in low) / len(terms)
        out.append({"path": rel, "score": s, "coverage": round(cov, 2), "snippet": txt[i:i + 1200]})
    return out

# ---------------- Laya reflex ----------------

NEUTRAL = None

class CircuitBreaker:
    """Simple circuit breaker for provider fallback handling."""
    def __init__(self, failure_threshold=3, timeout_seconds=300):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.last_failure_time = None
        self.lock = threading.RLock()

    def record_success(self):
        with self.lock:
            self.failure_count = 0

    def record_failure(self):
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

    def is_open(self):
        """Check if circuit is open (too many failures)."""
        with self.lock:
            if self.failure_count >= self.failure_threshold:
                elapsed = time.time() - self.last_failure_time
                if elapsed < self.timeout_seconds:
                    return True
                else:
                    # Reset after timeout
                    self.failure_count = 0
            return False

# Circuit breakers for Jev and Laya
_jev_breaker = CircuitBreaker(failure_threshold=2)
_laya_breaker = CircuitBreaker(failure_threshold=3)

def _laya(state, questions):
    """Route via Jev (OpenRouter Llama 3.3 70B) PRIMARY; fall back to local Laya on failure.
    Never loads a second copy of the model here (that doubled RAM use).
    If both fail, return neutral answers so the request still goes to Claude safely."""

    # Import jev_openrouter on first call
    if not hasattr(_laya, '_jev_imported'):
        try:
            import sys
            sys.path.insert(0, os.path.dirname(HERE))
            import jev_openrouter
            _laya._jev = jev_openrouter
            _laya._jev_imported = True
        except ImportError as e:
            _laya._jev = None
            _laya._jev_imported = True
            LOGGER.debug(f"Jev import failed: {e}")

    # Try Jev (OpenRouter) first if circuit is closed
    if _laya._jev and not _jev_breaker.is_open():
        try:
            jev_result = _laya._jev.call_jev(state, questions)
            if jev_result:
                _jev_breaker.record_success()
                LOGGER.debug("Jev route succeeded")
                return jev_result
        except Exception as e:
            _jev_breaker.record_failure()
            LOGGER.warning(f"Jev failed: {e}")

    # Fallback to Laya on port 8090 if circuit is closed
    if not _laya_breaker.is_open():
        body = json.dumps({"state": state, "questions": questions}).encode()
        try:
            req = urllib.request.Request(LAYA_ENGINE + "/predict", body, {"Content-Type": "application/json"})
            with NOPROXY.open(req, timeout=60) as r:
                result = json.loads(r.read())["answers"]
                _laya_breaker.record_success()
                LOGGER.debug("Laya route succeeded")
                return result
        except Exception as e:
            _laya_breaker.record_failure()
            LOGGER.warning(f"Laya route failed: {e}")

    # Both providers failed or circuits are open; try to start Laya and return neutral answers
    LOGGER.error("Both Jev and Laya failed; returning neutral reflex answers")
    try:
        laya_engine_path = os.getenv("JARVIS_LAYA_ENGINE_PATH", r"C:\Users\Arach\my-agent\laya-engine\JARVIS Laya Engine.vbs")
        if os.path.exists(laya_engine_path):
            subprocess.Popen(["wscript", laya_engine_path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            LOGGER.info("Attempted to restart Laya engine")
    except Exception as e:
        LOGGER.debug(f"Could not restart Laya: {e}")

    # Return neutral answers when all routing fails
    out = {}
    for k, q in questions.items():
        if q["type"] == "choice":
            first = next(iter(q["criteria"]))
            out[k] = {"choice": {"lane": "do_work", "business": "none"}.get(k, first), "confidence": 0.0}
        else:
            out[k] = {"noul": 0.5 if k == "stakes" else 0.0, "confidence": 0.0}  # unknown stakes -> ask first
    return out

QWORDS = ("what", "whats", "what's", "how", "why", "when", "where", "who", "which", "did", "do", "does", "is", "are",
          "was", "were", "have", "has", "can you tell", "tell me", "remind me", "show me", "pull up", "list", "explain")
GREET = ("hi", "hello", "hey", "good morning", "good afternoon", "good evening", "thanks", "thank you")

def reflex(request, notes):
    """Hybrid reflex: Laya for judgment calls it is good at (stakes, business, code, image, routine);
    plain rules for things rules do better (is it a question? a greeting? does a note cover the words?)."""
    t = time.time()
    a = _laya({"request": request}, REFLEX)
    n = lambda k: round(float(a[k].get("noul", 0.0)), 2)
    low = request.lower().strip()
    question = low.endswith("?") or low.startswith(QWORDS)
    greeting = len(low.split()) <= 8 and low.startswith(GREET)
    d = {"business": a["business"]["choice"], "business_conf": round(float(a["business"]["confidence"]), 2),
         "stakes": n("stakes"), "is_code": n("is_code"), "is_image": n("is_image"), "routine": n("routine"),
         "question": question, "vault_has_it": 0.0, "vault_note": None}
    if notes:
        v = _laya({"request": request, "note": notes[0]["snippet"][:500]}, VAULT_Q)
        d["vault_has_it"] = round(max(float(v["answers"]["noul"]), notes[0]["coverage"] if question else 0.0), 2)
        d["vault_note"] = notes[0]["path"]
    if greeting: lane = "chat"
    elif d["stakes"] >= 0.5 and not question: lane = "act (needs confirm)"
    elif question: lane = "recall"
    elif d["is_image"] >= 0.5: lane = "image"
    elif d["is_code"] >= 0.5: lane = "code_or_system"
    else: lane = "do_work"
    d["lane"], d["lane_conf"] = lane, 1.0
    d["ms"] = int((time.time() - t) * 1000)
    return d

# ---------------- brains ----------------
CLAUDE_LOCK = threading.Lock()
HISTORY = []  # recent exchanges, restored in the page after a reload

# OmniRoute (local gateway, default http://127.0.0.1:20128/v1) fronts the Claude
# lane so requests share OmniRoute's routing and usage tracking. Disabled by
# default in provider_policy.json; the key comes from the environment only.
OMNIROUTE_MODELS = {"haiku": "cc/claude-haiku-4-5-20251001", "sonnet": "cc/claude-sonnet-4-6"}

def ask_omniroute(prompt, model=None):
    key = os.environ.get("OMNIROUTE_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OMNIROUTE_API_KEY is not set in the environment.")
    base = os.environ.get("OMNIROUTE_URL", "http://127.0.0.1:20128/v1").rstrip("/")
    body = json.dumps({
        "model": OMNIROUTE_MODELS.get(model or "haiku", OMNIROUTE_MODELS["haiku"]),
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2048,
    }).encode("utf-8")
    req = urllib.request.Request(base + "/chat/completions", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # Report the status only; never echo the request or headers.
        raise RuntimeError(f"OmniRoute returned HTTP {e.code}") from e
    return ((data.get("choices") or [{}])[0].get("message", {}).get("content") or "").strip() or "[no output]"

def ask_claude(prompt, model=None):
    exe = shutil.which("claude") or shutil.which("claude.cmd")
    if not exe:
        return "[Claude Code CLI not found on PATH. Install/sign in to Claude Code, then retry.]"
    cmd = [exe, "-p", prompt, "--output-format", "text"]
    # A prompt asking for draft-only behavior is not a permission boundary.
    # Claude's verified plan mode prevents this Front Door from applying edits.
    cmd += ["--permission-mode", "plan"]
    if model:
        cmd += ["--model", model]
    try:
      with CLAUDE_LOCK:  # never run several Claude jobs at once
        r = subprocess.run(cmd, cwd=VAULT, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=600)
        return (r.stdout or r.stderr or "[no output]").strip()
    except subprocess.TimeoutExpired:
        return "[Claude took longer than 10 minutes; try a smaller request.]"

def ask_claude_first(prompt, model=None):
    """OmniRoute first; direct Claude only when OmniRoute cannot answer."""
    try:
        return ask_omniroute(prompt, model)
    except Exception as e:
        print(f"[omniroute] unavailable, answering with direct Claude: {e}", flush=True)
        return ask_claude(prompt, model)

def ask_codex(prompt, model=None):
    """Run Codex ephemerally with a read-only sandbox and capture only its final answer."""
    exe = shutil.which("codex") or shutil.which("codex.exe")
    if not exe:
        return "[Codex CLI not found on PATH.]"
    output_path = None
    try:
        with tempfile.NamedTemporaryFile(prefix="jarvis-codex-", suffix=".txt", delete=False) as handle:
            output_path = handle.name
        cmd = [exe, "exec", "--ephemeral", "--skip-git-repo-check", "--ignore-rules",
               "--sandbox", "read-only", "--cd", VAULT, "--output-last-message", output_path]
        if model:
            cmd += ["--model", model]
        cmd.append(prompt)
        r = subprocess.run(cmd, cwd=VAULT, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=600)
        with open(output_path, encoding="utf-8", errors="replace") as handle:
            answer = handle.read().strip()
        return answer or (r.stdout or r.stderr or "[no output]").strip()
    except subprocess.TimeoutExpired:
        return "[Codex took longer than 10 minutes; try a smaller request.]"
    finally:
        if output_path:
            try:
                os.unlink(output_path)
            except OSError:
                pass

def ask_hermes(prompt, model=None):
    """Run the isolated local Hermes profile with every toolset disabled."""
    exe = shutil.which("hermes") or shutil.which("hermes.exe")
    if not exe:
        return "[Hermes CLI not found on PATH.]"
    cmd = [exe, "-p", "draeven", "--ignore-rules", "--skills", "", "--toolsets", "",
           "--provider", "ollama", "--model", model or "ornith-final", "--oneshot", prompt]
    try:
        r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=240)
        return (r.stdout or r.stderr or "[no output]").strip()
    except subprocess.TimeoutExpired:
        return "[Local Hermes took longer than four minutes; try a smaller request.]"

def provider_answer(request, d, prompt, *, status_request=False, provider=None, model=None):
    """Select exactly one provider, enforce limits, and attach usage metadata."""
    if provider is None:
        provider, model = GATEWAY.choose(d["lane"], request, status_request=status_request)
    runners = {"claude": ask_claude_first, "codex": ask_codex, "hermes": ask_hermes, "omniroute": ask_claude_first}
    if provider not in runners:
        raise ProviderGatewayError(f"No text runner is registered for {provider}.")
    # Every provider receives the same small, secret-free operating baseline.
    # This replaces provider-specific hidden context as the source of truth.
    prompt = with_shared_context(prompt)
    result = GATEWAY.run(provider, prompt, runners[provider], model=model)
    d["provider"] = result.provider
    d["model"] = result.model
    d["provider_ms"] = result.elapsed_ms
    d["estimated_input_tokens"] = result.estimated_input_tokens
    d["estimated_output_tokens"] = result.estimated_output_tokens
    d["cloud_calls"] = result.cloud_calls
    route = result.provider + (f"/{result.model}" if result.model else "")
    return result.answer, route

def ask_ollama(prompt):
    try:
        with NOPROXY.open(OLLAMA + "/api/tags", timeout=3) as r:
            models = [m["name"] for m in json.loads(r.read()).get("models", [])]
        if not models:
            return None
        body = json.dumps({"model": models[0], "prompt": prompt, "stream": False}).encode()
        req = urllib.request.Request(OLLAMA + "/api/generate", body, {"Content-Type": "application/json"})
        with NOPROXY.open(req, timeout=180) as r:
            return f"(Ollama {models[0]}) " + json.loads(r.read()).get("response", "").strip()
    except Exception:
        return None

def notes_block(notes):
    return "\n\n".join(f"### {n['path']}\n{n['snippet']}" for n in notes)

PERSONA = ("You are JARVIS, Semaj's operating partner, speaking through his JARVIS front door. "
           "Be direct and concise (this may be read aloud). Push back when something is a bad idea. ")

STATUS_WORDS = ("priorit", "status", "running", "what's next", "whats next", "what is next", "overview", "all my business", "all of my business")

def handle(request, d=None, agent=None, context=None):
    # CRITICAL OPTIMIZATION: Eliminate vault searching entirely (~15-27 sec waste).
    # Laya routes instantly (~1-2 sec). Claude Code gets the boot brief via the boot hook.
    # Vault search was premature; Laya + boot brief + Claude makes it redundant.
    repo_request = parse_repository_request(request)
    if repo_request:
        action = repo_request["action"]
        decision = {"lane": "repository", "stakes": 1.0 if action in {"clone", "implement", "publish"} else 0.0}
        try:
            if action == "list":
                LOGGER.info("Repository list requested")
                return decision, format_result(REPOSITORIES.list()), "repository worker (read only)", None
            if action == "inspect":
                LOGGER.info(f"Repository inspect requested: {repo_request['name']}")
                return decision, format_result(REPOSITORIES.inspect(repo_request["name"])), "repository worker (read only)", None
        except RepositoryWorkerError as exc:
            LOGGER.error(f"Repository action failed: {exc}")
            return decision, str(exc), "repository worker (error)", None
        pid = uuid.uuid4().hex[:8]
        PENDING.set(pid, {"kind": "repository", **repo_request})
        if action == "clone":
            description = f"clone {repo_request['url']} into Draeven's managed repository workspace"
        elif action == "implement":
            description = f"let Codex edit {repo_request['name']} locally and leave a reviewable uncommitted diff"
        else:
            description = f"commit and push the reviewed changes in {repo_request['name']}"
        LOGGER.info(f"Repository {action} pending confirmation: {pid}")
        return decision, f"Ready to {description}. Confirm to continue.", "repository worker (waiting for confirmation)", pid

    timing = {"start": time.time()}
    d = d or {}
    if not d:
        timing["laya_start"] = time.time()
        notes = []  # <-- SKIP vault search entirely; boot brief handles context
        d = reflex(request, notes)
        timing["laya_end"] = time.time()
    else:
        notes = []  # No vault search for pre-computed paths either
    lane = d["lane"]
    model_request = request
    if isinstance(context, str) and context.strip():
        model_request = ("Recent Draeven conversation:\n" + context.strip()[:8000]
                         + "\n\nCurrent request:\n" + request)
    timing["routing_done"] = time.time()
    if lane == "chat":
        hour = datetime.datetime.now().hour
        part = "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
        return d, f"Good {part}, Semaj. I'm here. What do you need?", "instant (no AI needed)", None
    if any(w in request.lower() for w in STATUS_WORDS):
        timing["claude_start"] = time.time()
        answer, route = provider_answer(request, d, PERSONA + "Answer from JARVIS-BOOT-BRIEF.md, Active Priorities.md and MASTER_CONTEXT.md "
                             "in the vault root (read those, nothing else unless essential). Give: each business and its "
                             "current state, what is actually running, and the top priorities in order. Flag anything the "
                             f"vault is missing.\n\nRequest: {model_request}", status_request=True)
        timing["claude_end"] = time.time()
        d["timing_ms"] = {k: int((v - timing["start"]) * 1000) for k, v in timing.items() if k != "start"}
        return d, answer, route + " (status files)", None
    if agent in COUNCIL:
        provider, model, role = COUNCIL[agent]
        answer, route = provider_answer(request, d,
            PERSONA + role + " Give advice or a draft only. Do not perform external actions, publish, purchase, send, or delete.\n\nRequest: " + model_request,
            provider=provider, model=model)
        d["council_agent"] = agent
        return d, answer, route + f" (council:{agent}; advice only)", None
    if lane == "act (needs confirm)":
        pid = uuid.uuid4().hex[:8]
        PENDING.set(pid, request)
        timing["claude_start"] = time.time()
        draft, route = provider_answer(request, d, PERSONA + "This request has real-world stakes. DO NOT take any action, send anything, "
                           "or change any file. Produce only the draft or plan and list exactly what would happen "
                           f"if Semaj confirms.\n\nRequest: {model_request}", provider="claude", model="haiku")
        timing["claude_end"] = time.time()
        d["timing_ms"] = {k: int((v - timing["start"]) * 1000) for k, v in timing.items() if k != "start"}
        LOGGER.info(f"High-stakes action pending confirmation: {pid}")
        return d, draft, route + " (draft only - waiting for your Confirm)", pid
    if notes and (lane == "recall" or d["vault_has_it"] >= 0.5):
        best = [n for n in notes if n["path"] == d["vault_note"]] + [n for n in notes if n["path"] != d["vault_note"]]
        if d["vault_has_it"] >= 0.5 and d["routine"] >= 0.5:
            ans = ask_ollama(f"{PERSONA}Answer ONLY from these notes; say if they don't cover it.\n\n"
                             f"{notes_block(best[:3])}\n\nQuestion: {request}")
            if ans:
                return d, ans, "ollama + vault notes (local, free)", None
        return d, ask_claude_first(PERSONA + "Answer from the vault. Start with these notes, open others only if needed:\n"
                             + "\n".join(n["path"] for n in best) + f"\n\nQuestion: {request}", model="sonnet"), "claude + vault notes", None
    if lane == "chat" or (d["routine"] >= 0.6 and d["is_code"] < 0.5 and d["stakes"] < 0.5):
        ans = ask_ollama(PERSONA + request)
        if ans:
            return d, ans, "ollama (local, free)", None
    if lane == "image":
        answer, route = provider_answer(request, d, PERSONA + "Create a concise image-production prompt package. Use Semaj's existing O&L card pipeline "
                             "(C:\\Users\\Arach\\my-agent\\jarvis-control-plane, card_orchestrator.py) if it applies; "
                              f"otherwise write the image prompt and next step. Do not edit files, generate images, or execute actions. "
                              f"Midjourney submission is manual.\n\nRequest: {model_request}", provider="claude", model="haiku")
        return d, answer, route + " (manual image prompt package)", None
    timing["claude_start"] = time.time()
    answer, route = provider_answer(request, d, PERSONA + "Draft the requested work and explain the next step. Do not edit files, run commands, or perform external actions.\n\n" + model_request)
    timing["claude_end"] = time.time()
    d["timing_ms"] = {k: int((v - timing["start"]) * 1000) for k, v in timing.items() if k != "start"}
    return d, answer, route + " (draft only)", None

def log(request, d, route, answer):
    """Log request to vault markdown and structured logging."""
    folder = os.path.join(VAULT, "00 - Inbox", "JARVIS Log")
    os.makedirs(folder, exist_ok=True)
    now = datetime.datetime.now()
    log_file = os.path.join(folder, now.strftime("%Y-%m-%d") + ".md")

    # Write to vault markdown
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n## {now:%H:%M} - {request[:80]}\n- reflex: {json.dumps(d)}\n- route: {route}\n\n{answer[:3000]}\n")
    except Exception as e:
        LOGGER.warning(f"Failed to write vault log: {e}")

    # Log to structured logging
    LOGGER.info(f"Request: {request[:100]} | Route: {route}")
    if d.get("timing_ms"):
        LOGGER.debug(f"Timings: {d['timing_ms']}")

def _restart():
    time.sleep(0.5)
    subprocess.Popen([sys.executable, "-u", os.path.abspath(__file__), "--wait"], cwd=HERE,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    os._exit(0)

# ---------------- HTTP ----------------
class H(BaseHTTPRequestHandler):
    def _json(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            b = open(os.path.join(HERE, "index.html"), "rb").read()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
        elif self.path == "/history":
            with HISTORY_LOCK:
                self._json(200, list(HISTORY))
        elif self.path == "/health":
            health = {
                "ok": True,
                "notes_indexed": len(_index),
                "providers": GATEWAY.status(),
                "usage": GATEWAY.usage_status(),
                "shared_context": shared_context_status(),
                "pending_count": len(PENDING.data),
                "history_count": len(HISTORY)
            }
            self._json(200, health)
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(n) or b"{}")
        try:
            if self.path == "/ask":
                text = req["text"].strip()
                req_start = time.time()
                agent = req.get("agent")
                if agent is not None and agent not in COUNCIL:
                    return self._json(400, {"error": "unknown council agent"})
                d, ans, route, pid = handle(text, req.get("reflex"), agent, req.get("context"))
                req_total = int((time.time() - req_start) * 1000)
                log(text, d, route, ans)

                # Thread-safe history update
                with HISTORY_LOCK:
                    HISTORY.append({"q": text, "a": ans, "route": route, "confirm_id": pid})
                    del HISTORY[:-20]

                # Log timing with structured logging
                timing_str = ""
                if "timing_ms" in d:
                    timing_str = " > ".join(f"{k}={v}ms" for k, v in sorted(d["timing_ms"].items()))
                    LOGGER.info(f"Request timing: {text[:60][:60]} | Total={req_total}ms | {timing_str}")
                else:
                    LOGGER.info(f"Request completed: {text[:60]} | Total={req_total}ms")

                self._json(200, {"reflex": d, "answer": ans, "route": route, "confirm_id": pid})
            elif self.path == "/reflex":
                text = req["text"].strip()
                self._json(200, reflex(text, search(text)))
            elif self.path == "/restart":
                LOGGER.info("Restart requested")
                self._json(200, {"restarting": True})
                threading.Thread(target=_restart, daemon=True).start()
            elif self.path == "/confirm":
                confirm_id = req["id"]
                text = PENDING.pop(confirm_id, None)
                if not text:
                    LOGGER.warning(f"Confirm requested for missing pending ID: {confirm_id}")
                    return self._json(404, {"error": "nothing pending with that id"})
                LOGGER.info(f"Confirmation received for: {str(text)[:100]}")
                if isinstance(text, dict) and text.get("kind") == "repository":
                    try:
                        if text["action"] == "clone":
                            result = REPOSITORIES.clone(text["url"])
                        elif text["action"] == "implement":
                            result = REPOSITORIES.implement(text["name"], text["task"])
                        elif text["action"] == "publish":
                            result = REPOSITORIES.publish(text["name"], text["message"])
                        else:
                            raise RepositoryWorkerError("Unknown repository action.")
                    except RepositoryWorkerError as exc:
                        LOGGER.error(f"Repository action failed: {exc}")
                        return self._json(409, {"error": str(exc)})
                    return self._json(200, {"answer": format_result(result), "route": "repository worker",
                                            "receipt": {"id": "repository-" + uuid.uuid4().hex[:12],
                                                        "status": "executed", "executed": True}})
                decision = {"lane": "act (needs confirm)"}
                ans, route = provider_answer(text, decision, PERSONA + "Semaj approved this plan for implementation, but this Front Door is in draft-only mode. Do not edit files, run commands, or perform external actions. State that the approval is recorded, then list the exact manual implementation step and any required tools.\n\nRequest: " + text, provider="claude", model="haiku")
                route += " (approval recorded; draft only)"
                log("[APPROVED PLAN - NOT EXECUTED] " + text, decision, route, ans)
                receipt_id = "approval-" + uuid.uuid4().hex[:12]
                self._json(200, {"answer": ans, "route": route,
                    "receipt": {"id": receipt_id, "status": "approval_recorded", "executed": False}})
            else:
                self._json(404, {"error": "not found"})
        except Exception as e:
            LOGGER.exception(f"Unhandled error in POST handler: {e}")
            self._json(500, {"error": repr(e)})

    def log_message(self, fmt, *a):
        sys.stderr.write("[frontdoor] " + fmt % a + "\n")

if __name__ == "__main__":
    if "--wait" in sys.argv:
        time.sleep(2)  # let the old copy release the port
    try:
        srv = XServer(("127.0.0.1", PORT), H)
    except OSError:
        LOGGER.critical("Failed to bind to port (already running?)")
        sys.exit(1)

    LOGGER.info(f"JARVIS Front Door started on port {PORT}")
    LOGGER.info(f"Vault: {VAULT}")
    LOGGER.info(f"Laya Engine: {LAYA_ENGINE}")

    build_index()
    LOGGER.info(f"Vault index built: {len(_index)} markdown files")

    try:  # restore today's conversation so a restart/reload doesn't lose answers
        lp = os.path.join(VAULT, "00 - Inbox", "JARVIS Log", datetime.datetime.now().strftime("%Y-%m-%d") + ".md")
        with HISTORY_LOCK:
            for blk in open(lp, encoding="utf-8").read().split("\n## ")[1:]:
                head, _, rest = blk.partition("\n")
                q = head.split(" - ", 1)[-1]
                route = re.search(r"- route: (.*)", rest)
                ans = rest.split("\n\n", 1)[-1].strip()
                HISTORY.append({"q": q, "a": ans, "route": route.group(1) if route else "", "confirm_id": None})
            # drop half-sentences left by the old voice bug (an entry that a later entry merely extends)
            keep = [h for i, h in enumerate(HISTORY)
                    if not any(o["q"].startswith(h["q"]) and o["q"] != h["q"] for o in HISTORY[i + 1:])]
            seen, HISTORY[:] = set(), []
            for h in keep:
                if h["q"] not in seen:
                    seen.add(h["q"]); HISTORY.append(h)
            del HISTORY[:-20]
        LOGGER.info(f"Restored {len(HISTORY)} conversation turns from today")
    except OSError as e:
        LOGGER.debug(f"No previous history to restore: {e}")

    open(os.path.join(HERE, "status.txt"), "w").write(f"{datetime.datetime.now():%H:%M:%S} READY http://127.0.0.1:{PORT} notes={len(_index)}\n")
    print(f"JARVIS front door on http://127.0.0.1:{PORT} ({len(_index)} notes indexed)")
    LOGGER.info("Server ready, waiting for requests")
    srv.serve_forever()
