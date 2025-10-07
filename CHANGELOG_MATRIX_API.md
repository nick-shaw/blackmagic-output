# Changelog: Simplified HDR API with Matrix Parameter

## Summary

Enhanced `display_static_frame()` to accept optional `matrix` and `hdr_metadata` parameters, eliminating the need to use the lower-level API for HDR output.

## Changes

### 1. New `Matrix` Enum (High-level API)

Added `Matrix` enum to the high-level API for clearer naming when specifying RGB to Y'CbCr conversion matrices:

```python
from blackmagic_output import Matrix

Matrix.Rec709   # ITU-R BT.709 matrix (standard HD)
Matrix.Rec2020  # ITU-R BT.2020 matrix (wide color gamut)
```

**Note:** `Matrix` is an alias to the internal `Gamut` enum. The low-level API still uses `Gamut` for backward compatibility.

### 2. Enhanced `display_static_frame()` Signature

**Before:**
```python
def display_static_frame(frame_data, display_mode, pixel_format=PixelFormat.BGRA)
```

**After:**
```python
def display_static_frame(frame_data, display_mode,
                        pixel_format=PixelFormat.BGRA,
                        matrix=None,           # NEW: RGB→Y'CbCr matrix
                        hdr_metadata=None)     # NEW: HDR metadata dict
```

### 3. HDR Metadata Parameter

The `hdr_metadata` parameter accepts a dictionary:

```python
# Default metadata values
hdr_metadata = {'eotf': Eotf.PQ}

# Custom metadata values
hdr_metadata = {
    'eotf': Eotf.PQ,
    'custom': HdrMetadataCustom(...)
}
```

### 4. Updated Conversion Functions

The `matrix` parameter name is now used consistently throughout:

```python
# Before
dl.rgb_float_to_yuv10(frame, 1920, 1080, colorimetry=dl.Gamut.Rec2020)

# After (both forms work)
dl.rgb_float_to_yuv10(frame, 1920, 1080, matrix=dl.Matrix.Rec2020)
dl.rgb_float_to_yuv10(frame, 1920, 1080, dl.Matrix.Rec2020)
```

## Usage Examples

### Before (Required Low-level API)

```python
import decklink_output as dl

output = dl.DeckLinkOutput()
output.initialize()

# Step 1: Set HDR metadata (must be before setup_output)
output.set_hdr_metadata(dl.Gamut.Rec2020, dl.Eotf.PQ)

# Step 2: Setup output
settings = output.get_video_settings(dl.DisplayMode.HD1080p25)
settings.format = dl.PixelFormat.YUV10
output.setup_output(settings)

# Step 3: Convert with matching matrix
yuv_data = dl.rgb_float_to_yuv10(frame, 1920, 1080, dl.Gamut.Rec2020)
output.set_frame_data(yuv_data)

# Step 4: Start output
output.start_output()
```

### After (Simplified High-level API)

```python
from blackmagic_output import BlackmagicOutput, DisplayMode, PixelFormat, Matrix, Eotf

with BlackmagicOutput() as output:
    output.initialize()

    # All-in-one call: matrix and HDR metadata set automatically
    output.display_static_frame(
        frame,
        DisplayMode.HD1080p25,
        pixel_format=PixelFormat.YUV10,
        matrix=Matrix.Rec2020,
        hdr_metadata={'eotf': Eotf.PQ}
    )

    input("Press Enter to stop...")
```

## Benefits

1. **Simpler API**: Single function call instead of multiple steps
2. **Automatic consistency**: Matrix is automatically used for both metadata and conversion
3. **Less error-prone**: No need to remember call order or match matrix/gamut values
4. **Backward compatible**: Old code continues to work
5. **Clear naming**: `matrix` parameter makes it clear it controls the RGB→Y'CbCr conversion matrix

## Technical Implementation

- `Matrix` enum created in Python wrapper (blackmagic_output.py:21-24)
- `Matrix` aliased to `Gamut` in C++ bindings (python_bindings.cpp:246)
- `display_static_frame()` internally calls `set_hdr_metadata()` before `setup_output()` when HDR metadata is provided
- Matrix parameter stored in instance (`_current_matrix`) for use by `update_frame()`
- Conversion functions accept `matrix` parameter (backward compatible with positional args)

## Files Modified

1. `python_bindings.cpp` - Added Matrix enum alias, renamed parameter to `matrix`
2. `src/blackmagic_output/blackmagic_output.py` - Enhanced display_static_frame(), added Matrix/Eotf enums
3. `src/blackmagic_output/__init__.py` - Export Matrix and Eotf
4. `README.md` - Updated documentation with new examples
5. `examples/hdr_simple_api.py` - New example demonstrating simplified API

## Migration Guide

Existing code continues to work. To use the new simplified API:

1. Import `Matrix` and `Eotf` from `blackmagic_output`
2. Replace low-level HDR setup with `matrix` and `hdr_metadata` parameters in `display_static_frame()`
3. Optionally replace `colorimetry` with `matrix` in conversion function calls (both work)

## Testing

- Built and tested C++ extension successfully
- Verified Matrix enum works correctly
- Tested HDR metadata parameter parsing
- Confirmed backward compatibility with existing code
