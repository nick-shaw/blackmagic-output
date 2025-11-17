# Advanced Example: T-PAT Pattern Renderer

This example demonstrates advanced usage of the Blackmagic DeckLink output module by rendering Test Pattern Descriptor (T-PAT) files directly to SDI/HDMI output.

## What is T-PAT?

T-PAT (Test Pattern Descriptor) is a JSON-based file format for describing test patterns. It allows you to define complex test patterns using simple text files rather than image files. For more information, see the [test-pattern-descriptor](https://github.com/yergin/test-pattern-descriptor) repository on GitHub.

## Usage

```bash
python tpat_bmd.py <tpat_file> <display_mode> [options]
```

### Required Arguments

- `tpat_file` - Path to the T-PAT JSON file
- `display_mode` - Video display mode (must match pattern dimensions) one of:
  - `1080p25`, `1080p2997`, `1080p30`
  - `1080p50`, `1080p5994`, `1080p60`
  - `1080i50`, `1080i5994`, `1080i60`
  - `2160p25`, `2160p2997`, `2160p30`
  - `2160p50`, `2160p5994`, `2160p60`

### Optional Arguments

- `-p {YUV10,RGB10,RGB12}` - Pixel format (default: YUV10)
- `-r {full,narrow}` - Signal range (overrides T-PAT file if specified)
- `-m {Rec709,Rec2020}` - Y'CbCr matrix (overrides T-PAT file if specified)
- `-e {SDR,HLG,PQ}` - EOTF (overrides T-PAT file if specified)

## Examples

### HLG Narrow Range Pattern as 10-bit Y'CbCr
```bash
python display_tpat.py BT2111_HLG_10bit_narrow_1080.tpat 1080p50
```

### PQ Full Range Pattern as 10-bit RGB
```bash
python display_tpat.py BT2111_PQ_10bit_full_1080.tpat 1080p25 -p RGB10
```

The range, matrix and EOTF are specified in the T-PAT files, so do not need to be passed as arguments.

## Included Sample Patterns

- `BT2111_HLG_10bit_narrow_1080.tpat` - ITU-R BT.2111 HLG HDR test pattern
- `BT2111_PQ_10bit_full_1080.tpat` - ITU-R BT.2111 PQ HDR test pattern

**Note:** The full range PQ pattern is intended to be displayed as full range RGB, i.e. using `RGB10` or `RGB12` as the `PixelFormat`. Displaying it without specifying the pixel format will output full range `YUV10`, which is non-standard.

## Creating Your Own Patterns

You can create your own T-PAT files using the JSON format. See the [test-pattern-descriptor](https://github.com/yergin/test-pattern-descriptor) repository for:
- Format specification
- Schema documentation
- Additional pattern examples

## Requirements

- jsonschema (for T-PAT validation)
- imageio (optional, for image overlay features)
