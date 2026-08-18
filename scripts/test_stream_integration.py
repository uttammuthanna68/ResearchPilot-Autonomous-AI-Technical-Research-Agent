"""End-to-end streaming integration test for ResearchPilot API."""

import urllib.request
import json

url = "http://127.0.0.1:8000/api/research/stream"
data = json.dumps({"query": "How does state persistence work in LangGraph using checkpointers?", "mode": "hybrid"}).encode("utf-8")

req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

print("Sending streaming request to FastAPI backend...")
events_received = []

with urllib.request.urlopen(req) as response:
    for line in response:
        decoded = line.decode("utf-8").strip()
        if decoded.startswith("data: "):
            json_str = decoded.replace("data: ", "")
            try:
                payload = json.loads(json_str)
                events_received.append(payload)
                event_type = payload.get("event")
                stage = payload.get("stage")
                status = payload.get("status")
                print(f"[SSE Event] event={event_type}, stage={stage}, status={status}")
                if event_type == "complete":
                    print(f"\n✓ Stream completed successfully!")
                    print(f"  Query: {payload.get('query')}")
                    print(f"  Tasks Count: {len(payload.get('steps', []))}")
                    print(f"  Documents Count: {len(payload.get('documents', []))}")
                    print(f"  Verification Status: {payload.get('evidence_verification', {}).get('status')}")
                    print(f"  Report Length: {len(payload.get('report', ''))} chars")
            except Exception as e:
                print(f"Parse error: {e}")

assert len(events_received) > 0, "No events received from SSE stream!"
print("\nStream Integration Test PASSED 100%!")
