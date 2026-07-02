import httpx
import pytest

from chatbot.services import llm


@pytest.mark.asyncio
async def test_hf_failure_falls_back_and_sets_notice(monkeypatch):
    async def fake_hf_call(payload, timeout=20.0):
        raise httpx.TimeoutException("hf timed out")

    async def fake_ensure_ollama_available():
        return True

    async def fake_ollama_call(payload, timeout=20.0):
        return {"message": {"content": "local reply"}}

    monkeypatch.setattr(llm.hf, "call_ollama", fake_hf_call)
    monkeypatch.setattr(llm, "_ensure_ollama_available", fake_ensure_ollama_available)
    monkeypatch.setattr(llm.ollama_backend, "call_ollama", fake_ollama_call)

    llm._hf_available = True
    llm._fallback_since = None

    result = await llm.call_ollama({"messages": [{"role": "user", "content": "hi"}]}, timeout=20.0)

    assert result["_backend"] == "ollama"
    assert "free tier" in result["_notice"].lower()


@pytest.mark.asyncio
async def test_both_backends_fail_raise_unavailable_error(monkeypatch):
    async def fake_hf_call(payload, timeout=20.0):
        raise RuntimeError("hf failed")

    async def fake_ensure_ollama_available():
        return False

    monkeypatch.setattr(llm.hf, "call_ollama", fake_hf_call)
    monkeypatch.setattr(llm, "_ensure_ollama_available", fake_ensure_ollama_available)

    llm._hf_available = True
    llm._fallback_since = None

    with pytest.raises(RuntimeError, match="not available"):
        await llm.call_ollama({"messages": [{"role": "user", "content": "hi"}]}, timeout=20.0)
