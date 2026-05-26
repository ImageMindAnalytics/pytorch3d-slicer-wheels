# Setup guide

## One-time setup of the wheel-building repo

1. Create a new public GitHub repo (e.g. `pytorch3d-slicer-wheels`) and
   push these files to its `main` branch.

2. In the repo settings:
   - **Pages** → Source: "Deploy from a branch", Branch: `gh-pages` / `(root)`.
     The first publish workflow run will create the `gh-pages` branch.
   - **Actions** → General → Workflow permissions: "Read and write
     permissions". Needed for the publish step to push to gh-pages.

## First build

From the GitHub Actions tab, run each workflow manually
(`workflow_dispatch`) with `publish: true`:

- **Build Windows wheels** — fans out across the rows in `matrix.yml`
  (torch 2.6.0+cu124, 2.8.0+cu129, 2.8.0+cpu) on `windows-2022`.
- **Build Windows wheels cu130** — torch 2.12.0+cu130 from
  `matrix-cu130.yml`. Kept in a separate workflow because of
  cu130-specific NVCC flags.
- **Build macOS wheels** — torch 2.2.2+cpu from `matrix-macos.yml` on
  `macos-13` (Intel).

Each runner installs its toolchain (CUDA / MSVC / clang) and the matching
torch, then builds pytorch3d 0.7.9 from source. Expect 25-40 minutes per
wheel. After build finishes, each workflow's publish job additively
merges its artifacts into `gh-pages` (the workflows share a
`gh-pages-deploy` concurrency group so they queue, not race).

When all three are done, browse to your Pages URL. You should see a
landing page and `simple/pytorch3d/` listing one `.whl` per matrix row.

## Installing into Slicer

Run this in Slicer's Python console:

```python
import slicer.util
slicer.util.pip_install(
    "pytorch3d==0.7.9 "
    "--extra-index-url https://ImageMindAnalytics.github.io/pytorch3d-slicer-wheels/simple/"
)
import pytorch3d
print(pytorch3d.__version__)
```

## Updating the matrix

When Slicer bumps Python, or when you want to support a new torch,
edit the relevant matrix file (`matrix.yml`, `matrix-cu130.yml`, or
`matrix-macos.yml`), push, and re-run that workflow. Publishing is
additive: each workflow's publish job merges its new wheels with the
wheels already on `gh-pages`, so building a subset of the matrix
doesn't wipe the others.

To retire an old wheel, delete it from the `gh-pages` branch directly
(or from `simple/pytorch3d/` in a worktree) and regenerate the index
with `scripts/make_index.py`.

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
