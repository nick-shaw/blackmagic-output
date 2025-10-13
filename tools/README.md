# Pixel Format Reader for Blackmagic DeckLink Devices

This tool reads the incoming signal on a Blackmagic DeckLink device and displays:
- The detected pixel format (including bit depth and color space)
- The code values at specified pixel coordinates
- Metadata (EOTF and matrix) when present

## Features

- **Automatic Format Detection**: Detects all supported YUV and RGB formats
- **Supported Formats**:
  - **YUV formats**: 8-bit YUV (2vuy), 10-bit YUV (v210), 10-bit YUVA (Ay10)
  - **RGB formats**:
    - 8-bit: ARGB, BGRA
    - 10-bit: R10l (little-endian - default), r210 (big-endian), R10b (big-endian)
    - 12-bit: R12L (little-endian - default), R12B (big-endian)
- **Accurate Pixel Extraction**: Properly unpacks pixel data for each format
- **Metadata Display**: Shows EOTF (SDR/PQ/HLG) and matrix (Rec.601/709/2020) when present
- **Real-time Display**: Continuously updates as frames arrive

## Building

### macOS
```bash
make
```

### Linux
```bash
make
```

### Windows (MinGW)
```bash
make
```

## Usage

```bash
./pixel_reader [options] [x] [y]
```

### Options

- `-d <index>`: Select DeckLink device by index (see `-l` for device list)
- `-l`: List all available DeckLink devices with their capabilities
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

# Show help
./pixel_reader -h
```

## Output

The tool displays:
1. **Format Detection**: When the input signal format changes, it shows:
   - Color space (YCbCr422, RGB444)
   - Bit depth (8-bit, 10-bit, 12-bit)
   - Pixel format name

2. **Pixel Values**: Continuously updated pixel values at the specified coordinates
   - For YUV: Shows Y'CbCr values
   - For RGB: Shows R'G'B' values

3. **Metadata** (when present):
   - Matrix: Rec.601, Rec.709, or Rec.2020
   - EOTF: SDR, PQ, or HLG

### Example Output

```
Input display mode: 1080p50
Input color space changed:
  Color space: RGB444
  Bit depth: 10-bit
  Pixel format: 10-bit RGBX LE (R10l)

R'G'B' (960, 540) = [940, 512, 64]
Matrix: Rec.709 | EOTF: SDR
```

## Technical Details

### Pixel Format Support

- **v210 (10-bit YUV)**: 6 pixels packed in 16 bytes, accurate extraction per pixel
- **2vuy (8-bit YUV)**: UYVY format, 2 pixels in 4 bytes
- **r210 (10-bit RGB)**: Big-endian RGB 10-bit, packed as 2:10:10:10
- **R10l/R10b (10-bit RGBX)**: Little/big-endian variants
- **R12B/R12L (12-bit RGB)**: Big/little-endian 12-bit RGB
- **BGRA/ARGB (8-bit)**: Standard 8-bit formats

### Limitations

- Requires a DeckLink device with input format detection support
- Coordinates must be within the input frame dimensions
- Does not support input selection (HDMI/SDI) - uses the active input on the selected device

## Platform Support

- macOS (tested)
- Linux (untested, but should work)
- Windows (untested, requires DeckLink SDK and appropriate build tools)

## Dependencies

- Blackmagic DeckLink SDK 14.1 (included in decklink_sdk directory)
- C++11 compatible compiler
- Platform-specific libraries (CoreFoundation on macOS, pthread/dl on Linux, ole32/oleaut32 on Windows)

## License

Based on Blackmagic Design DeckLink SDK samples. See LICENSE for details.
