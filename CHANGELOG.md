# Changelog

## 1.0.0 - 2026-06-12

Initial stable release.

- YAML-driven WireGuard mesh configuration generator.
- `mesh/settings.yaml`, `mesh/peers.yaml`, `mesh/mesh.yaml` as source of truth.
- `wgmesh fill` for explicit `null` PrivateKey / mesh PSK values.
- `wgmesh build` for WireGuard configs and route artifacts.
- Jinja2 route templates for Keenetic and MikroTik.
- Bash completion helper.
- Human-readable errors for missing WireGuard CLI tools.
