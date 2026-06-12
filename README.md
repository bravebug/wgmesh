# wgmesh

WireGuard mesh topology generator.

The main documentation lives in config examples:

```text
mesh/settings.yaml.example
mesh/peers.yaml.example
mesh/mesh.yaml.example
```

Quick start:

```bash
pip install -e .
wgmesh init
wgmesh fill --build
```

Build only:

```bash
wgmesh build --clean
```

Validate/render without writing files:

```bash
wgmesh build --dry-run
```

Smoke test:

```bash
python -m compileall src/wgmesh
pip install -e .
wgmesh build --dry-run
test ! -d generated
wgmesh build --clean
test -f generated/office.example.com/wg0.conf
test -f generated/office.example.com/routes.keenetic.txt
test -f generated/office.example.com/routes.mikrotik.rsc
```

`wgmesh build` and `wgmesh build --dry-run` call `wg pubkey`, so WireGuard tools must be installed.

Output:

```text
generated/<peer>/
  wg0.conf
  routes.keenetic.txt
  routes.mikrotik.rsc
```

Principles:

- YAML is the source of truth.
- `mesh.yaml` defines both topology and PSK.
- Missing mesh entry means no connection.
- `null` is the only magic.
- `fill` changes only explicit `null` values.
- `build` never changes YAML.
- `build --dry-run` never writes generated files.
- Routes are simple route artifacts only; no firewall/policy rules.


## Bash completion

Install for current user:

```bash
./scripts/install-bash-completion.sh
```

or manually:

```bash
mkdir -p ~/.local/share/bash-completion/completions
cp completion/wgmesh.bash ~/.local/share/bash-completion/completions/wgmesh
```

Reload shell or run:

```bash
source ~/.local/share/bash-completion/completions/wgmesh
```


## Route templates

Route files are rendered from Jinja2 templates:

```text
templates/routes/keenetic.txt.j2
templates/routes/mikrotik.rsc.j2
```

Template context:

```text
peer_id
interface_name
routes
```

Use another template directory:

```bash
wgmesh --templates-dir ./templates build --clean
```


## Generators

Extra artifacts are generated through small generator modules:

```text
src/wgmesh/generators/
  __init__.py
  routes.py
```

Current generator:

```text
routes → routes.keenetic.txt, routes.mikrotik.rsc
```

Future generators can be plugged in the same style without changing
the core WireGuard config rendering.


## Runtime dependencies

Python dependencies are installed by pip:

```text
PyYAML
Jinja2
```

System dependency:

```text
wg
```

`wgmesh` calls:

```text
wg pubkey
wg genkey
wg genpsk
```

Install WireGuard tools:

```bash
# Debian/Ubuntu
sudo apt install wireguard-tools

# Fedora/RHEL
sudo dnf install wireguard-tools

# Alpine
sudo apk add wireguard-tools

# Arch Linux
sudo pacman -S wireguard-tools
```

Windows:

Install official WireGuard for Windows MSI. The command line tool is usually installed as:

```text
C:/Program Files/WireGuard/wg.exe
```

If needed, override the path:

```bash
WG_EXECUTABLE=/path/to/wg wgmesh build
```


## Platform adapter

WireGuard CLI access is isolated in:

```text
src/wgmesh/wg.py
```

All calls to external `wg` are made through this module.


License: MIT.


Release / packaging notes: see `RELEASE.md`.


Note: by default route templates are loaded from the installed Python package,
not from the current directory. Use `--templates-dir` only when you want custom
templates.
