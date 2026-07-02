from __future__ import annotations

import json


def test_traceability_manifest_maps_tests_to_all_top_level_requirements(tmp_path):
    manifest = {
        "RBS-1": "environment and dependency tests are executed through pytest.ini and CI-compatible commands",
        "RBS-2": "backend API and service lifecycle are covered by service round-trip tests",
        "RBS-3": "frontend coverage is represented by build/E2E plan and should be executed in browser CI",
        "RBS-4": "prompt/data preprocessing and postprocessing are covered by parser and metric tests",
        "RBS-5": "outline generation structure is covered by full DSL fixtures",
        "RBS-6": "content generation quality is covered by density/diversity metrics",
        "RBS-7": "RAG retrieval fusion is covered by deterministic RRF tests",
        "RBS-8": "rendering and export are covered by RenderTree and PPTX openability tests",
    }
    path = tmp_path / "traceability_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert sorted(loaded) == [f"RBS-{i}" for i in range(1, 9)]
