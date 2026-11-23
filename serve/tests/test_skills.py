"""Smoke test for the OpenCode-style skill interface."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from skills import SkillLibrary

def test_discovery_and_load():
    lib = SkillLibrary()
    lib._ensure()
    assert lib.count > 0, "no skills discovered"
    demo = lib.get("bhajanlal-local-demo")
    assert demo is not None, "project-local skill not discovered"
    out = lib.tool_result("load", "bhajanlal-local-demo")
    assert "SKILL: Bhajanlal Local Demo" in out
    assert "Workflow" in out
    # metadata-only search
    hits = lib.search("project-local", limit=5)
    assert any(h["id"] == "bhajanlal-local-demo" for h in hits)
    print("OK: %d skills; project-local discovery + on-demand load work" % lib.count)

if __name__ == "__main__":
    test_discovery_and_load()
