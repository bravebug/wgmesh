from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Iterable


def package_templates_dir() -> Path:
    return Path(str(files("wgmesh") / "templates"))


def iter_mesh_example_files() -> Iterable[tuple[str, str]]:
    examples_dir = files("wgmesh") / "examples" / "mesh"

    for item in examples_dir.iterdir():
        name = item.name
        if not name.endswith(".yaml.example"):
            continue

        target_name = name.removesuffix(".example")
        yield target_name, item.read_text(encoding="utf-8")
