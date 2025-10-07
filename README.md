# Blackmagic DeckLink Python Output Library

A Python library for outputting video frames to Blackmagic DeckLink devices using the official DeckLink SDK. This library provides a simple interface for displaying static frames, solid colors, and dynamic content from NumPy arrays.

## Features

- **Static Frame Output**: Display static images from NumPy arrays
- **Solid Color Output**: Display solid colors for testing and calibration
- **Dynamic Updates**: Update displayed frames in real-time
- **Multiple Resolutions**: Support for HD and various display modes
- **10-bit YUV Output**: Professional 10-bit YUV 4:2:2 (v210) for high-quality output
- **HDR Support**: Rec.2020 colorimetry with PQ and HLG transfer functions
- **Flexible Color Spaces**: Rec.709 and Rec.2020 matrix support
- **RP188 Timecode**: Embedded VITC and LTC timecode with auto-increment
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Pythonic API**: Simple, intuitive Python interface
- **High Performance**: C++ backend with Python bindings

## Requirements

### System Requirements
- Python 3.7 or higher
- Blackmagic DeckLink device (DeckLink, UltraStudio, or Intensity series)
- Blackmagic Desktop Video software installed

### Software Dependencies
- NumPy >= 1.19.0
- pybind11 >= 2.6.0
- Blackmagic DeckLink SDK (free download from Blackmagic Design)

## Installation

### 1. Install DeckLink SDK

