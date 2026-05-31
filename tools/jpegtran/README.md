# Bundled jpegtran

This directory contains the Windows x64 `jpegtran` runtime used for lossless JPEG rotation.

- Source project: libjpeg-turbo
- Version: 3.1.4.1
- Downloaded asset: `libjpeg-turbo-3.1.4.1-vc-x64.exe`
- Download URL: https://github.com/libjpeg-turbo/libjpeg-turbo/releases/download/3.1.4.1/libjpeg-turbo-3.1.4.1-vc-x64.exe
- SHA256: `2bb347f106473c12635bdd414b1f289de9f4d6dea4a496d3f9dd212db9eda0dc`

Files included:

- `jpegtran.exe`
- `jpeg62.dll`
- `LICENSE-libjpeg-turbo.md`

`jpeg62.dll` is required by `jpegtran.exe`; the executable does not run correctly as a standalone file without it.
