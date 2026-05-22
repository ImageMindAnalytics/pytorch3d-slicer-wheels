"""
PyTorch3DUtils
--------------

A scripted Slicer module that installs PyTorch3D into Slicer's bundled
Python, using prebuilt wheels hosted at WHEEL_INDEX_URL.

Modeled after fepegar/SlicerPyTorch but specialized for pytorch3d:
- pytorch3d has no PyPI wheels for Windows, so we serve them from a
  GitHub Pages PEP 503 index.
- The wheel ABI is pinned to a specific (Slicer python, torch, cuda)
  combination. If the user's torch doesn't match, we surface a clear
  error instead of letting pip try to compile from source.

Usage from other Slicer modules:

    import PyTorch3DUtils
    pt3d = PyTorch3DUtils.PyTorch3DUtilsLogic().pytorch3d
    # pytorch3d is now importable
"""

import logging
import platform
import sys
from typing import Optional

import qt
import slicer
from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleLogic,
    ScriptedLoadableModuleWidget,
)


# -----------------------------------------------------------------------------
# CONFIGURE THESE for your fork.
# -----------------------------------------------------------------------------

# The PEP 503 simple index served from gh-pages.
WHEEL_INDEX_URL = "https://ImageMindAnalytics.github.io/pytorch3d-slicer-wheels/simple/"

# What we built our wheels against. Each (torch, backend) pair must map
# to a wheel published on WHEEL_INDEX_URL whose PEP 440 local version is
# "pt" + torch.replace(".", "") + backend (matches scripts/build_one.py).
# If the user's installed torch+backend doesn't match any pair by
# major.minor, the binary would fail to import at runtime, so we check
# up-front and explain.
SUPPORTED_WHEELS = [
    ("2.6.0", "cu124"),
    ("2.8.0", "cu129"),
    ("2.8.0", "cpu"),
]
SUPPORTED_PYTHON = (3, 12)
SUPPORTED_PYTORCH3D = "0.7.9"


def _major_minor(version: str) -> str:
    """Return 'X.Y' from a version string like '2.6.0' or '2.6.0+cu124'."""
    return ".".join(version.split("+")[0].split(".")[:2])


def _find_supported_wheel(torch_ver: str, backend: str):
    """Return the (torch, backend) entry from SUPPORTED_WHEELS matching the
    user's installed torch by major.minor and backend exactly, else None."""
    installed_mm = _major_minor(torch_ver)
    for t, b in SUPPORTED_WHEELS:
        if _major_minor(t) == installed_mm and b == backend:
            return (t, b)
    return None


# -----------------------------------------------------------------------------
# Module registration
# -----------------------------------------------------------------------------

