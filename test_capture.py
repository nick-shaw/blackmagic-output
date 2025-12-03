#!/usr/bin/env python3
"""Simple test script for DeckLink input/capture"""

import decklink_output

print("Testing DeckLink Input...")
print("=" * 60)

# Create input object
input_device = decklink_output.DeckLinkInput()

# Initialize
if not input_device.initialize(0):
    print("ERROR: Failed to initialize device")
    exit(1)

print("Device initialized successfully")

# Get device list
devices = input_device.get_device_list()
print(f"Found {len(devices)} device(s):")
for i, dev in enumerate(devices):
    print(f"  [{i}] {dev}")

# Start capture with auto-detection
print("\nStarting capture with auto-detection...")
if not input_device.start_capture():
    print("ERROR: Failed to start capture")
    exit(1)

print("Capture started. Waiting for frames...")

# Try to capture a frame
frame = decklink_output.CapturedFrame()
if input_device.capture_frame(frame, 10000):  # 10 second timeout
    print(f"\nFrame captured successfully!")
    print(f"  Width: {frame.width}")
    print(f"  Height: {frame.height}")
    print(f"  Format: {frame.format}")
    print(f"  Mode: {frame.mode}")
    print(f"  Data size: {len(frame.data)} bytes")
    print(f"  Valid: {frame.valid}")

    # Get detected format
    detected = input_device.get_detected_format()
    print(f"\nDetected format:")
    print(f"  Mode: {detected.mode}")
    print(f"  Resolution: {detected.width}x{detected.height}")
    print(f"  Framerate: {detected.framerate} fps")

    # Get detected pixel format
    pixel_format = input_device.get_detected_pixel_format()
    print(f"  Detected pixel format: {pixel_format}")
else:
    print("ERROR: Failed to capture frame (timeout or no signal)")

# Cleanup
input_device.stop_capture()
input_device.cleanup()

print("\nTest complete!")
