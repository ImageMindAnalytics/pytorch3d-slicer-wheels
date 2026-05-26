# pytorch3d-slicer-wheels

Prebuilt PyTorch3D wheels for 3D Slicer's bundled Python.

## What this is

PyTorch3D doesn't publish Windows wheels on PyPI, so installing it into
Slicer's bundled Python normally requires compiling from source with a
matching CUDA toolkit and MSVC. This repo builds those wheels once in CI
and serves them through a PEP 503 "simple" index hosted on GitHub Pages.

## Current build matrix

| Slicer | Python | torch    | CUDA  | OS                  |
|--------|--------|----------|-------|---------------------|
| 5.10   | 3.12   | 2.6.0    | cu124 | win_amd64           |
| 5.10   | 3.12   | 2.8.0    | cu129 | win_amd64           |
| 5.10   | 3.12   | 2.8.0    | cpu   | win_amd64           |
| 5.10   | 3.12   | 2.12.0   | cu130 | win_amd64           |
| 5.10   | 3.12   | 2.2.2    | cpu   | macosx_10_13_x86_64 |

PyTorch3D version: **0.7.9**

## Using the wheels directly

From a Slicer Python console (pin to the local-version tag of the wheel
that matches your installed torch — `+pt260cu124` for torch 2.6.0+cu124,
`+pt280cu129` for torch 2.8.0+cu129, `+pt280cpu` for torch 2.8.0+cpu):

```python
import slicer.util
slicer.util.pip_install(
    "pytorch3d==0.7.9+pt260cu124 "
    "--extra-index-url https://ImageMindAnalytics.github.io/pytorch3d-slicer-wheels/simple/"
)
```

## Building locally

You shouldn't need to. CI builds on every push to `main` and on manual
dispatch. If you do need to reproduce locally, see `scripts/build_one.py`
and the matching workflow in `.github/workflows/`.

## License

The build scripts here are MIT. The wheels they produce are PyTorch3D,
which is BSD-3-Clause.
