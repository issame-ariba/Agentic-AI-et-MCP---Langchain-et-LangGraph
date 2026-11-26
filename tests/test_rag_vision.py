from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from D_Projet_Final_SAV import rag_mcp_server
from common.manual_search import PROJECT_ROOT


def test_figure_analysis_uses_configured_groq_vision_model(monkeypatch):
    image_path = PROJECT_ROOT / "data" / "demo_assets" / "img_px200_01_demo.png"
    captured = {}

    class FakeChatGroq:
        def __init__(self, *, model, temperature, api_key):
            captured["model"] = model
            captured["temperature"] = temperature
            captured["api_key"] = api_key

        def invoke(self, messages):
            captured["messages"] = messages
            return SimpleNamespace(content="Synthetic warning icon.")

    monkeypatch.setenv("GROQ_API_KEY", "test-key-not-sent")
    monkeypatch.setenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")
    monkeypatch.setattr(rag_mcp_server, "ChatGroq", FakeChatGroq)

    result = rag_mcp_server._analyze_figure(image_path)

    human_content = captured["messages"][1].content
    image_block = next(block for block in human_content if block["type"] == "image_url")
    assert result == "Synthetic warning icon."
    assert captured["model"] == "qwen/qwen3.8-27b"
    assert captured["temperature"] == 0
    assert captured["api_key"] == "test-key-not-sent"
    assert image_block["image_url"]["url"].startswith("data:image/png;base64,")


def test_figure_analysis_skips_vision_without_groq_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    def fail_if_called(**_kwargs):
        raise AssertionError("Vision model should not be constructed without a key.")

    monkeypatch.setattr(rag_mcp_server, "ChatGroq", fail_if_called)

    assert rag_mcp_server._analyze_figure(Path("image.png")) is None
