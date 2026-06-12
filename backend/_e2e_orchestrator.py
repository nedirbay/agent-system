"""End-to-end: orchestrator plan + workflow engine run (real LLM via Ollama)."""
import asyncio

import httpx

from app.main import app

PREFIX = "/api/v1"


async def main():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=180) as client:
        # 1. Orchestrator plan only (Tasks 11–12)
        r = await client.post(
            f"{PREFIX}/agents/orchestrator/plan",
            json={"request": "Yüklenen şertnamany okap, töwekgelçilikli şertleri analiz et we gysga hasabat taýýarla"},
        )
        r.raise_for_status()
        plan = r.json()
        print("1. PLAN (fallback=%s): %s" % (plan["fallback"], plan["summary"]))
        for s in plan["steps"]:
            print("   %d. %-14s [%s/%s] approval=%s :: %s" % (
                s["step_order"], s["agent_type"], s["tier"], s["model"],
                s["requires_approval"], s["objective"][:60]))
        assert plan["steps"]

        # 2. Run a full workflow (Task 13): plan -> persist -> execute steps
        r = await client.post(
            f"{PREFIX}/workflows/run",
            json={"request": "Aşgabadyň howasy barada gysgaça maglumat ber we esasy bellikleri sanaw görnüşinde jemle"},
        )
        r.raise_for_status()
        inst = r.json()
        print("\n2. RUN instance %s status=%s steps=%d" % (inst["id"][:8], inst["status"], len(inst["steps"])))
        for s in inst["steps"]:
            preview = (s["output"] or {}).get("result", "") if s["output"] else (s["error"] or "")
            print("   %d. %-14s %-10s att=%d :: %s" % (
                s["step_order"], s["agent_type"], s["status"], s["attempts"],
                preview[:70].replace("\n", " ")))
        assert inst["status"] == "Completed", inst["status"]
        assert all(s["status"] == "Succeeded" for s in inst["steps"])
        # context carried each step output forward
        assert len(inst["context"]) == len(inst["steps"])

        # 3. Fetch the persisted instance back
        r = await client.get(f"{PREFIX}/workflows/instances/{inst['id']}")
        r.raise_for_status()
        got = r.json()
        print("\n3. GET instance status=%s, persisted steps=%d" % (got["status"], len(got["steps"])))
        assert got["id"] == inst["id"]
        assert got["status"] == "Completed"

    print("\nORCHESTRATOR E2E OK")


asyncio.run(main())
