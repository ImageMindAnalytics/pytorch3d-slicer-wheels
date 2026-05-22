cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(PyTorch3D)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/ImageMindAnalytics/pytorch3d-slicer-wheels")
set(EXTENSION_CATEGORY "Utilities")
set(EXTENSION_CONTRIBUTORS "Juan Prieto (UNC)")
set(EXTENSION_DESCRIPTION
  "Installs PyTorch3D into Slicer's bundled Python using prebuilt wheels.")
set(EXTENSION_ICONURL "")
set(EXTENSION_SCREENSHOTURLS "")
set(EXTENSION_DEPENDS "PyTorch")

#-----------------------------------------------------------------------------
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
add_subdirectory(PyTorch3DUtils)

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
