# Blackmagic DeckLink Python Output Library

A Python library for outputting video frames to Blackmagic DeckLink devices using the official DeckLink SDK. This library provides a simple interface for displaying static frames, solid colors, and dynamic content from NumPy arrays.

Written by Nick Shaw, www.antlerpost.com, with a lot of help from [Claude Code](https://www.claude.com/product/claude-code)!

**⚠️ Note:** The library has only had minimal testing at this time. Please report any issues you encounter. I am particularly interested in feedback from Linux and Windows users.

## Features

- **Static Frame Output**: Display static images from NumPy arrays
- **Solid Color Output**: Display solid colors for testing and calibration
- **Dynamic Updates**: Update displayed frames in real-time
- **Multiple Resolutions**: Support for all display modes supported by your DeckLink device (SD, HD, 2K, 4K, 8K, and PC modes)
- **10-bit Y'CbCr Output**: 10-bit Y'CbCr 4:2:2 (v210) (default for uint16/float data)
- **10 and 12-bit R'G'B' output**: 10 and 12-bit R'G'B' 4:4:4
- **Automatic Format Detection**: Automatically uses optimal output format based on input data type
- **HDR Support**: Rec.2020 colorimetry with PQ and HLG transfer functions
- **Flexible Color Spaces**: Rec.709 and Rec.2020 matrix support
- **RP188 Timecode**: Embedded VITC and LTC timecode with auto-increment
- **Cross-Platform**: Works on Windows, macOS, and Linux (in theory - only macOS build tested so far)

## Requirements

### System Requirements
- Python 3.7 or higher
- Blackmagic DeckLink device (DeckLink, UltraStudio, or Intensity series)
- Blackmagic Desktop Video software installed

### Software Dependencies
- NumPy >= 1.19.0
- pybind11 >= 2.6.0
- Blackmagic DeckLink SDK (v14.1 headers included - see below)

## Installation

### 1. DeckLink SDK

**All Platforms (macOS, Windows, Linux):**

No additional download needed - SDK v14.1 headers for all platforms are included in the repository:
- `decklink_sdk/Mac/include/` - macOS headers
- `decklink_sdk/Win/include/` - Windows headers
- `decklink_sdk/Linux/include/` - Linux headers

The build system automatically uses the correct platform-specific headers.

**⚠️ Important:** This library is built against SDK v14.1. If you need to download the SDK separately, ensure you get v14.1 from [Blackmagic Design Developer](https://www.blackmagicdesign.com/developer/). Newer versions (v15.x) may cause API compatibility issues and build failures.

### 2. Build the Library

```bash
# Clone or download the library files
git clone https://github.com/nick-shaw/blackmagic-output.git
cd blackmagic-output

# Install Python dependencies
pip install numpy pybind11

# Build the C++ extension
python setup.py build_ext --inplace

# Optional: Install in development mode
pip install -e .

# If upgrading from a previous development version, force reinstall:
# pip install --force-reinstall -e .
```

### 3. Install Optional Dependencies

For examples and additional functionality:
```bash
pip install imageio pillow  # For image loading with 16-bit TIFF support
```

**Note:** While imageio/PIL can load 16-bit TIFF files correctly, 16-bit PNG files are often converted to 8-bit during loading due to PIL limitations. For reliable 16-bit workflows, use TIFF format.

## Quick Start

```python
import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode

# Create a simple test image (1080p R'G'B')
frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
frame[:, :] = [255, 0, 0]  # Red frame

# Display the frame
with BlackmagicOutput() as output:
    # Initialize device (uses first available device)
    output.initialize()
    
    # Display static frame at 1080p25
    output.display_static_frame(frame, DisplayMode.HD1080p25)
    
    # Keep displaying (Enter to stop)
    input("Press Enter to stop...")
```

## API Reference

The library provides two APIs:

1. **High-level Python wrapper** (`blackmagic_output.BlackmagicOutput`) - Convenient API for simple use cases
2. **Low-level direct access** (`decklink_output.DeckLinkOutput`) - Full control for advanced features (HDR, timecode)

### High-Level API: BlackmagicOutput Class

Convenient Python wrapper for simple video output operations.

#### Methods

**`__init__()`**
Create a new BlackmagicOutput instance.

**`initialize(device_index=0) -> bool`**
Initialize the specified DeckLink device.
- `device_index`: Index of device to use (default: 0)
- Returns: True if successful

**`get_available_devices() -> List[str]`**
Get list of available DeckLink device names.

**`setup_output(display_mode, pixel_format=PixelFormat.YUV10) -> bool`**
Setup video output parameters.
- `display_mode`: Video resolution and frame rate
- `pixel_format`: Pixel format (default: YUV10)
- Returns: True if successful

**`display_static_frame(frame_data, display_mode, pixel_format=PixelFormat.YUV10, matrix=None, hdr_metadata=None, narrow_range=True) -> bool`**
Display a static frame continuously.
- `frame_data`: NumPy array with image data:
  - RGB: shape (height, width, 3), dtype uint8/uint16/float32
  - BGRA: shape (height, width, 4), dtype uint8
- `display_mode`: Video resolution and frame rate
- `pixel_format`: Pixel format (default: YUV10, automatically uses BGRA for uint8 data)
- `matrix`: Optional R'G'B' to Y'CbCr conversion matrix (`Matrix.Rec709` or `Matrix.Rec2020`). Only used with YUV10 format. Default: Rec709
- `hdr_metadata`: Optional HDR metadata dict with keys:
  - `'eotf'`: Eotf enum (SDR, PQ, or HLG)
  - `'custom'`: Optional HdrMetadataCustom object for custom metadata values
- `narrow_range`: For float input with RGB10 output only, whether to use narrow range (64-940) or full range (0-1023). Default: True (narrow range). Note: Does not apply to YUV10 (always narrow range) or RGB12 (always full range). uint16 inputs are bit-shifted and ignore this parameter.
- Returns: True if successful

**`display_solid_color(color, display_mode) -> bool`**
Display a solid color.
- `color`: R'G'B' tuple (r, g, b) with values 0-255 or 0.0-1.0
- `display_mode`: Video resolution and frame rate
- Returns: True if successful

**`update_frame(frame_data) -> bool`**
Update currently displayed frame with new data.
- `frame_data`: New frame data as NumPy array
- Returns: True if successful

**`get_display_mode_info(display_mode) -> dict`**
Get information about a display mode.
- Returns: Dictionary with 'width', 'height', 'framerate'

**`get_current_output_info() -> dict`**
Get information about the current output configuration.
- Returns: Dictionary with 'display_mode_name', 'pixel_format_name', 'width', 'height', 'framerate', 'rgb444_mode_enabled'

**`stop(send_black_frame=False) -> bool`**
Stop video output.
- `send_black_frame`: If True, sends a black frame before stopping to avoid flickering or frozen last frame
- Returns: True if successful

**`cleanup(send_black_frame=False)`**
Cleanup resources and stop output.
- `send_black_frame`: If True, sends a black frame before stopping

**Context Manager Support:**
```python
with BlackmagicOutput() as output:
    output.initialize()
    # ... use output ...
# Automatic cleanup
```

#### Utility Functions

**`create_test_pattern(width, height, pattern='gradient', grad_start=0.0, grad_end=1.0) -> np.ndarray`**
Create test patterns for display testing and calibration.
- `width`: Frame width in pixels
- `height`: Frame height in pixels
- `pattern`: Pattern type - `'gradient'`, `'bars'`, or `'checkerboard'`
- `grad_start`: Float starting value for gradient pattern (default: 0.0, use <0.0 for sub-black)
- `grad_end`: Float ending value for gradient pattern (default: 1.0, use >1.0 for super-white)
- Returns: R'G'B' array (H×W×3), dtype float32

### Low-Level API: DeckLinkOutput Class

Direct C++ API for advanced features including HDR and timecode.

#### Methods

**`initialize(device_index=0) -> bool`**
Initialize the specified DeckLink device.

**`get_device_list() -> List[str]`**
Get list of available DeckLink devices.

**`get_video_settings(display_mode) -> VideoSettings`**
Get video settings object for a display mode.

**`setup_output(settings: VideoSettings) -> bool`**
Setup output with detailed settings.

**`set_frame_data(data: np.ndarray) -> bool`**
Set frame data from NumPy array (must be in correct format).

**`start_output() -> bool`**
Start scheduled video output.

**`stop_output(send_black_frame=False) -> bool`**
Stop video output.
- `send_black_frame`: If True, sends a black frame before stopping to avoid flickering or frozen last frame

**`cleanup()`**
Cleanup all resources.

**`set_hdr_metadata(colorimetry: Gamut, eotf: Eotf)`**
Set HDR metadata with default values. Must be called before `setup_output()`.

**`set_hdr_metadata_custom(colorimetry: Gamut, eotf: Eotf, custom: HdrMetadataCustom)`**
Set HDR metadata with custom values. Must be called before `setup_output()`.

**`set_timecode(tc: Timecode)`**
Set timecode value (enables timecode output). Must be called before `setup_output()`.

**`get_timecode() -> Timecode`**
Get current timecode value.

### Data Structures

**`VideoSettings`**
```python
class VideoSettings:
    mode: DisplayMode      # Video mode (resolution/framerate)
    format: PixelFormat    # Pixel format
    width: int             # Frame width in pixels
    height: int            # Frame height in pixels
    framerate: float       # Frame rate (e.g., 25.0, 29.97, 60.0)
    colorimetry: Gamut     # Color space (Rec709/Rec2020)
    eotf: Eotf             # Transfer function (SDR/PQ/HLG)
```

**`HdrMetadataCustom`**
```python
class HdrMetadataCustom:
    # Display primaries (xy chromaticity coordinates)
    display_primaries_red_x: float
    display_primaries_red_y: float
    display_primaries_green_x: float
    display_primaries_green_y: float
    display_primaries_blue_x: float
    display_primaries_blue_y: float
    white_point_x: float
    white_point_y: float

    # Luminance values (nits)
    max_mastering_luminance: float
    min_mastering_luminance: float
    max_content_light_level: float
    max_frame_average_light_level: float
```

**`Timecode`**
```python
class Timecode:
    hours: int         # 0-23
    minutes: int       # 0-59
    seconds: int       # 0-59
    frames: int        # 0-(framerate-1)
    drop_frame: bool   # True for drop-frame timecode
```

### Utility Functions

**`rgb_to_bgra(rgb_array, width, height) -> np.ndarray`**
Convert RGB to BGRA format.
- `rgb_array`: NumPy array (H×W×3), dtype uint8
- Returns: BGRA array (H×W×4), dtype uint8

**`rgb_uint16_to_yuv10(rgb_array, width, height, matrix=Matrix.Rec709) -> np.ndarray`**
Convert R'G'B' uint16 to 10-bit Y'CbCr v210 format.
- `rgb_array`: NumPy array (H×W×3), dtype uint16 (0-65535 range)
- `matrix`: R'G'B' to Y'CbCr conversion matrix (Matrix.Rec709 or Matrix.Rec2020)
- Returns: Packed v210 array

**`rgb_float_to_yuv10(rgb_array, width, height, matrix=Matrix.Rec709) -> np.ndarray`**
Convert R'G'B' float to 10-bit Y'CbCr v210 format.
- `rgb_array`: NumPy array (H×W×3), dtype float32 (0.0-1.0 range)
- `matrix`: R'G'B' to Y'CbCr conversion matrix (Matrix.Rec709 or Matrix.Rec2020)
- Returns: Packed v210 array (always video range: Y: 64-940, UV: 64-960)

**`rgb_uint16_to_rgb10(rgb_array, width, height) -> np.ndarray`**
Convert R'G'B' uint16 to 10-bit R'G'B' (bmdFormat10BitRGBXLE) format.
- `rgb_array`: NumPy array (H×W×3), dtype uint16 (0-65535 range)
- Returns: Packed 10-bit R'G'B' array (bit-shifted from 16-bit to 10-bit)

**`rgb_float_to_rgb10(rgb_array, width, height, narrow_range=True) -> np.ndarray`**
Convert R'G'B' float to 10-bit R'G'B' (bmdFormat10BitRGBXLE) format.
- `rgb_array`: NumPy array (H×W×3), dtype float32 (0.0-1.0 range)
- `narrow_range`: If True, maps 0.0-1.0 to 64-940 (narrow range). If False, maps 0.0-1.0 to 0-1023 (full range). Default: True
- Returns: Packed 10-bit R'G'B' array

**`create_solid_color_frame(width, height, color) -> np.ndarray`**
Create a solid color frame in BGRA format.
- `color`: R'G'B' tuple (r, g, b) with values 0-255
- Returns: BGRA array (H×W×4), dtype uint8

### Enums

**`DisplayMode`**

The library supports all display modes available on your DeckLink device. Display mode settings (resolution, framerate) are queried dynamically from the hardware. Common examples include:
- `HD1080p25`: 1920×1080 @ 25fps
- `HD1080p30`: 1920×1080 @ 30fps
- `HD1080p50`: 1920×1080 @ 50fps
- `HD1080p60`: 1920×1080 @ 60fps
- `HD720p50`: 1280×720 @ 50fps
- `HD720p60`: 1280×720 @ 60fps

Additional modes are available including SD (NTSC, PAL), 2K, 4K, 8K, and PC display modes. The complete list of DisplayMode values can be found in `src/blackmagic_output/blackmagic_output.py`.

**Querying Available Display Modes:**

To determine which display modes your specific DeckLink device supports, use the `get_display_mode_info()` method to test each mode:

```python
from blackmagic_output import BlackmagicOutput, DisplayMode

with BlackmagicOutput() as output:
    output.initialize()

    # Test a specific display mode
    try:
        info = output.get_display_mode_info(DisplayMode.Mode4K2160p25)
        print(f"4K 25p: {info['width']}x{info['height']} @ {info['framerate']}fps")
    except Exception as e:
        print(f"Mode not supported: {e}")

    # Or iterate through modes you're interested in
    test_modes = [
        DisplayMode.HD1080p25,
        DisplayMode.HD1080p50,
        DisplayMode.Mode4K2160p25,
        DisplayMode.Mode4K2160p50
    ]

    for mode in test_modes:
        try:
            info = output.get_display_mode_info(mode)
            print(f"{mode.name}: {info['width']}x{info['height']} @ {info['framerate']}fps")
        except:
            print(f"{mode.name}: Not supported")
```

**`PixelFormat`**
- `BGRA`: 8-bit BGRA (automatically used for uint8 data)
- `YUV`: 8-bit Y'CbCr 4:2:2
- `YUV10`: 10-bit Y'CbCr 4:2:2 (v210) - default for uint16/float data, provides high-quality output
  - Always uses narrow range: Y: 64-940, UV: 64-960
- `RGB10`: 10-bit R'G'B' (bmdFormat10BitRGBXLE) - native R'G'B' output without Y'CbCr conversion
  - uint16 input: Bit-shifted from 16-bit to 10-bit (>> 6)
  - float input: Configurable range via `narrow_range` parameter
    - `narrow_range=True` (default): 0.0-1.0 maps to 64-940 (narrow range)
    - `narrow_range=False`: 0.0-1.0 maps to 0-1023 (full range)
- `RGB12`: 12-bit R'G'B' (bmdFormat12BitRGBLE) - native R'G'B' output with 12-bit precision
  - uint16 input: Bit-shifted from 16-bit to 12-bit (>> 4)
  - float input: Full range only - 0.0-1.0 maps to 0-4095

**`Matrix`** (High-level API)
- `Rec709`: ITU-R BT.709 R'G'B' to Y'CbCr conversion matrix (standard HD)
- `Rec2020`: ITU-R BT.2020 R'G'B' to Y'CbCr conversion matrix (wide color gamut for HDR)

**`Gamut`** (Low-level API, same values as Matrix)
- `Rec709`: ITU-R BT.709 colorimetry (standard HD)
- `Rec2020`: ITU-R BT.2020 colorimetry (wide color gamut for HDR)

**`Eotf`**
- `SDR`: Standard Dynamic Range (BT.1886 transfer function)
- `PQ`: Perceptual Quantizer (SMPTE ST 2084, HDR10)
- `HLG`: Hybrid Log-Gamma (HDR broadcast standard)

## Examples

### Example 1: Static Image Display

```python
import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode

# Create a gradient test pattern
height, width = 1080, 1920
frame = np.zeros((height, width, 3), dtype=np.uint8)

for y in range(height):
    for x in range(width):
        frame[y, x] = [
            int(255 * x / width),      # Red gradient
            int(255 * y / height),     # Green gradient
            128                        # Blue constant
        ]

# Display the frame
with BlackmagicOutput() as output:
    output.initialize()
    output.display_static_frame(frame, DisplayMode.HD1080p25)
    input("Press Enter to stop...")
```

### Example 2: Color Bars Test Pattern

```python
from blackmagic_output import BlackmagicOutput, DisplayMode, create_test_pattern

# Create color bars test pattern
frame = create_test_pattern(1920, 1080, 'bars')

with BlackmagicOutput() as output:
    output.initialize()
    output.display_static_frame(frame, DisplayMode.HD1080p25)
    input("Press Enter to stop...")
```

### Example 3: Dynamic Animation

```python
import numpy as np
import time
from blackmagic_output import BlackmagicOutput, DisplayMode

with BlackmagicOutput() as output:
    output.initialize()
    
    # Start with black frame
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    output.display_static_frame(frame, DisplayMode.HD1080p25)
    
    # Animate
    for i in range(100):
        # Create moving pattern
        frame.fill(0)
        offset = i * 10
        frame[:, offset:offset+100] = [255, 255, 255]  # White bar
        
        output.update_frame(frame)
        time.sleep(1/25)  # 25 fps
```

### Example 4: Load Image from File

```python
import imageio.v3 as iio
import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode

# Load image (preserves bit depth for 16-bit TIFFs, etc.)
# Note: Use TIFF for reliable 16-bit support (PNGs may convert to 8-bit)
frame = iio.imread('your_image.tif')

# Resize if needed
if frame.shape[0] != 1080 or frame.shape[1] != 1920:
    from PIL import Image
    img = Image.fromarray(frame)
    img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
    frame = np.array(img)

# Remove alpha channel if present
if frame.shape[2] == 4:
    frame = frame[:, :, :3]

# Display image (format auto-detected from dtype)
with BlackmagicOutput() as output:
    output.initialize()
    output.display_static_frame(frame, DisplayMode.HD1080p25)
    input("Press Enter to stop...")
```

### Example 5: 10-bit Y'CbCr Output with Float Data

```python
import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode

# Create float R'G'B' image (0.0-1.0 range)
# This could be from color grading, rendering, or HDR processing
frame = np.zeros((1080, 1920, 3), dtype=np.float32)

# Example: gradient in float space
for y in range(1080):
    for x in range(1920):
        frame[y, x] = [
            x / 1920,           # Red gradient
            y / 1080,           # Green gradient
            0.5                 # Blue constant
        ]

# Output as 10-bit Y'CbCr (automatically selected for float data)
with BlackmagicOutput() as output:
    output.initialize()
    output.display_static_frame(frame, DisplayMode.HD1080p25)
    input("Press Enter to stop...")
```

### Example 6: 10-bit Y'CbCr with uint16 Data

```python
import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode

# Create uint16 R'G'B' image (0-65535 range)
# Useful for 10-bit/12-bit/16-bit image processing pipelines
frame = np.zeros((1080, 1920, 3), dtype=np.uint16)

# Full range gradient
for x in range(1920):
    frame[:, x, 0] = int(x / 1920 * 65535)  # Red gradient

# Output as 10-bit Y'CbCr (automatically selected for uint16 data)
with BlackmagicOutput() as output:
    output.initialize()
    output.display_static_frame(frame, DisplayMode.HD1080p25)
    input("Press Enter to stop...")
```

### Example 6a: 10-bit R'G'B' with uint16 Data

```python
import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode, PixelFormat

# Create uint16 R'G'B' image (0-65535 range)
frame = np.zeros((1080, 1920, 3), dtype=np.uint16)

# Full range gradient
for x in range(1920):
    frame[:, x, 0] = int(x / 1920 * 65535)  # Red gradient

# Output as 10-bit R'G'B' (bit-shifted from 16-bit to 10-bit)
with BlackmagicOutput() as output:
    output.initialize()
    output.display_static_frame(frame, DisplayMode.HD1080p25, PixelFormat.RGB10)
    input("Press Enter to stop...")
```

### Example 6b: 10-bit R'G'B' with Float Data (Narrow Range)

```python
import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode, PixelFormat

# Create float R'G'B' image (0.0-1.0 range)
frame = np.zeros((1080, 1920, 3), dtype=np.float32)

# Gradient
for x in range(1920):
    frame[:, x, 0] = x / 1920  # Red gradient

# Output as 10-bit R'G'B' with narrow range (0.0-1.0 maps to 64-940)
with BlackmagicOutput() as output:
    output.initialize()
    output.display_static_frame(
        frame,
        DisplayMode.HD1080p25,
        PixelFormat.RGB10,
        narrow_range=True  # Default: narrow range
    )
    input("Press Enter to stop...")
```

### Example 6c: 10-bit R'G'B' with Float Data (Full Range)

```python
import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode, PixelFormat

# Create float R'G'B' image (0.0-1.0 range)
frame = np.zeros((1080, 1920, 3), dtype=np.float32)

# Gradient
for x in range(1920):
    frame[:, x, 0] = x / 1920  # Red gradient

# Output as 10-bit R'G'B' with full range (0.0-1.0 maps to 0-1023)
with BlackmagicOutput() as output:
    output.initialize()
    output.display_static_frame(
        frame,
        DisplayMode.HD1080p25,
        PixelFormat.RGB10,
        narrow_range=False  # Full range
    )
    input("Press Enter to stop...")
```

### Example 7: HDR Output with Rec.2020 and HLG (Simplified API)

```python
import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode, Matrix, Eotf

# Create HDR content in normalised float (0.0-1.0 range)
frame = np.zeros((1080, 1920, 3), dtype=np.float32)

# Example: HDR gradient with extended range
for y in range(1080):
    for x in range(1920):
        frame[y, x] = [
            x / 1920,           # Red gradient
            y / 1080,           # Green gradient
            0.5                 # Blue constant
        ]

# Configure for HLG HDR output using the simplified API
with BlackmagicOutput() as output:
    output.initialize()

    # Single call with matrix and HDR metadata
    # YUV10 automatically selected for float data
    output.display_static_frame(
        frame,
        DisplayMode.HD1080p25,
        matrix=Matrix.Rec2020,           # Use Rec.2020 matrix
        hdr_metadata={'eotf': Eotf.HLG}  # HLG with default metadata
    )

    input("Press Enter to stop...")
```

**Alternative: Low-level API for more control**

```python
import numpy as np
import decklink_output as dl

# Create HDR content
frame = np.zeros((1080, 1920, 3), dtype=np.float32)
# ... fill frame ...

# Configure for HLG HDR output using low-level API
output = dl.DeckLinkOutput()
output.initialize()

# Set HDR metadata BEFORE setup_output()
output.set_hdr_metadata(dl.Gamut.Rec2020, dl.Eotf.HLG)

# Setup output
settings = output.get_video_settings(dl.DisplayMode.HD1080p25)
settings.format = dl.PixelFormat.YUV10
output.setup_output(settings)

# Convert R'G'B' to Y'CbCr using Rec.2020 matrix
yuv_data = dl.rgb_float_to_yuv10(frame, 1920, 1080, dl.Matrix.Rec2020)
output.set_frame_data(yuv_data)

output.start_output()
input("Press Enter to stop...")
output.stop_output()
output.cleanup()
```

### Example 8: HDR10 (PQ) Output (Simplified API)

```python
import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode, Matrix, Eotf

# Create HDR10 content with PQ transfer function applied
frame = np.zeros((1080, 1920, 3), dtype=np.float32)

# Fill with PQ-encoded HDR content
# A library such as Colour Science for Python (colour-science.org) is needed for PQ encoding
# frame = colour.eotf(linear_rgb_data, 'ST 2084')

# Configure for HDR10 (PQ) output using the simplified API
with BlackmagicOutput() as output:
    output.initialize()

    # Single call with Rec.2020 matrix and PQ metadata
    # YUV10 automatically selected for float data
    output.display_static_frame(
        frame,
        DisplayMode.HD1080p25,
        matrix=Matrix.Rec2020,
        hdr_metadata={'eotf': Eotf.PQ}
    )

    input("Press Enter to stop...")
```

**Alternative: Low-level API**

```python
import numpy as np
import decklink_output as dl

# Create HDR10 content
frame = np.zeros((1080, 1920, 3), dtype=np.float32)
# ... fill frame ...

# Configure for HDR10 (PQ) output
output = dl.DeckLinkOutput()
output.initialize()

# IMPORTANT: Set HDR metadata BEFORE setup_output()
# This embeds HDR metadata (including Rec.2020 primaries, EOTF, mastering display info) in frames
output.set_hdr_metadata(dl.Gamut.Rec2020, dl.Eotf.PQ)

# Setup output settings
settings = output.get_video_settings(dl.DisplayMode.HD1080p25)
settings.format = dl.PixelFormat.YUV10
output.setup_output(settings)

# Convert to Y'CbCr with Rec.2020 matrix
yuv_data = dl.rgb_float_to_yuv10(frame, 1920, 1080, dl.Gamut.Rec2020)
output.set_frame_data(yuv_data)

output.start_output()
input("Press Enter to stop...")
output.stop_output()
output.cleanup()
```

## HDR Metadata

HDR metadata is embedded into each video frame using the DeckLink SDK's `IDeckLinkVideoFrameMetadataExtensions` interface. When you call `set_hdr_metadata()`, the library automatically wraps each output frame with the specified metadata.

### Metadata Includes:

- **Display Primaries**: Automatically set to match the matrix parameter (unless explicitly specified via custom metadata)
  - Matrix.Rec709 → Rec.709 primaries (x,y): R(0.64, 0.33), G(0.30, 0.60), B(0.15, 0.06)
  - Matrix.Rec2020 → Rec.2020 primaries (x,y): R(0.708, 0.292), G(0.170, 0.797), B(0.131, 0.046)
- **White Point**: D65 (0.3127, 0.3290) for all matrices (unless explicitly specified)
- **EOTF**: Electro-Optical Transfer Function (SDR/Rec.709, PQ/SMPTE ST 2084, or HLG)
- **Mastering Display Info**: Default values for max/min luminance
- **Content Light Levels**: Max content light level and max frame average

### Default Metadata Values:

**When using Matrix.Rec709:**
```
Display Primaries: Rec.709 (ITU-R BT.709)
  Red:   (0.64, 0.33)
  Green: (0.30, 0.60)
  Blue:  (0.15, 0.06)
White Point: D65 (0.3127, 0.3290)
```

**When using Matrix.Rec2020:**
```
Display Primaries: Rec.2020 (ITU-R BT.2020)
  Red:   (0.708, 0.292)
  Green: (0.170, 0.797)
  Blue:  (0.131, 0.046)
White Point: D65 (0.3127, 0.3290)
```

**Luminance values by EOTF:**
```python
# SDR (Eotf.SDR)
Max Mastering Luminance: 100 nits
Min Mastering Luminance: 0.0001 nits
Max Content Light Level: 100 nits
Max Frame Average Light Level: 50 nits

# HLG (Eotf.HLG)
Max Mastering Luminance: 1000 nits
Min Mastering Luminance: 0.0001 nits
Max Content Light Level: 1000 nits
Max Frame Average Light Level: 50 nits

# PQ (Eotf.PQ)
Max Mastering Luminance: 1000 nits
Min Mastering Luminance: 0.0001 nits
Max Content Light Level: 1000 nits
Max Frame Average Light Level: 50 nits
```

### Customizing HDR Metadata Values:

**High-level API:**

```python
from blackmagic_output import BlackmagicOutput, DisplayMode, PixelFormat, Matrix, Eotf
import decklink_output as dl

# Create custom metadata
custom = dl.HdrMetadataCustom()
custom.display_primaries_red_x = 0.708
custom.display_primaries_red_y = 0.292
# ... set other values ...
custom.max_mastering_luminance = 1000.0
custom.min_mastering_luminance = 0.0001

# Use in simplified API
with BlackmagicOutput() as output:
    output.initialize()
    output.display_static_frame(
        frame,
        DisplayMode.HD1080p25,
        pixel_format=PixelFormat.YUV10,
        matrix=Matrix.Rec2020,
        hdr_metadata={'eotf': Eotf.PQ, 'custom': custom}
    )
    input("Press Enter to stop...")
```

**Low-level API:**

For precise control over HDR metadata with the low-level API, use `set_hdr_metadata_custom()`:

```python
import decklink_output as dl

# Create custom metadata for specific mastering display
custom = dl.HdrMetadataCustom()

# Display primaries (chromaticity coordinates)
custom.display_primaries_red_x = 0.708
custom.display_primaries_red_y = 0.292
custom.display_primaries_green_x = 0.170
custom.display_primaries_green_y = 0.797
custom.display_primaries_blue_x = 0.131
custom.display_primaries_blue_y = 0.046
custom.white_point_x = 0.3127
custom.white_point_y = 0.3290

# Mastering display luminance
custom.max_mastering_luminance = 4000.0      # 4000 nits peak (e.g., for HDR10+ content)
custom.min_mastering_luminance = 0.0005      # 0.0005 nits black level

# Content light levels
custom.max_content_light_level = 2000.0     # 2000 nits max content (MaxCLL)
custom.max_frame_average_light_level = 400.0 # 400 nits average (MaxFALL)

output = dl.DeckLinkOutput()
output.initialize()
output.set_hdr_metadata_custom(dl.Gamut.Rec2020, dl.Eotf.PQ, custom)
```

### Available HDR Metadata Fields:

All 14 CEA-861.3/ITU-R BT.2100 HDR static metadata fields are supported:

**Display Primaries (xy chromaticity coordinates):**
- `display_primaries_red_x`, `display_primaries_red_y`
- `display_primaries_green_x`, `display_primaries_green_y`
- `display_primaries_blue_x`, `display_primaries_blue_y`
- `white_point_x`, `white_point_y`

**Mastering Display Luminance:**
- `max_mastering_luminance` (nits) - Peak luminance of mastering display
- `min_mastering_luminance` (nits) - Minimum luminance of mastering display

**Content Light Levels:**
- `max_content_light_level` (nits) - Maximum luminance of any pixel (MaxCLL)
- `max_frame_average_light_level` (nits) - Maximum average luminance of any frame (MaxFALL)

### Important Notes:

1. **Simplified API**: With `display_static_frame()`, HDR metadata and matrix are set in a single call
2. **Low-level API call order**: When using the low-level API, `set_hdr_metadata()` must be called before `setup_output()`
3. **Frame-level metadata**: Metadata is embedded in every video frame, not set globally
4. **Matrix consistency**: When using the simplified API, the same `matrix` parameter is used for both metadata and R'G'B' →Y'CbCr conversion. With the low-level API, ensure consistency between `set_hdr_metadata()` and conversion functions.
5. **Transfer function**: The library only sets the metadata - you must apply the actual transfer function (PQ/HLG curve) to your RGB data before conversion
6. **All 14 metadata fields supported**: The library implements all CEA-861.3/ITU-R BT.2100 HDR metadata fields including display primaries, white point, mastering display luminance, and content light levels

## RP188 Timecode Support

The library supports embedding RP188 timecode in the output video signal. Timecode is automatically incremented each frame and embedded in both VITC1 and LTC formats.

### Basic Timecode Usage

```python
import decklink_output as dl
from datetime import datetime

output = dl.DeckLinkOutput()
output.initialize()

# Create timecode from system clock
now = datetime.now()
tc = dl.Timecode()
tc.hours = now.hour
tc.minutes = now.minute
tc.seconds = now.second
tc.frames = 0
tc.drop_frame = False

# IMPORTANT: Set timecode BEFORE setup_output()
output.set_timecode(tc)

# Setup and start output
settings = output.get_video_settings(dl.DisplayMode.HD1080p25)
settings.format = dl.PixelFormat.YUV10
output.setup_output(settings)

# ... set frame data and start output ...
```

### Frame-Accurate Time-of-Day Timecode

For frame-accurate synchronization to the system clock:

```python
import decklink_output as dl
from datetime import datetime

output = dl.DeckLinkOutput()
output.initialize()

settings = output.get_video_settings(dl.DisplayMode.HD1080p25)
settings.format = dl.PixelFormat.YUV10

# Calculate frame number from microseconds
now = datetime.now()
frame_number = int((now.microsecond / 1000000.0) * settings.framerate)

tc = dl.Timecode()
tc.hours = now.hour
tc.minutes = now.minute
tc.seconds = now.second
tc.frames = frame_number
tc.drop_frame = False

output.set_timecode(tc)
output.setup_output(settings)

# ... set frame data ...
output.start_output()

# Jam sync for better accuracy (optional)
time.sleep(0.1)  # Let output stabilize
now = datetime.now()
frame_number = int((now.microsecond / 1000000.0) * settings.framerate)
tc.hours = now.hour
tc.minutes = now.minute
tc.seconds = now.second
tc.frames = frame_number
output.set_timecode(tc)  # Re-sync while running
```

### Timecode Features

- **Auto-increment**: Timecode automatically increments each frame based on the video framerate
- **Drop-frame support**: Properly handles 29.97fps and 59.94fps drop-frame timecode
- **Multiple formats**: Embeds timecode in both RP188 VITC1 and RP188 LTC formats
- **Runtime updates**: Timecode can be updated while output is running for jam sync
- **Reading timecode**: Use `get_timecode()` to read the current timecode value

### Timecode Structure

```python
class Timecode:
    hours: int        # 0-23
    minutes: int      # 0-59
    seconds: int      # 0-59
    frames: int       # 0-(framerate-1)
    drop_frame: bool  # True for drop-frame timecode
```

### Drop-Frame Timecode

For 29.97fps and 59.94fps video:

```python
tc = dl.Timecode()
tc.hours = 10
tc.minutes = 0
tc.seconds = 0
tc.frames = 0
tc.drop_frame = True  # Enable drop-frame

output.set_timecode(tc)
```

The library automatically handles drop-frame rules:
- Skips frames 0 and 1 at the start of each minute (except every 10th minute)
- For 59.94fps, skips frames 0-3 instead of 0-1

### Complete Example: Color Bars with Time-of-Day Timecode

See `timecode_test.py` for a complete working example that outputs SMPTE color bars with frame-accurate time-of-day timecode and jam sync.

## Troubleshooting

### Common Issues

**"DeckLink output module not found"**
- Build the C++ extension: `python setup.py build_ext --inplace`
- Check that pybind11 is installed: `pip install pybind11`

**"Could not create DeckLink iterator"**
- Install Blackmagic Desktop Video software
- Ensure DeckLink device is connected and recognized by the system
- Check device drivers are properly installed

**"Could not find DeckLink device"**
- Verify device is connected and powered
- Check device appears in Blackmagic software (Media Express, etc.)
- Try different device index: `output.initialize(device_index=1)`

**Build errors about missing headers**
- Verify DeckLink SDK is installed correctly
- Update SDK paths in `setup.py` if installed in non-standard location
- On Linux, ensure headers are in system include path

**Permission errors (Linux)**
- Add user to appropriate groups: `sudo usermod -a -G video $USER`
- Log out and back in for group changes to take effect

**HDR output not displaying correctly**
- Verify your monitor/display supports the selected transfer function (PQ or HLG)
- **Simplified API**: Specify both `matrix` and `hdr_metadata` in `display_static_frame()` - they're automatically set correctly
- **Low-level API**: Call `set_hdr_metadata()` BEFORE `setup_output()` - metadata is embedded in each frame
- Ensure frame data has appropriate transfer function applied before conversion
- For PQ: Apply SMPTE ST 2084 curve to linear RGB before conversion
- For HLG: Apply ITU-R BT.2100 HLG curve before conversion
- Ensure matrix consistency: same value in both metadata and R'G'B' →Y'CbCr conversion

### Testing Your Installation

Run the example script to test your installation:

```bash
python example_usage.py
```

This will show available devices and let you test various output modes.

## Platform-Specific Notes

### Windows
- Requires Visual Studio Build Tools or Visual Studio with C++ support
- DeckLink SDK typically installs to Program Files

### macOS  
- Requires Xcode Command Line Tools
- May need to codesign the built extension for some versions

### Linux
- Requires build-essential package
- May need to configure udev rules for device access
- Some distributions require additional video group membership

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

### Blackmagic DeckLink SDK License

This repository includes header files from the Blackmagic DeckLink SDK v14.1. These header files are redistributable under the terms of the Blackmagic DeckLink SDK End User License Agreement (Section 0.1), which specifically exempts the Include folder headers from the more restrictive licensing terms that apply to other parts of the SDK.

**Important notes about the SDK headers:**
- The header files in `decklink_sdk/{Mac,Win,Linux}/include/` directories are from the Blackmagic DeckLink SDK
- These headers are required only for **building** the library from source
- **Runtime usage requires** the Blackmagic Desktop Video software to be installed separately
- The SDK headers are provided under Blackmagic Design's EULA - see `Blackmagic Design EULA.pdf` for full terms
- Download the complete SDK and Desktop Video software from: https://www.blackmagicdesign.com/developer

The Blackmagic DeckLink SDK is © Blackmagic Design Pty. Ltd. All rights reserved.

## Support

- Check the [Issues](https://github.com/nick-shaw/blackmagic-output/issues) page for known problems
- Review Blackmagic's official DeckLink SDK documentation
- Ensure your DeckLink device is supported by the SDK version

## Acknowledgments

- Blackmagic Design for the DeckLink SDK
- pybind11 project for excellent C++/Python bindings
- Contributors and testers