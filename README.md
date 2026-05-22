# pytorch3d-slicer-wheels

Prebuilt PyTorch3D wheels for 3D Slicer's bundled Python.

## What this is

PyTorch3D doesn't publish Windows wheels on PyPI, so installing it into
Slicer's bundled Python normally requires compiling from source with a
matching CUDA toolkit and MSVC. This repo builds those wheels once in CI
and serves them through a PEP 503 "simple" index hosted on GitHub Pages.

A companion Slicer module (`slicer-module/PyTorch3DUtils/`) installs
pytorch3d into Slicer's Python with one click, modeled after the
SlicerPyTorch extension.

## Current build matrix

| Slicer | Python | torch    | CUDA  | OS         |
|--------|--------|----------|-------|------------|
| 5.10   | 3.12   | 2.6.0    | cu124 | win_amd64  |
| 5.10   | 3.12   | 2.8.0    | cu129 | win_amd64  |
| 5.10   | 3.12   | 2.12.0   | cu130 | win_amd64  |
| 5.10   | 3.12   | 2.12.0   | cpu   | win_amd64  |

PyTorch3D version: **0.7.9**

## Using the wheels directly

From a Slicer Python console:

```python
import slicer.packaging
# CPU
slicer.packaging.pip_ensure(
    "pytorch3d==0.7.9",
    extra_index_url="https://ImageMindAnalytics.github.io/pytorch3d-slicer-wheels/simple/",
)
```

## Building locally

You shouldn't need to. CI builds on every push to `main` and on manual
dispatch. If you do need to reproduce locally, see `scripts/build_one.py`
and the matching workflow in `.github/workflows/`.

## License

The build scripts here are MIT. The wheels they produce are PyTorch3D,
which is BSD-3-Clause.
