"""Proves the REAL Laya model (convaiinnovations/laya) is installed and answering.
Run:  python laya_selftest.py      First run downloads the model (~1-2 GB)."""
import json, sys, time

def to_jsonable(o):
    try:
        return float(o)
    except Exception:
        return str(o)

try:
    import laya
except ImportError:
    print("FAIL: laya is not installed. Run install-laya.bat first.")
    sys.exit(1)

print("laya version:", getattr(laya, "__version__", "unknown"))
state = ("Etsy message from a buyer: I bought the Out & Legendary Quest Log planner "
         "but the hyperlinks don't work in Goodnotes on my iPad. Can you help?")

questions = None
for name in ("triage_questions", "router_questions"):
    fn = getattr(laya, name, None)
    if fn:
        try:
            questions = fn()
            print(f"using built-in question set: laya.{name}()")
            break
        except Exception as e:
            print(f"laya.{name}() failed: {e}")
if questions is None:
    print("FAIL: no built-in question set available; check `pip show laya` version.")
    sys.exit(1)

t = time.time()
router = laya.Router(preload=False)
result = router.predict(state, questions)
print(f"answered in {time.time() - t:.1f}s (first run includes model load)")
print(json.dumps(result, indent=2, default=to_jsonable)[:4000])
print("\nPASS: real Laya model responded.")
