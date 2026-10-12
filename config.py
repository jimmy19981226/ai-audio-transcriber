from pathlib import Path
from typing import TypedDict


class Agent(TypedDict):
    name: str
    description: str
    prompt: str
    model: str
    tools: list[str]
    kwargs: dict | None


class Config(TypedDict):
    agents: list[Agent]
    main: str


def load_config(config_path: Path | str = "agents.yaml") -> Config:
    """Read an agent configuration from a path or filename."""
    config_path = Path(config_path)
    ext = config_path.suffix.lower()
    if ext in [".yaml", ".yml"]:
        import yaml

        return yaml.safe_load(config_path.read_text(encoding="utf-8"))

    elif ext in [".json"]:
        import json

        return json.loads(config_path.read_text(encoding="utf-8"))

    elif ext in [".md", ".mdd"]:
        import markdowndata

        return markdowndata.loads(config_path.read_text(encoding="utf-8"))

    else:
        raise NotImplementedError(f"Unsupported config format: {config_path.suffix}")
