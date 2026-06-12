from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined


ROUTE_TEMPLATES: dict[str, str] = {
    "routes.keenetic.txt": "routes/keenetic.txt.j2",
    "routes.mikrotik.rsc": "routes/mikrotik.rsc.j2",
}


def generate_route_files(
    *,
    templates_dir: Path,
    peer_id: str,
    interface_name: str,
    routes: list[str],
) -> dict[str, str]:
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    context = {
        "peer_id": peer_id,
        "interface_name": interface_name,
        "routes": routes,
    }

    rendered: dict[str, str] = {}

    for output_name, template_name in ROUTE_TEMPLATES.items():
        template = env.get_template(template_name)
        rendered[output_name] = template.render(**context)

    return rendered