class PyTorch3DUtils(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        parent.title = "PyTorch3D Utils"
        parent.categories = ["Utilities"]
        parent.dependencies = ["PyTorchUtils"]
        parent.contributors = ["Juan Prieto (UNC)"]
        parent.helpText = (
            "Install PyTorch3D into Slicer's bundled Python.\n\n"
            "PyTorch3D has no Windows wheels on PyPI. This module installs "
            "prebuilt wheels from a custom index that match Slicer's bundled "
            "Python and the torch version installed by SlicerPyTorch."
        )
        parent.acknowledgementText = (
            "Wheels built by the pytorch3d-slicer-wheels project. PyTorch3D "
            "is developed by Meta AI (FAIR)."
        )


# -----------------------------------------------------------------------------
# Logic
# -----------------------------------------------------------------------------

class PyTorch3DUtilsLogic(ScriptedLoadableModuleLogic):
    """Programmatic API for installing and accessing pytorch3d."""

    @property
    def pytorch3d(self):
        """
        Lazy-import pytorch3d, installing it first if necessary.
        Mirrors PyTorchUtilsLogic().torch from SlicerPyTorch.
        """
        try:
            import pytorch3d  # noqa: F401
        except ImportError:
            logging.info("pytorch3d not found; installing...")
            self.install()
            self._reload_modules()
            import pytorch3d  # noqa: F401
        import pytorch3d
        return pytorch3d

    # -- Status checks ------------------------------------------------------

    def is_installed(self) -> bool:
        try:
            import pytorch3d  # noqa: F401
            return True
        except ImportError:
            return False

    def installed_version(self) -> Optional[str]:
        try:
            import pytorch3d
            return getattr(pytorch3d, "__version__", "unknown")
        except ImportError:
            return None

    def installed_torch_version(self) -> Optional[str]:
        try:
            import torch
            return torch.__version__
        except ImportError:
            return None

    # -- Pre-flight ---------------------------------------------------------

    def _check_platform(self) -> Optional[str]:
        """Return None if platform is supported, error message otherwise."""
        if platform.system() != "Windows":
            return (
                f"This wheel index only ships Windows wheels at the moment. "
                f"Detected platform: {platform.system()}. "
                f"See {WHEEL_INDEX_URL} for the current build matrix."
            )
        if sys.version_info[:2] != SUPPORTED_PYTHON:
            return (
                f"Slicer's Python is {sys.version_info[0]}.{sys.version_info[1]} "
                f"but the wheels are built for "
                f"{SUPPORTED_PYTHON[0]}.{SUPPORTED_PYTHON[1]}. "
                f"This module needs to be updated for your Slicer version."
            )
        return None

    def _check_torch(self) -> Optional[str]:
        """Return None if torch is OK, error message otherwise."""
        torch_ver = self.installed_torch_version()
        if torch_ver is None:
            return (
                "PyTorch is not installed. Install it first using the "
                "PyTorch extension (PyTorch Utils module), then return here."
            )
        backend = self._detect_backend()
        if _find_supported_wheel(torch_ver, backend) is None:
            available = ", ".join(f"torch {t}+{b}" for t, b in SUPPORTED_WHEELS)
            return (
                f"Installed torch {torch_ver} (backend {backend}) doesn't "
                f"match any wheel in our index.\n"
                f"Available: {available}\n\n"
                f"Options:\n"
                f"  1. Reinstall torch via PyTorch Utils, choosing a version "
                f"     and backend in the available list.\n"
                f"  2. Add a matching row to matrix.yml in pytorch3d-slicer-"
                f"wheels and rebuild.\n"
            )
        return None

    def _detect_backend(self) -> str:
        """Return e.g. 'cu124', 'cu129', or 'cpu' based on torch's build."""
        torch_ver = self.installed_torch_version() or ""
        if "+cu" in torch_ver:
            # e.g. "2.6.0+cu124" -> "cu124"
            return torch_ver.split("+")[1]
        return "cpu"

    # -- Install ------------------------------------------------------------

    def install(self, force: bool = False):
        """
        Install pytorch3d via pip from the custom index.
        Raises RuntimeError on pre-flight failure.
        """
        if self.is_installed() and not force:
            logging.info(
                f"pytorch3d already installed ({self.installed_version()}); "
                f"skipping. Pass force=True to reinstall."
            )
            return

        err = self._check_platform()
        if err:
            raise RuntimeError(err)
        err = self._check_torch()
        if err:
            raise RuntimeError(err)

        # _check_torch already verified a wheel exists for (torch, backend).
        backend = self._detect_backend()
        match = _find_supported_wheel(self.installed_torch_version(), backend)
        torch_for_wheel, _ = match

        # Local version specifier targets our exact wheel.
        # Format mirrors scripts/build_one.py: "pt" + torch.replace(".","") + backend
        # e.g. torch 2.6.0 + cu124 -> "pt260cu124"
        torch_compact = torch_for_wheel.replace(".", "")
        backend_local = f"pt{torch_compact}{backend}"
        spec = f"pytorch3d=={SUPPORTED_PYTORCH3D}+{backend_local}"

        logging.info(f"Installing {spec} from {WHEEL_INDEX_URL}")

        # Prefer slicer.packaging (5.11+) if available; fall back to pip_install.
        try:
            import slicer.packaging
            slicer.packaging.pip_install([
                spec,
                "--extra-index-url", WHEEL_INDEX_URL,
            ])
        except (ImportError, AttributeError):
            slicer.util.pip_install(
                f'"{spec}" --extra-index-url {WHEEL_INDEX_URL}'
            )

    def uninstall(self):
        slicer.util.pip_uninstall("pytorch3d")

    def _reload_modules(self):
        """Drop cached pytorch3d submodules so a fresh import works."""
        stale = [m for m in sys.modules if m == "pytorch3d" or m.startswith("pytorch3d.")]
        for m in stale:
            del sys.modules[m]


# -----------------------------------------------------------------------------
# Widget (UI)
# -----------------------------------------------------------------------------

class PyTorch3DUtilsWidget(ScriptedLoadableModuleWidget):

    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.logic = PyTorch3DUtilsLogic()

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Status group
        statusBox = qt.QGroupBox("Status")
        statusLayout = qt.QFormLayout(statusBox)
        self.torchLabel = qt.QLabel("...")
        self.pytorch3dLabel = qt.QLabel("...")
        self.backendLabel = qt.QLabel("...")
        statusLayout.addRow("PyTorch:", self.torchLabel)
        statusLayout.addRow("PyTorch3D:", self.pytorch3dLabel)
        statusLayout.addRow("Backend:", self.backendLabel)
        self.layout.addWidget(statusBox)

        # Install button
        self.installButton = qt.QPushButton("Install PyTorch3D")
        self.installButton.toolTip = (
            "Install PyTorch3D into Slicer's Python using a prebuilt wheel."
        )
        self.installButton.connect("clicked()", self.onInstall)
        self.layout.addWidget(self.installButton)

        # Reinstall / uninstall in a row
        row = qt.QHBoxLayout()
        self.reinstallButton = qt.QPushButton("Reinstall")
        self.reinstallButton.connect("clicked()", self.onReinstall)
        self.uninstallButton = qt.QPushButton("Uninstall")
        self.uninstallButton.connect("clicked()", self.onUninstall)
        row.addWidget(self.reinstallButton)
        row.addWidget(self.uninstallButton)
        self.layout.addLayout(row)

        self.layout.addStretch(1)
        self.refreshStatus()

    def refreshStatus(self):
        self.torchLabel.text = self.logic.installed_torch_version() or "not installed"
        self.pytorch3dLabel.text = self.logic.installed_version() or "not installed"
        try:
            self.backendLabel.text = self.logic._detect_backend()
        except Exception:
            self.backendLabel.text = "unknown"
        self.installButton.enabled = not self.logic.is_installed()
        self.reinstallButton.enabled = self.logic.is_installed()
        self.uninstallButton.enabled = self.logic.is_installed()

    def onInstall(self):
        self._run_install(force=False)

    def onReinstall(self):
        self._run_install(force=True)

    def onUninstall(self):
        with slicer.util.tryWithErrorDisplay("Failed to uninstall pytorch3d"):
            self.logic.uninstall()
        self.refreshStatus()

    def _run_install(self, force):
        with slicer.util.tryWithErrorDisplay("Failed to install pytorch3d"):
            slicer.app.setOverrideCursor(qt.Qt.WaitCursor)
            try:
                self.logic.install(force=force)
            finally:
                slicer.app.restoreOverrideCursor()
        self.refreshStatus()
        if self.logic.is_installed():
            slicer.util.infoDisplay(
                f"PyTorch3D {self.logic.installed_version()} installed.\n\n"
                f"You may need to restart Slicer for the import to work in "
                f"already-loaded modules."
            )
