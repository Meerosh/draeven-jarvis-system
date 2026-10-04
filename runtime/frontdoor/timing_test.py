"""Test one request and measure timing of each component."""
import urllib.request
import json
import time

request_text = "Make a birthday card for Crystal"
print(f"Testing request: '{request_text}'\n")

# Measure frontdoor /reflex call
start = time.time()
try:
    payload = json.dumps({"request": request_text}).encode('utf-8')
    req = urllib.request.Request(
        'http://127.0.0.1:4719/reflex',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        result = json.loads(r.read())
        total_time = time.time() - start

        print(f"✓ Response received in {total_time:.1f} seconds")
        print(f"\nResponse data:")
        print(f"  Lane: {result.get('lane', 'unknown')}")
        print(f"  Business: {result.get('business', 'unknown')}")
        print(f"  Handler: {result.get('handler', 'unknown')}")
        print(f"  Needs approval: {result.get('needs_approval', False)}")
        print(f"  Message preview: {str(result.get('message', ''))[:150]}...")

except Exception as e:
    total_time = time.time() - start
    print(f"✗ Failed after {total_time:.1f}s: {str(e)[:100]}")
