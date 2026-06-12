from __future__ import annotations

from pathlib import Path

from .resources import iter_mesh_example_files


def init_project(mesh_dir: Path, *, force: bool = False) -> None:
    mesh_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped: list[Path] = []

    for filename, content in iter_mesh_example_files():
        path = mesh_dir / filename

        if path.exists() and not force:
            skipped.append(path)
            continue

        path.write_text(content, encoding="utf-8")
        created += 1
        print(f"created: {path}")

    if skipped:
        print("")
        print("Skipped existing files:")
        for path in skipped:
            print(f"  {path}")
        print("")
        print("Use --force to overwrite them.")

    print("")
    print(f"mesh files created: {created}")
