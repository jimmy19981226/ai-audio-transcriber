from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

from tools import print_verbose

MODEL_NAME = "base"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"
BEAM_SIZE = 5

_MODEL: "WhisperModel | None" = None


class TranscriptionError(RuntimeError):
    """Audio could not be decoded into a non-empty transcript."""


def _get_model() -> "WhisperModel":
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel

        print_verbose(f"[transcription] loading whisper model {MODEL_NAME!r} on {DEVICE}/{COMPUTE_TYPE}")
        _MODEL = WhisperModel(MODEL_NAME, device=DEVICE, compute_type=COMPUTE_TYPE)
    return _MODEL


def load_audio_file(file_path: str) -> str:
    """Transcribe audio, raising on failure so error messages never become data."""
    if not Path(file_path).is_file():
        raise TranscriptionError(f"Audio file not found: {file_path}")

    try:
        model = _get_model()
        print_verbose(f"[transcription] using model={MODEL_NAME!r}")
        segments, _ = model.transcribe(
            file_path,
            beam_size=BEAM_SIZE,
        )

        full_transcript = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                full_transcript.append(text)
        transcript = " ".join(full_transcript)
        if not transcript:
            raise TranscriptionError("No speech was detected in the audio file")
        return transcript
    except TranscriptionError:
        raise
    except Exception as exc:
        raise TranscriptionError(f"Could not transcribe {Path(file_path).name}: {exc}") from exc
