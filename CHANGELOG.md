# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.15.0b0] - 2025-01-22

### Added
- Color patch support in `display_solid_color()` method
  - New `patch` parameter: tuple (center_x, center_y, width, height) with normalized coordinates (0.0-1.0)
  - New `background_color` parameter: R'G'B' tuple for background when using patches
  - Useful for testing, calibration, and creating custom test patterns
  - Background color defaults to black (0 or 64 depending on `input_narrow_range`)
- Comprehensive test suite for range conversions (24 tests covering all range combinations)
- RGB12 documentation sections in README (previously missing)

### Changed
- **BREAKING**: Replaced ambiguous `narrow_range` parameter with explicit `input_narrow_range` and `output_narrow_range` parameters
  - Affects high-level API methods: `display_static_frame()` and `display_solid_color()`
  - Affects low-level conversion functions: `rgb_uint16_to_yuv10()`, `rgb_float_to_yuv10()`, `rgb_uint16_to_rgb10()`, `rgb_float_to_rgb10()`, `rgb_uint16_to_rgb12()`, `rgb_float_to_rgb12()`
  - `input_narrow_range`: Controls interpretation of uint16 input values (narrow: 64-940 @10-bit, i.e., 4096-60160 @16-bit; full: 0-65535)
  - `output_narrow_range`: Controls output encoding (narrow or full range)
  - Float inputs always interpreted as full range (0.0-1.0), no `input_narrow_range` parameter
- **Improved**: YUV10 output now supports full range Y'CbCr (0-1023) via `output_narrow_range=False`
  - Previously only narrow range (64-940/64-960) was supported
- **Optimized**: uint16 RGB conversions use efficient bit-shift when input and output ranges match, float conversion when they differ

### Fixed
- Removed manual range conversion code from high-level API that prevented full range YUV10 output

### Notes
- Default behavior maintained for backward compatibility:
  - `input_narrow_range=False` (full range 16-bit input)
  - `output_narrow_range=True` for YUV10 and RGB10 (narrow range output)
  - `output_narrow_range=False` for RGB12 (full range output)
- Applications using default parameters do not require code changes

## [0.14.0b0] - 2025-10-17

### Changed
- **Build system**: Switched from setuptools to CMake + scikit-build-core
  - Provides better cross-platform build support
  - Improved Linux compatibility
- **Directory structure**: Moved SDK headers from `decklink_sdk/` to `_vendor/decklink_sdk/`
- **C++ improvements**: Enhanced cross-platform support for Linux builds
  - Uses `memcmp` for `REFIID` comparison on Linux
  - Platform-specific string handling for device and display mode names

### Notes
- No breaking changes to the Python API
- Users building from source will need CMake (automatically handled by scikit-build-core)
- Installation command remains the same: `pip install -e .`

## [0.13.0-beta] - 2025-01-16

### Added
- New `pixel_reader` utility tool for reading and verifying SDI/HDMI output
  - Displays pixel values, metadata (EOTF, matrix), and video format information
  - Supports input selection for devices with multiple inputs
  - Useful for validating output from this library

### Removed
- **BREAKING**: Removed `is_display_mode_supported()` method from high-level API (`BlackmagicOutput`)
  - Use `is_pixel_format_supported(display_mode, pixel_format)` instead for more specific hardware capability checking
  - The removed method only checked if a display mode exists in the enum, not if hardware actually supports it
- **BREAKING**: Removed 8-bit YUV pixel format support
  - This needed to be supplied with packed 8-bit YUV data, which there were no helper functions to support
  - 8-bit data (uint8 dtype) uses BGRA format, which is converted by the SDK to 8-bit YCbCr output
  - Simplifies API by removing redundant pixel format

## [0.12.0-beta] - 2025-01-12

### Removed
- **BREAKING**: Removed `setup_output()` method from high-level API (`BlackmagicOutput`)
  - The method had no practical use case - `display_static_frame()` and `display_solid_color()` handle setup automatically
  - For applications that need to setup output without displaying (e.g., testing), use the low-level API (`decklink_output.DeckLinkOutput`)
  - Tests updated to use low-level API for setup-only operations

## [0.11.0-beta] - 2025-01-12

### Removed
- **BREAKING**: Removed timecode support entirely
  - Removed `set_timecode()` and `get_timecode()` methods from low-level API
  - Removed `Timecode` class
  - Removed `timecode_example.py` example
  - Rationale: Timecode requires real-time scheduled playback to be accurate. The current API only supports manual frame display (not scheduled playback), making timecode unreliable as it simply increments per `display_frame()` call rather than tracking actual elapsed time. Since the library is designed for manual frame display use cases (video routing, still frames, test patterns), timecode support is unnecessary complexity.

## [0.10.0-beta] - 2025-01-11

### Changed
- **BREAKING**: Replaced asynchronous scheduled playback with synchronous frame display
- **BREAKING**: Removed `start_output()` method from low-level API
- **BREAKING**: Timecode now increments per `display_frame()` call instead of automatically in the background
- Display mode switching is now instant with no delays or black screens
- Simplified internal implementation by removing ~200 lines of callback and scheduling code

### Added
- New `display_frame()` method for synchronous frame display in low-level API
- Support for instant display mode switching without stopping/restarting output

### Fixed
- Display mode switching now works correctly without black screens or delays
- Eliminated timing issues related to asynchronous hardware operations

### Notes
- For timecode to advance in real-time, applications must call `display_frame()` at the appropriate frame rate (e.g., 25 times per second for 25fps video)
- High-level `display_static_frame()` API remains unchanged and handles this automatically

## [0.9.0-beta] - 2025-01-10

### Added
- 12-bit RGB support
- 10-bit RGB output
- Hardware capability checking methods: `is_display_mode_supported()` and `is_pixel_format_supported()`

### Changed
- Renamed `video_range` parameter to `narrow_range` throughout the API

### Fixed
- HDR metadata now correctly omits luminance values for HLG (only sets for PQ)

## Earlier versions

See git history for changes prior to 0.9.0-beta.
