# Release guide

## 1. Create GitHub repository

```bash
git init
git add .
git commit -m "Initial wgmesh 1.0.0"
git branch -M main
git remote add origin git@github.com:bravebug/wgmesh.git
git push -u origin main
```

## 2. Create PyPI project with Trusted Publishing

1. Register / login at PyPI.
2. Create project `wgmesh` after the first upload prompt, or configure publishing from the PyPI project settings.
3. Add a Trusted Publisher:
   - owner: `bravebug`
   - repository: `wgmesh`
   - workflow name: `publish-pypi.yml`
   - environment name: `pypi`

No PyPI API token is needed.

## 3. Publish version

```bash
git tag v1.0.0
git push origin v1.0.0
```

Then create a GitHub Release for tag `v1.0.0`.

The `Publish to PyPI` workflow runs when the GitHub Release is published.

## 4. Build locally before release

```bash
python -m pip install --upgrade pip build
python -m build
python -m pip install -e .
wgmesh build --dry-run
```

## 5. Arch package

Use:

```text
packaging/arch/PKGBUILD
```

Package name:

```text
python-wgmesh
```

Before publishing to AUR, replace `sha256sums=("SKIP")` with the real checksum.

## 6. Debian / PPA

Debian packaging skeleton lives in:

```text
packaging/debian/
```

For a real Debian/PPA build, copy or move it to the source root as `debian/`
before running Debian packaging tools.

Example:

```bash
cp -a packaging/debian debian
dpkg-buildpackage -us -uc
```
