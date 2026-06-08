# AI Audio Transcriber

An end-to-end, multi-agent pipeline that turns raw audio — interviews, lectures,
meetings — into clean transcripts and structured, bullet-point summaries. Drop in an
audio file and the pipeline transcribes it locally, cleans and summarizes it with a
team of LLM agents, and exports the result to JSON, DOCX, and PDF, with optional
translation into ten languages.

Run it from the command line or through a drag-and-drop web UI.

---

## How it works

```
                ┌──────────────────────────────────────────────────────┐
   audio file   │  faster-whisper (local, CPU)  ──►  raw transcript     │
   ───────────► │                                          │            │
                │                                          ▼            │
                │   Coordinator agent  ◄────────►  Cleaner agent         │
                │   (greets, gathers           (cleans, formats,        │
                │    preferences, delegates)    summarizes)              │
                └──────────────────────────────────────────│───────────┘
                                                            ▼
                              JSON · DOCX · PDF   (+ optional translation)
```

- **Local transcription.** Audio is transcribed on-device with
  [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (`base` model, int8, CPU) —
  no audio ever leaves your machine for the speech-to-text step.
- **Multi-agent cleaning & summarization.** A two-agent system, defined declaratively in
  [`agents.yaml`](agents.yaml), refines the transcript:
  - **Coordinator** — the user-facing agent. Greets, gathers preferences (focus areas,
    number of summary bullets), retrieves the transcript, and delegates.
  - **Cleaner** — removes filler words, fixes grammar and punctuation, strips timestamps
    while preserving speaker labels and `[inaudible]` markers, and writes a concise
    bullet-point summary.
- **Shared context.** Agents read from and write to a shared context object, so
  transcription can run in the background and block the cleaner only when its output is
  actually needed.
- **Optional translation.** After the transcript and summary are ready, translation runs
  concurrently and emits a separate set of output files per target language.
- **Multi-format export.** Every run produces `JSON`, `DOCX`, and `PDF` artifacts in
  `output/`.

## Prerequisites

- **Python 3.12+**
- **ffmpeg** — required by the audio libraries (`pydub`, `faster-whisper`)
  - Linux: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: [download from ffmpeg.org](https://ffmpeg.org/download.html)
- **OpenAI API key** with access to the models used for cleaning, summarization, and
  translation.

> This project targets a Unix-style terminal (Linux, macOS, WSL). The Dev Container
> below is the most reliable way to run it on Windows.

## Setup

Secrets are loaded from a `.env` file at the project root:

```bash
echo "OPENAI_API_KEY=your_api_key_here" >> .env
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Command line

```bash
python3 agent.py [-h] [-v] [-t LANG_CODE] path/to/audio/file
```

| Flag | Description |
|------|-------------|
| `-h` | Show help and exit |
| `-v` | Verbose/debug logging for each pipeline step |
| `-t`  | Translate the output to a target language (see codes below) |

- **Supported audio formats:** `.mp3`, `.wav`, `.m4a`, `.flac`
- **Supported translation languages:** `en`, `zh`, `fr`, `es`, `de`, `ja`, `ko`, `pt`,
  `ar`, `ru`. Translation runs concurrently after the transcript and summary are ready
  and writes a parallel set of output files with a language suffix (e.g. `test_es.json`).

Output files are written to `output/`.

### Web UI (Gradio)

```bash
python3 gradio_app.py
```

Open **http://localhost:7860** to:

- Upload an audio file via drag-and-drop or file picker
- Click **Transcribe** to run the full agent pipeline
- Watch the cleaned transcription and summary stream in as each step completes

Internally, `gradio_app.py` runs `agent.py` as a subprocess and communicates over a
structured event protocol ([`runtime_events.py`](runtime_events.py)). The UI auto-replies
to the coordinator so the pipeline runs hands-free; per-run logs are saved under `logs/`.

## Project structure

```
.
├── agent.py                 # CLI entry point + agent runtime loop
├── gradio_app.py            # web UI; drives agent.py as a subprocess
├── agents.yaml              # declarative definition of the coordinator + cleaner agents
├── runtime_events.py        # event protocol bridging the UI and the pipeline
├── config.py                # loads agent config (yaml / json / md)
├── tools/
│   ├── transcription.py     # local faster-whisper transcription
│   ├── translation.py       # concurrent multi-language translation
│   ├── exporters.py         # JSON / DOCX / PDF output
│   ├── context.py           # shared transcript context
│   ├── coordinator_tools.py # tools exposed to the coordinator agent
│   ├── cleaner_tools.py     # tools exposed to the cleaner agent
│   └── toolbox.py           # tool registry
├── tests/                   # pytest suite
├── audio/                   # input audio (gitignored)
└── output/                  # generated transcripts & summaries (gitignored)
```

## Running with Docker

### Docker Compose

```bash
docker compose up --build
docker compose exec app bash
```

Builds from `Dockerfile.dev` and volume-mounts the project, so local edits are reflected
immediately.

### VS Code Dev Container (recommended for development)

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Install the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension.
3. Open the cloned folder in VS Code and choose **Reopen in Container** when prompted
   (or run `Dev Containers: Reopen in Container` from the command palette).
4. The first build installs everything; later starts are fast.
5. If dependencies change, run `Dev Containers: Rebuild Container Without Cache`.

> If import warnings appear, run `Python: Select Interpreter` → `/usr/local/bin/python`
> (3.12). Place audio in the local `audio/` folder; it is mirrored into the container and
> gitignored to avoid committing large files.

## Development

This project uses [ruff](https://docs.astral.sh/ruff/) for linting, enforced by a
[pre-commit](https://pre-commit.com/) hook on push, and `pytest` for tests.

```bash
# install the pre-push hook (automatic in the dev container)
pre-commit install --hook-type pre-push

ruff check .            # lint
ruff check --fix .      # auto-fix
pytest                  # run the test suite
```

Continuous integration runs via GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Acknowledgements

This repository is a fork of
[kennionblack/ai-audio-transcriber](https://github.com/kennionblack/ai-audio-transcriber).
See the upstream project for original authorship and history.
