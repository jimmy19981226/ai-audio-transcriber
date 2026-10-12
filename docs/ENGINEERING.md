# Engineering and development notes

## Runtime boundaries

`agent.py` owns a tool registry and transcript context for its process. It starts local Whisper transcription in a thread, then runs the configured agent. Tools await the same transcription task. The cleaner writes a validated transcript and summary into shared context; the summary completion hook creates export files and can start translation.

`gradio_app.py` starts the CLI as a subprocess and consumes JSON events from stdout. The UI has shared process state and should be used as a local single-user application. A hosted multi-user version would need per-session state, isolated outputs, authentication, request limits, and lifecycle management.

Each `run_agent` invocation is limited to 30 turns by default. That bound applies to one invocation, not a global budget across recursively delegated agents. A centralized call/delegation budget would be a useful further improvement for a hosted service.

## Data flow

| Data | Destination |
| --- | --- |
| Audio | Local speech-recognition process; the first model load downloads weights |
| Raw transcript and user preferences | Configured OpenAI agents |
| Cleaned transcript and summary | Local context, exports, and optionally OpenAI translation |
| Runtime output | Gradio UI and local per-run logs |
| Generated files | `output/` by default; override with `OUTPUT_DIR` |

`.env`, audio inputs, output artifacts, and logs are ignored by Git. Development containers mount the project directory; keep private recordings and credentials out of version control and images. JSON and DOCX retain Unicode; the current PDF renderer's Latin-1 fallback can substitute characters in translated text.

## Development container

The repository includes a Docker Compose development service and a VS Code Dev Container configuration. With Docker installed:

```bash
docker compose up --build -d
docker compose exec app bash
python -m pytest -q
```

Or use VS Code's **Dev Containers: Reopen in Container** command. Inspect `Dockerfile.dev` and `.devcontainer.json` for the environment setup. Standard local development also works with the virtual-environment instructions in the main README.

## Validation strategy

- Unit and workflow tests use synthetic data and mocks for paid model calls.
- The real Whisper fixture is opt-in through `RUN_TRANSCRIPTION_INTEGRATION=1`.
- Document export tests check that JSON, DOCX, and PDF artifacts are created; visual document quality and multilingual rendering need separate review.
- Ruff checks and formatting apply to the maintained audio pipeline. The separate historical `professor_framework/` is retained for reference.

Run `python -m pytest -q`, `ruff check .`, and `ruff format --check .` before submitting changes. Document any changes to prompts, model configuration, tool schemas, events, or output formats because each can affect downstream consumers.

## Known next steps

Useful follow-up work includes a Unicode-font PDF renderer, session isolation in the UI, a global delegation budget, atomic export packages, a curated speech/summary evaluation set, and explicit handling of long recordings. These are proposed improvements rather than claims about current capability.

## Attribution

This fork retains the upstream MIT license and authorship. Keep the license notice and explain substantial behavioral changes in commit or pull-request descriptions. New examples should use synthetic or appropriately consented recordings.
