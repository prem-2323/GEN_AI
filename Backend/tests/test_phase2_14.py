"""Phase 2-14 end-to-end test: local workspace -> project -> upload -> JSON
source -> extraction -> AI -> UCKR -> 7 deliverables -> validation ->
export -> search -> jobs -> isolation. Run: python test_phase2_14.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

SAMPLE = """Threat Intelligence Report Q3 2026.
Acme Corp detected 47 phishing attempts targeting the finance team in September 2026.
The security team must patch all edge servers within 14 days.
On September 12, 2026, a malware sample exploited CVE-2026-1234 affecting 12 servers.
Analysts should review firewall logs and ensure multi-factor authentication is enforced.
Estimated potential loss is 2.5 million dollars if the breach succeeds.
The board meeting on October 5, 2026 will review the incident response plan.
"""

c = TestClient(app)
A = {"X-User-Uid": "phase2-user-A", "X-User-Email": "a@example.com"}
B = {"X-User-Uid": "phase2-user-B"}
fails = []


def check(name, cond, extra=""):
    print(f"  [{'OK' if cond else 'FAIL'}] {name} {extra}")
    if not cond:
        fails.append(name)


def run_e2e_test():
    print("1. health:", c.get("/health").json().get("ok"))
    print("2. projects:", c.get("/api/projects", headers=A).status_code)

    proj = c.post("/api/projects", json={"name": "Threat Intel Report", "description": "e2e"}, headers=A).json()
    pid = proj["id"]
    check("create project", pid and proj.get("userId") == "phase2-user-A", pid)

    up = c.post(f"/api/projects/{pid}/upload", files={"file": ("threat_report.txt", SAMPLE, "text/plain")}, headers=A)
    check("upload status", up.status_code == 200, str(up.status_code))
    src = up.json()["source"]
    sid = src["sourceId"]
    check("source completed", src["processing"]["stage"] == "completed", src["processing"]["stage"])
    check("extraction stats", src["extraction"]["textLength"] > 100 and src["extraction"]["pageCount"] >= 1,
          str(src["extraction"]))

    ls = c.get(f"/api/projects/{pid}/sources", headers=A).json()
    check("list sources", len(ls["sources"]) == 1)

    an = c.post(f"/api/projects/{pid}/analyze", json={"sourceId": sid}, headers=A)
    check("analyze", an.status_code == 200, f"{an.status_code} provider={an.json().get('analysisProvider')}")
    uckr = an.json()["uckr"]
    check("uckr facts", len(uckr["facts"]) >= 3, f"facts={len(uckr['facts'])} version={uckr['version']}")

    tr = c.post(f"/api/projects/{pid}/transform",
                json={"types": ["linkedin", "twitter", "advisory", "executive_summary", "infographic",
                                 "presentation", "video"]}, headers=A)
    check("7 deliverables", tr.json().get("count") == 7, str(tr.json().get("count")))

    va = c.post(f"/api/projects/{pid}/validate", headers=A)
    check("validation", va.status_code == 200 and va.json()["validation"]["status"] in ("pass", "warning", "fail"),
          va.json().get("validation", {}).get("status", va.status_code))

    dels = c.get(f"/api/projects/{pid}/deliverables", headers=A).json()["deliverables"]
    ex = c.post(f"/api/deliverables/{dels[0]['deliverableId']}/export", params={"format": "md"}, headers=A)
    check("export md", ex.json().get("ok") is True, str(ex.json().get("storagePath")))
    pres = [d for d in dels if d["type"] == "presentation"][0]
    exp = c.post(f"/api/deliverables/{pres['deliverableId']}/export", params={"format": "pptx"}, headers=A)
    check("export pptx", exp.json().get("ok") is True)

    se = c.get("/api/search", params={"q": "phishing"}, headers=A).json()
    check("search finds source", len(se["sources"]) >= 1)

    ov = c.get(f"/api/projects/{pid}/overview", headers=A).json()
    check("overview bundle", ov["uckr"] is not None and len(ov["deliverables"]) == 7 and len(ov["validations"]) >= 1)

    cross = c.get(f"/api/projects/{pid}", headers=B)
    check("cross-tenant project 403", cross.status_code == 403, str(cross.status_code))
    cross2 = c.get(f"/api/sources/{sid}", headers=B)
    check("cross-tenant source 403", cross2.status_code == 403, str(cross2.status_code))

    jb = c.post(f"/api/projects/{pid}/jobs", json={"sourceId": sid}, headers=B if False else A).json()
    jid = jb["job"]["jobId"]
    import time
    for _ in range(30):
        time.sleep(1)
        st = c.get(f"/api/jobs/{jid}", headers=A).json()["job"]
        if st["stage"] in ("completed", "failed"):
            break
    check("background job completed", st["stage"] == "completed", f"{st['stage']} {st.get('error', '')}")
    check("job uckr v2", (st.get("result") or {}).get("uckrVersion") == 2, str((st.get("result") or {})))

    bad = c.post(f"/api/projects/{pid}/upload", files={"file": ("evil.exe", b"xx", "application/octet-stream")}, headers=A)
    check("exe rejected 422", bad.status_code == 422, str(bad.status_code))

    print("cleanup:", c.delete(f"/api/sources/{sid}", headers=A).status_code,
          c.delete(f"/api/projects/{pid}", headers=A).json())

    if fails:
        print(f"\nFAILED: {fails}")
        sys.exit(1)
    print("\nAll Phase 2-14 pipeline tests passed!")


if __name__ == "__main__":
    run_e2e_test()
