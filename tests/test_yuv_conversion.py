#!/usr/bin/env python3
"""Test YUV to RGB conversion functions"""

import decklink_output
import numpy as np
import matplotlib.pyplot as plt

print("Testing YUV to RGB conversion...")
print("=" * 60)

# Create input object
input_device = decklink_output.DeckLinkInput()

# Initialize
if not input_device.initialize(0):
    print("ERROR: Failed to initialize device")
    exit(1)

print("Device initialized successfully")

# Start capture
print("Starting capture...")
if not input_device.start_capture():
    print("ERROR: Failed to start capture")
    exit(1)

# Capture a frame
frame = decklink_output.CapturedFrame()
if input_device.capture_frame(frame, 10000):
    print(f"\nFrame captured:")
    print(f"  Format: {frame.format}")
    print(f"  Size: {frame.width}x{frame.height}")
    print(f"  Data size: {len(frame.data)} bytes")
    print(f"  Colorspace: {frame.colorspace}")

    # Test unpacking function
    if frame.format == decklink_output.PixelFormat.YUV10:
        print("\n--- Testing unpack_v210() ---")
        yuv_data = decklink_output.unpack_v210(np.array(frame.data, dtype=np.uint8), frame.width, frame.height)
        print(f"  Y shape: {yuv_data['y'].shape}, dtype: {yuv_data['y'].dtype}")
        print(f"  Cb shape: {yuv_data['cb'].shape}, dtype: {yuv_data['cb'].dtype}")
        print(f"  Cr shape: {yuv_data['cr'].shape}, dtype: {yuv_data['cr'].dtype}")
        print(f"  Y range: {yuv_data['y'].min()}-{yuv_data['y'].max()}")
        print(f"  Cb range: {yuv_data['cb'].min()}-{yuv_data['cb'].max()}")
        print(f"  Cr range: {yuv_data['cr'].min()}-{yuv_data['cr'].max()}")

        # Test combined uint16 conversion
        print("\n--- Testing yuv10_to_rgb_uint16() ---")
        rgb_uint16 = decklink_output.yuv10_to_rgb_uint16(
            np.array(frame.data, dtype=np.uint8),
            frame.width,
            frame.height,
            matrix=frame.colorspace,
            input_narrow_range=True,
            output_narrow_range=False
        )
        print(f"  RGB shape: {rgb_uint16.shape}, dtype: {rgb_uint16.dtype}")
        print(f"  R range: {rgb_uint16[:,:,0].min()}-{rgb_uint16[:,:,0].max()}")
        print(f"  G range: {rgb_uint16[:,:,1].min()}-{rgb_uint16[:,:,1].max()}")
        print(f"  B range: {rgb_uint16[:,:,2].min()}-{rgb_uint16[:,:,2].max()}")

        # Test combined float conversion
        print("\n--- Testing yuv10_to_rgb_float() ---")
        rgb_float = decklink_output.yuv10_to_rgb_float(
            np.array(frame.data, dtype=np.uint8),
            frame.width,
            frame.height,
            matrix=frame.colorspace,
            input_narrow_range=True
        )
        print(f"  RGB shape: {rgb_float.shape}, dtype: {rgb_float.dtype}")
        print(f"  R range: {rgb_float[:,:,0].min():.6f}-{rgb_float[:,:,0].max():.6f}")
        print(f"  G range: {rgb_float[:,:,1].min():.6f}-{rgb_float[:,:,1].max():.6f}")
        print(f"  B range: {rgb_float[:,:,2].min():.6f}-{rgb_float[:,:,2].max():.6f}")

        # Display the captured frame
        print("\n--- Displaying captured frame ---")
        plt.figure(figsize=(12, 8))
        plt.imshow(rgb_float)
        plt.title(f"Captured Frame ({frame.width}x{frame.height}, {frame.colorspace})")
        plt.axis('off')
        plt.tight_layout()
        plt.show()
        print("  Image displayed")

        print("\n✓ All conversion functions working!")
    else:
        print(f"\nSkipping YUV conversion tests - frame is {frame.format}, not YUV10")
else:
    print("ERROR: Failed to capture frame")

# Cleanup
input_device.stop_capture()
input_device.cleanup()

print("\nTest complete!")
