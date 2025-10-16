# Pixel Reader for Blackmagic DeckLink Devices

This tool reads the incoming signal on a Blackmagic DeckLink device and displays:
- The detected pixel format (including bit depth and color space)
- The code values at specified pixel coordinates
- Metadata (EOTF and matrix) when present

## Features

- **Automatic Format Detection**: Detects all supported YUV and RGB formats
- **Supported Formats**:
  - 8-bit YUV (4:2:2)
  - 10-bit YUV (4:2:2)
  - 10-bit YUVA (4:4:4:4)
  - 8-bit RGB (4:4:4)
  - 10-bit RGB (4:4:4)
  - 12-bit RGB (4:4:4)
- **Metadata Display**: Shows EOTF (SDR/PQ/HLG) and matrix (Rec.601/709/2020) when present
- **Real-time Display**: Continuously updates as frames arrive

## Building

### Option 1: CMake (Recommended)
```bash
# Create build directory
mkdir build && cd build

# Configure and build
cmake ..
cmake --build .

# The executable will be in the tools directory
cd ..
```

### Option 2: Make (Legacy)
#### macOS
```bash
make
```

#### Linux
```bash
make
```

#### Windows (MinGW)
```bash
make
```

## Usage

```bash
./pixel_reader [options] [x] [y]
```

### Options

- `-d <index>`: Select DeckLink device by index (see `-l` for device list). Default: first device with input capability
- `-i <input>`: Select input connection (sdi, hdmi, optical, component, composite, svideo). Default: uses currently active input on the device
- `-l`: List all available DeckLink devices with their input capabilities and available inputs
- `-h`: Show help message

### Arguments

- `x`: X coordinate of pixel to read (default: 960)
- `y`: Y coordinate of pixel to read (default: 540)

### Examples

```bash
# List available devices
./pixel_reader -l

# Use first device with input capability (default), read pixel at (100, 100)
./pixel_reader 100 100

# Select device 1, use default position (960, 540)
./pixel_reader -d 1

# Select device 0, read pixel at position (100, 100)
./pixel_reader -d 0 100 100

# Use HDMI input
./pixel_reader -i hdmi

# Use device 0, SDI input, read pixel at (100, 200)
./pixel_reader -d 0 -i sdi 100 200

# Show help
./pixel_reader -h
```

## Output

The tool displays:
1. **Format Detection**: When the input signal is detected or changes, it shows:
   - Signal format (YCbCr422, RGB444)
   - Bit depth (8-bit, 10-bit, 12-bit)

2. **Pixel Values**: Continuously updated pixel values at the specified coordinates
   - For YUV: Shows Y'CbCr values
   - For RGB: Shows R'G'B' values

3. **Metadata** (when present):
   - Matrix: Rec.601, Rec.709, or Rec.2020
   - EOTF: SDR, PQ, or HLG

### Example Output

```
Input display mode: 1080p50
Input signal detected:
  Signal format: RGB444
  Bit depth: 10-bit

R'G'B' (960, 540) = [940, 512, 64]
Matrix: Rec.709 | EOTF: SDR
```

## Technical Details

### Buffer Format Implementation

The tool uses little-endian buffer formats by default for easier unpacking:
- **8-bit YUV**: 2vuy (UYVY) format
- **10-bit YUV**: v210 format
- **10-bit YUVA**: Ay10 format
- **8-bit RGB**: ARGB/BGRA formats
- **10-bit RGB**: R10l (little-endian RGBX) format
- **12-bit RGB**: R12L (little-endian) format

Note: The buffer format variants (little/big-endian, different packing) are SDK implementation details, not signal format differences.

### Limitations

- Requires a DeckLink device with input format detection support
- Coordinates must be within the input frame dimensions

## Platform Support

- macOS (tested)
- Linux (untested, but should work)
- Windows (untested, requires DeckLink SDK and appropriate build tools)

## Dependencies

- Blackmagic DeckLink SDK 14.1 (included in decklink_sdk directory)
- C++11 compatible compiler
- Platform-specific libraries (CoreFoundation on macOS, pthread/dl on Linux, ole32/oleaut32 on Windows)

## License

Based on Blackmagic Design DeckLink SDK samples. This tool uses the DeckLink SDK which is subject to the Blackmagic Design End User License Agreement (see `Blackmagic Design EULA.pdf` in the repository root). The tool code itself is available under the license in the repository LICENSE file.
