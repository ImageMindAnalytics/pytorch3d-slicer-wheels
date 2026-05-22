"""
Build one pytorch3d wheel.

Invoked by the GitHub Actions workflow. Reads parameters from CLI args so
the workflow can pass a row from matrix.yml.

Assumes the environment is already set up:
  - Python of the requested version is on PATH
  - CUDA toolkit is installed (if cuda != "cpu") and CUDA_HOME is set
  - MSVC v142 is active (we use vcvarsall.bat in the workflow)
  - The pytorch3d source tree is checked out at $PYTORCH3D_SRC

Outputs: a single .whl in $OUTPUT_DIR.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd, **kwargs):
    print(f"$ {' '.join(str(c) for c in cmd)}", flush=True)
    return subprocess.run(cmd, check=True, **kwargs)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--python", required=True, help="e.g. 3.12")
    p.add_argument("--torch", required=True, help="e.g. 2.5.1")
    p.add_argument("--torchvision", required=True, help="e.g. 0.20.1")
    p.add_argument("--cuda", required=True, help="'cpu' or '12.4'")
    p.add_argument("--pytorch3d", required=True, help="e.g. 0.7.9")
    p.add_argument("--src", required=True, help="pytorch3d source dir")
    p.add_argument("--out", required=True, help="output wheel dir")
    args = p.parse_args()

    src = Path(args.src).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        sys.exit(f"pytorch3d source not found at {src}")

    # 1. Install build dependencies (torch + everything pytorch3d setup.py imports)
    pip = [sys.executable, "-m", "pip"]
    run(pip + ["install", "-U", "pip", "wheel", "setuptools", "ninja"])

    if args.cuda == "cpu":
        torch_index = "https://download.pytorch.org/whl/cpu"
    else:
        # 12.4 -> cu124
        cuda_tag = "cu" + args.cuda.replace(".", "")
        torch_index = f"https://download.pytorch.org/whl/{cuda_tag}"

    run(
        pip
        + [
            "install",
            f"torch=={args.torch}",
            f"torchvision=={args.torchvision}",
            "--index-url",
            torch_index,
        ]
    )
    run(pip + ["install", "fvcore", "iopath"])

    # 2. Configure pytorch3d build environment.
    env = os.environ.copy()
    env["DISTUTILS_USE_SDK"] = "1"
    env["PYTORCH3D_NO_NINJA"] = "0"
    env["MAX_JOBS"] = "4"  # avoid OOM on GH runners

    if args.cuda != "cpu":
        env["FORCE_CUDA"] = "1"
        # NVCC needs to know which arches to target. Restrict to common
        # consumer + datacenter compute capabilities to keep build time
        # bounded. Skip 9.0 (Hopper) here; add it back if you need H100.
        env["TORCH_CUDA_ARCH_LIST"] = "6.0;7.0;7.5;8.0;8.6;8.9"
    else:
        env["FORCE_CUDA"] = "0"
        # When building CPU-only, pytorch3d's setup.py still inspects
        # CUDA env vars. Make sure none leak through.
        for v in ("CUDA_HOME", "CUDA_PATH"):
            env.pop(v, None)

    # 3. Build the wheel.
    run(
        [sys.executable, "setup.py", "bdist_wheel", "--dist-dir", str(out)],
        cwd=src,
        env=env,
    )

    wheels = list(out.glob("pytorch3d-*.whl"))
    if not wheels:
        sys.exit("No wheel produced.")
    for w in wheels:
        print(f"Built: {w}")

    # 4. Tag the wheel with our local build identifier so users can tell
    #    which (torch, cuda) it was built against. Rename:
    #      pytorch3d-0.7.9-cp312-cp312-win_amd64.whl
    #    -> pytorch3d-0.7.9+pt251cu124-cp312-cp312-win_amd64.whl
    backend_tag = "cpu" if args.cuda == "cpu" else "cu" + args.cuda.replace(".", "")
    torch_tag = "pt" + args.torch.replace(".", "")
    local_id = f"{torch_tag}{backend_tag}"

    for w in wheels:
        # filename format: {dist}-{version}(-{build_tag})?-{python}-{abi}-{platform}.whl
        parts = w.stem.split("-")
        # parts: ['pytorch3d', '0.7.9', 'cp312', 'cp312', 'win_amd64']
        dist, version, *rest = parts
        # PEP 440 local version: append +local_id to version
        new_version = f"{version}+{local_id}"
        new_name = "-".join([dist, new_version, *rest]) + ".whl"
        new_path = w.with_name(new_name)
        w.rename(new_path)
        print(f"Renamed -> {new_path.name}")


if __name__ == "__main__":
    main()
