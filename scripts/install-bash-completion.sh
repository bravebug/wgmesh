#!/usr/bin/env bash
set -euo pipefail

src_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
src_file="${src_dir}/completion/wgmesh.bash"

target_dir="${HOME}/.local/share/bash-completion/completions"
target_file="${target_dir}/wgmesh"

mkdir -p "${target_dir}"
cp "${src_file}" "${target_file}"

echo "Installed bash completion:"
echo "  ${target_file}"
echo
echo "Reload your shell or run:"
echo "  source ${target_file}"
