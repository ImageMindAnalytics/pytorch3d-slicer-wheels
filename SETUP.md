# Setup guide

## One-time setup of the wheel-building repo

1. Create a new public GitHub repo (e.g. `pytorch3d-slicer-wheels`) and
   push these files to its `main` branch.

2. In the repo settings:
   - **Pages** → Source: "Deploy from a branch", Branch: `gh-pages` / `(root)`.
     The first publish workflow run will create the `gh-pages` branch.
   - **Actions** → General → Workflow permissions: "Read and write
     permissions". Needed for the publish step to push to gh-pages.

3. Edit `slicer-module/PyTorch3DUtils/PyTorch3DUtils.py` and update
   `WHEEL_INDEX_URL` to point at your GitHub Pages URL:

   ```python
   WHEEL_INDEX_URL = "https://ImageMindAnalytics.github.io/pytorch3d-slicer-wheels/simple/"
   ```

   Do the same for the `EXTENSION_HOMEPAGE` in
   `slicer-module/CMakeLists.txt` if you intend to submit the module to
   the Slicer Extensions Index later.

## First build

From the GitHub Actions tab, run the **Build Windows wheels** workflow
manually (`workflow_dispatch`) with `publish: true`. The first run will:

1. Spin up two Windows runners in parallel — one for cu130, one for cpu.
2. Each runner installs CUDA (if needed), MSVC v143, torch 2.12.0, and
   builds pytorch3d 0.7.9 from source. Expect 25-40 minutes per wheel.
3. After both finish, the publish job downloads the artifacts, generates
   a PEP 503 index, and pushes to `gh-pages`.

When it's done, browse to your Pages URL. You should see a landing page
and `simple/pytorch3d/` listing two `.whl` files.

## Installing into Slicer (manual, for testing)

Before packaging as an extension, you can verify the wheels work by
running this in Slicer's Python console:

```python
import slicer.util
slicer.util.pip_install(
    "pytorch3d==0.7.9 "
    "--extra-index-url https://ImageMindAnalytics.github.io/pytorch3d-slicer-wheels/simple/"
)
import pytorch3d
print(pytorch3d.__version__)
```

If that works end-to-end, the module-based UX in
`slicer-module/PyTorch3DUtils/` should also work.

## Updating the matrix

When Slicer bumps Python, or when you want to support a new torch,
update `matrix.yml`, push, and re-run the workflow. Old wheels stay in
the index because `gh-pages` is replaced from artifacts on every run —
if you want to keep old versions, change `force_orphan: true` to
`false` in `.github/workflows/build-windows.yml` and merge instead.

## Troubleshooting

**Build fails with "Thrust requires at least C++17" or nvcc warning
"-std=c++20 flag is not supported with the configured host compiler".**
The MSVC toolset is too old for the C++ standard PyTorch requests. Make
sure the `ilammy/msvc-dev-cmd` step has no `toolset:` pin so the runner
uses its default v143 (VS 2022).

**Build fails during nvcc compilation with OOM.** Reduce `MAX_JOBS` in
`scripts/build_one.py` from 4 to 2.

**Smoke test fails with "undefined symbol" when importing pytorch3d.**
The wheel was built against a different torch ABI than what got
installed for the smoke test. Pin torchvision to a version that's known
to be released for your exact torch (check pytorch.org/whl/cu130).

**User reports "Installed torch X doesn't match Y" in Slicer.** The
SlicerPyTorch extension auto-selected a different torch version than
your wheels target. Either rebuild the wheels for that torch version, or
document which Slicer release / SlicerPyTorch version your wheels
support.
