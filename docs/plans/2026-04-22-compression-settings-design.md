# Compression Settings Design

## Goal

Add advanced compression controls so users can choose how aggressively the app reduces file size.

## Approved Direction

Use advanced settings instead of a simple preset selector.

The first version adds three controls:

- Image maximum resolution: `800`, `1200`, `1600`, or keep original dimensions.
- JPEG quality: `50`, `65`, `78`, or `90`.
- PDF compression level: screen, ebook, printer, or prepress.

## UI

Add a compact settings row above the file table.

The row contains:

- A combo box for image maximum resolution.
- A combo box for JPEG quality.
- A combo box for PDF compression level.

Defaults are:

- Image maximum resolution: `1600`.
- JPEG quality: `78`.
- PDF compression level: screen.

## Engine Flow

The UI builds a `CompressionOptions` object from the selected controls and passes it to `compress_file(path, options)`.

The engine passes the same options to the relevant format compressor.

- ZIP-based document compression uses `max_dimension` and `jpeg_quality`.
- PDF compression maps the selected PDF preset to Ghostscript `-dPDFSETTINGS`.
- HWP and legacy Office adapters accept options for API consistency but still report their current unsupported automation state.

## Testing

Add tests for:

- Default option values.
- Image options reaching the image optimizer.
- PDF preset values in the Ghostscript command.
- UI-selected values being passed into the engine call.
