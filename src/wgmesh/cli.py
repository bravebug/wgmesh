from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .build import build_configs
from .fill import fill_nulls
from .init import init_project
from .validate import ConfigError
from .wg import WireGuardToolsError


def main() -> None:
    parser = argparse.ArgumentParser(prog="wgmesh")
    parser.add_argument(
        "--mesh-dir",
        default="mesh",
        help="Directory with settings.yaml, peers.yaml, mesh.yaml",
    )
    parser.add_argument(
        "--output-dir",
        default="generated",
        help="Directory for generated configs",
    )
    parser.add_argument(
        "--templates-dir",
        default=None,
        help="Optional directory with custom Jinja2 templates",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="Create mesh config files from packaged examples")
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing mesh config files",
    )

    build_parser = sub.add_parser("build", help="Generate WireGuard configs")
    build_parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove output directory before generation",
    )
    build_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and render in memory without writing generated files",
    )

    fill_parser = sub.add_parser("fill", help="Fill explicit null PrivateKey/mesh PSK values")
    fill_parser.add_argument(
        "--build",
        action="store_true",
        help="Run build after filling null values",
    )

    args = parser.parse_args()

    templates_dir = Path(args.templates_dir) if args.templates_dir else None

    try:
        if args.command == "init":
            init_project(
                mesh_dir=Path(args.mesh_dir),
                force=args.force,
            )

        elif args.command == "build":
            build_configs(
                mesh_dir=Path(args.mesh_dir),
                output_dir=Path(args.output_dir),
                templates_dir=templates_dir,
                clean=args.clean,
                dry_run=args.dry_run,
            )

        elif args.command == "fill":
            fill_nulls(
                mesh_dir=Path(args.mesh_dir),
                run_build=args.build,
                output_dir=Path(args.output_dir),
                templates_dir=templates_dir,
            )

    except (ConfigError, FileNotFoundError, RuntimeError, KeyError, ValueError, WireGuardToolsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
