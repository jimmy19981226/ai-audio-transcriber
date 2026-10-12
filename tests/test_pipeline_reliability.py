import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

import agent
from config import load_config
from tools import context, transcription
from tools.context import TranscriptContext
from tools.toolbox import ToolBox, generate_function_schema


def test_config_accepts_default_and_string_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("agents.yaml").write_text("main: cleaner\nagents: []\n", encoding="utf-8")
    assert load_config()["main"] == "cleaner"
    assert load_config("agents.yaml")["agents"] == []


def test_missing_audio_raises_before_loading_a_model(tmp_path, monkeypatch):
    loader = Mock()
    monkeypatch.setattr(transcription, "_get_model", loader)
    with pytest.raises(transcription.TranscriptionError, match="not found"):
        transcription.load_audio_file(str(tmp_path / "missing.wav"))
    loader.assert_not_called()


def test_transcription_combines_segments_and_rejects_silence(tmp_path, monkeypatch):
    audio = tmp_path / "fixture.wav"
    audio.write_bytes(b"synthetic fixture; decoder is stubbed")
    model = Mock()
    model.transcribe.return_value = (iter([SimpleNamespace(text=" Hello "), SimpleNamespace(text="world.")]), None)
    monkeypatch.setattr(transcription, "_get_model", lambda: model)
    assert transcription.load_audio_file(str(audio)) == "Hello world."
    model.transcribe.return_value = (iter([]), None)
    with pytest.raises(transcription.TranscriptionError, match="No speech"):
        transcription.load_audio_file(str(audio))


def test_decoder_failure_never_becomes_transcript_text(tmp_path, monkeypatch):
    audio = tmp_path / "bad.wav"
    audio.touch()
    model = Mock()
    model.transcribe.side_effect = ValueError("invalid audio")
    monkeypatch.setattr(transcription, "_get_model", lambda: model)
    with pytest.raises(transcription.TranscriptionError, match="invalid audio"):
        transcription.load_audio_file(str(audio))


def test_transcription_error_propagates_through_tool_dispatch():
    box = ToolBox()

    async def read_audio() -> str:
        raise transcription.TranscriptionError("decode failed")

    box.tool(read_audio)
    with pytest.raises(transcription.TranscriptionError):
        asyncio.run(box.run_tool("read_audio"))


def test_optional_tool_parameter_is_nullable_in_strict_schema():
    def example(count: int | None) -> str:
        return str(count)

    schema = generate_function_schema(example)["parameters"]
    assert schema["properties"]["count"]["type"] == ["integer", "null"]
    assert schema["required"] == ["count"]


@pytest.mark.parametrize("text", [None, 42, [], " "])
def test_context_rejects_invalid_transcript_types(text):
    ctx = TranscriptContext()
    assert ctx.set_cleaned_transcript(text)
    assert ctx.cleaned_transcript is None


def test_summary_before_cleaned_transcript_is_rejected():
    assert TranscriptContext().set_summary(["one", "two", "three"])


def test_export_failure_prevents_translation_callback(tmp_path, monkeypatch):
    monkeypatch.setattr(context, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(context, "write_outputs", Mock(side_effect=OSError("disk full")))
    callback = Mock()
    ctx = TranscriptContext(cleaned_transcript="Example.", on_translation_ready=callback)
    with pytest.raises(RuntimeError, match="disk full"):
        ctx.set_summary(["one", "two", "three"])
    callback.assert_not_called()


def test_agent_loop_is_bounded(monkeypatch):
    response = SimpleNamespace(output=[SimpleNamespace(type="reasoning")])
    client = SimpleNamespace(responses=SimpleNamespace(create=AsyncMock(return_value=response)))
    monkeypatch.setattr(agent, "client", client)
    config = {"name": "example", "prompt": "test", "tools": [], "kwargs": None}
    with pytest.raises(RuntimeError, match="exceeded 2 turns"):
        asyncio.run(agent.run_agent(config, ToolBox(), None, max_turns=2))
    assert client.responses.create.call_count == 2


def test_export_writes_aligned_files(tmp_path):
    pytest.importorskip("fpdf", reason="PDF export dependency is required for this integration check")
    from tools.exporters import write_outputs

    outputs = write_outputs(
        output_dir=tmp_path,
        stem="example",
        cleaned_transcript="Hello world.",
        summary=["An illustrative greeting."],
        metadata={},
    )
    assert set(outputs) == {"json", "docx", "pdf"}
    assert all(path.is_file() and path.stat().st_size for path in outputs.values())
    assert json.loads(outputs["json"].read_text())["transcript_lines"] == ["Hello world."]
    assert outputs["pdf"].read_bytes().startswith(b"%PDF")