Download and install the DeckLink SDK from [Blackmagic Design Developer](https://www.blackmagicdesign.com/developer/):

**Windows:**
- Install to: `C:\\Program Files\\Blackmagic Design\\DeckLink SDK\\`

**macOS:**
- Install to: `/Applications/Blackmagic DeckLink SDK/`

**Linux:**
- Extract SDK and ensure headers are in `/usr/include/decklink/` or `/usr/local/include/decklink/`

### 2. Build the Library

```bash
# Clone or download the library files
git clone https://github.com/yourusername/blackmagic-output.git
cd blackmagic-output

# Install Python dependencies
pip install numpy pybind11

# Build the C++ extension
python setup.py build_ext --inplace

# Optional: Install in development mode
pip install -e .
```

### 3. Install Optional Dependencies

For examples and additional functionality:
```bash
pip install pillow opencv-python  # For image loading and processing
```

## Quick Start

```python
import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode

# Create a simple test image (1080p RGB)
frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
frame[:, :] = [255, 0, 0]  # Red frame

# Display the frame
with BlackmagicOutput() as output:
    # Initialize device (uses first available device)
    output.initialize()
    
    # Display static frame at 1080p25
    output.display_static_frame(frame, DisplayMode.HD1080p25)
    
    # Keep displaying (Ctrl+C to stop)
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

**`setup_output(display_mode, pixel_format=PixelFormat.BGRA) -> bool`**
Setup video output parameters.
- `display_mode`: Video resolution and frame rate
- `pixel_format`: Pixel format (default: BGRA)
- Returns: True if successful

**`display_static_frame(frame_data, display_mode, pixel_format=PixelFormat.BGRA) -> bool`**
Display a static frame continuously.
- `frame_data`: NumPy array with image data:
  - RGB: shape (height, width, 3), dtype uint8/uint16/float32
  - BGRA: shape (height, width, 4), dtype uint8
- `display_mode`: Video resolution and frame rate
- `pixel_format`: Pixel format (BGRA, YUV, or YUV10)
- Returns: True if successful

**`display_solid_color(color, display_mode) -> bool`**
Display a solid color.
- `color`: RGB tuple (r, g, b) with values 0-255
- `display_mode`: Video resolution and frame rate
- Returns: True if successful

**`update_frame(frame_data) -> bool`**
Update currently displayed frame with new data.
- `frame_data`: New frame data as NumPy array
- Returns: True if successful

**`get_display_mode_info(display_mode) -> dict`**
Get information about a display mode.
- Returns: Dictionary with 'width', 'height', 'framerate'

**`stop() -> bool`**
Stop video output.

**`cleanup()`**
Cleanup resources and stop output.

**Context Manager Support:**
```python
with BlackmagicOutput() as output:
    output.initialize()
    # ... use output ...
# Automatic cleanup
```

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

**`stop_output() -> bool`**
Stop video output.

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
    eotf: Eotf            # Transfer function (SDR/PQ/HLG)
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

**`rgb_uint16_to_yuv10(rgb_array, width, height, colorimetry=Gamut.Rec709) -> np.ndarray`**
Convert RGB uint16 to 10-bit YUV v210 format.
- `rgb_array`: NumPy array (H×W×3), dtype uint16 (0-65535 range)
- `colorimetry`: Color space matrix (Rec709 or Rec2020)
- Returns: Packed v210 array

**`rgb_float_to_yuv10(rgb_array, width, height, colorimetry=Gamut.Rec709) -> np.ndarray`**
Convert RGB float to 10-bit YUV v210 format.
- `rgb_array`: NumPy array (H×W×3), dtype float32 (0.0-1.0 range)
- `colorimetry`: Color space matrix (Rec709 or Rec2020)
- Returns: Packed v210 array

**`create_solid_color_frame(width, height, color) -> np.ndarray`**
Create a solid color frame in BGRA format.
- `color`: RGB tuple (r, g, b) with values 0-255
- Returns: BGRA array (H×W×4), dtype uint8

**`create_test_pattern(width, height, pattern='gradient') -> np.ndarray`**
Create test patterns (from `blackmagic_output` module).
- `pattern`: 'gradient', 'bars', or 'checkerboard'
- Returns: RGB array (H×W×3), dtype uint8

### Enums

**`DisplayMode`**
- `HD1080p25`: 1920×1080 @ 25fps
- `HD1080p30`: 1920×1080 @ 30fps  
- `HD1080p50`: 1920×1080 @ 50fps
- `HD1080p60`: 1920×1080 @ 60fps
- `HD720p50`: 1280×720 @ 50fps
- `HD720p60`: 1280×720 @ 60fps

**`PixelFormat`**
- `BGRA`: 8-bit BGRA (recommended for uint8 data)
- `YUV`: 8-bit YUV 4:2:2
- `YUV10`: 10-bit YUV 4:2:2 (v210) - recommended for high-quality output with float/uint16 data

**`Gamut`**
- `Rec709`: ITU-R BT.709 colorimetry (standard HD)
- `Rec2020`: ITU-R BT.2020 colorimetry (wide color gamut for HDR)

**`Eotf`**
- `SDR`: Standard Dynamic Range (Rec.709 transfer function)
- `PQ`: Perceptual Quantizer (SMPTE ST 2084, HDR10)
- `HLG`: Hybrid Log-Gamma (HDR broadcast standard)

### Utility Functions

**`create_test_pattern(width, height, pattern='gradient') -> np.ndarray`**
Create test patterns for display.
- `pattern`: 'gradient', 'bars', or 'checkerboard'
- Returns: RGB frame data

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
from PIL import Image
import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode

# Load and resize image
with Image.open('your_image.jpg') as img:
    img = img.convert('RGB').resize((1920, 1080))
    frame = np.array(img)

# Display image
with BlackmagicOutput() as output:
    output.initialize()
    output.display_static_frame(frame, DisplayMode.HD1080p25)
    input("Press Enter to stop...")
```

### Example 5: 10-bit YUV Output with Float Data

```python
import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode, PixelFormat

# Create float RGB image (0.0-1.0 range)
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

# Output as 10-bit YUV for maximum quality
with BlackmagicOutput() as output:
    output.initialize()
    output.display_static_frame(frame, DisplayMode.HD1080p25, PixelFormat.YUV10)
    input("Press Enter to stop...")
```

### Example 6: 10-bit YUV with uint16 Data

```python
import numpy as np
from blackmagic_output import BlackmagicOutput, DisplayMode, PixelFormat

# Create uint16 RGB image (0-65535 range)
# Useful for 10-bit/12-bit/16-bit image processing pipelines
frame = np.zeros((1080, 1920, 3), dtype=np.uint16)

# Full range gradient
for x in range(1920):
    frame[:, x, 0] = int(x / 1920 * 65535)  # Red gradient

# Output as 10-bit YUV
with BlackmagicOutput() as output:
    output.initialize()
    output.display_static_frame(frame, DisplayMode.HD1080p25, PixelFormat.YUV10)
    input("Press Enter to stop...")
```

### Example 7: HDR Output with Rec.2020 and HLG

```python
import numpy as np
import decklink_output as dl

# Create HDR content in linear RGB (0.0-1.0 range)
# This could be from HDR grading, rendering, or tone mapping
frame = np.zeros((1080, 1920, 3), dtype=np.float32)

# Example: HDR gradient with extended range
for y in range(1080):
    for x in range(1920):
        frame[y, x] = [
            x / 1920,           # Red gradient
            y / 1080,           # Green gradient
            0.5                 # Blue constant
        ]

# Configure for HLG HDR output
output = dl.DeckLinkOutput()
output.initialize()

# IMPORTANT: Set HDR metadata BEFORE setup_output()
# This embeds HDR metadata in every video frame
output.set_hdr_metadata(dl.Gamut.Rec2020, dl.Eotf.HLG)

# Setup output
settings = output.get_video_settings(dl.DisplayMode.HD1080p25)
settings.format = dl.PixelFormat.YUV10
output.setup_output(settings)

# Convert RGB to YUV using Rec.2020 matrix
yuv_data = dl.rgb_float_to_yuv10(frame, 1920, 1080, dl.Gamut.Rec2020)
output.set_frame_data(yuv_data)

output.start_output()
input("Press Enter to stop...")
output.stop_output()
output.cleanup()
```

### Example 8: HDR10 (PQ) Output

```python
import numpy as np
import decklink_output as dl

# Create HDR10 content with PQ transfer function applied
# Note: You need to apply PQ encoding to your linear/gamma RGB data first
frame = np.zeros((1080, 1920, 3), dtype=np.float32)

# Fill with PQ-encoded HDR content
# (Assume apply_pq_transfer() converts linear to PQ curve)
# frame = apply_pq_transfer(linear_rgb_data)

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

# Convert to YUV with Rec.2020 matrix
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

- **Colorspace**: Rec.709 or Rec.2020 primaries
- **EOTF**: Electro-Optical Transfer Function (SDR/Rec.709, PQ/SMPTE ST 2084, or HLG)
- **Mastering Display Info**: Default values for max/min luminance (1000 nits max, 0.0001 nits min)
- **Content Light Levels**: Max content light level (1000 nits), max frame average (50 nits)

### Default Metadata Values:

```python
# SDR defaults (when using Eotf.SDR)
- Primaries: Rec.709
- Max Mastering Luminance: 100 nits
- Min Mastering Luminance: 0.0001 nits

# HLG defaults (when using Eotf.HLG)
- Primaries: Rec.2020
- Max Mastering Luminance: 1000 nits
- Min Mastering Luminance: 0.0001 nits

# PQ defaults (when using Eotf.PQ)
- Primaries: Rec.2020
- Max Mastering Luminance: 1000 nits
- Min Mastering Luminance: 0.0001 nits
```

### Customizing HDR Metadata Values:

For precise control over HDR metadata, use `set_hdr_metadata_custom()`:

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

1. **Call order matters**: `set_hdr_metadata()` must be called before `setup_output()`
2. **Frame-level metadata**: Metadata is embedded in every video frame, not set globally
3. **Colorimetry consistency**: Use the same `Gamut` value in both `set_hdr_metadata()` and the RGB→YUV conversion functions
4. **Transfer function**: The library only sets the metadata - you must apply the actual transfer function (PQ/HLG curve) to your RGB data before conversion
5. **All 14 metadata fields supported**: The library implements all CEA-861.3/ITU-R BT.2100 HDR metadata fields including display primaries, white point, mastering display luminance, and content light levels

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
- **IMPORTANT**: Call `set_hdr_metadata()` BEFORE `setup_output()` - metadata is embedded in each frame
- Ensure frame data has appropriate transfer function applied before conversion
- For PQ: Apply SMPTE ST 2084 curve to linear RGB before conversion
- For HLG: Apply ITU-R BT.2100 HLG curve before conversion
- Use the matching colorimetry in both `set_hdr_metadata()` and `rgb_*_to_yuv10()` conversion functions

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

## Support

- Check the [Issues](https://github.com/yourusername/blackmagic-output/issues) page for known problems
- Review Blackmagic's official DeckLink SDK documentation
- Ensure your DeckLink device is supported by the SDK version

## Acknowledgments

- Blackmagic Design for the DeckLink SDK
- pybind11 project for excellent C++/Python bindings
- Contributors and testers