#!/usr/bin/env python3
"""
Test script for RP188 timecode support with color bars
"""

import numpy as np
import time
from datetime import datetime
import decklink_output

def create_color_bars(width, height):
    """Create SMPTE color bars pattern"""
    bars = np.zeros((height, width, 3), dtype=np.float32)

    bar_width = width // 7

    colors = [
        [0.75, 0.75, 0.75],  # White
        [0.75, 0.75, 0.00],  # Yellow
        [0.00, 0.75, 0.75],  # Cyan
        [0.00, 0.75, 0.00],  # Green
        [0.75, 0.00, 0.75],  # Magenta
        [0.75, 0.00, 0.00],  # Red
        [0.00, 0.00, 0.75],  # Blue
    ]

    for i, color in enumerate(colors):
        x_start = i * bar_width
        x_end = (i + 1) * bar_width if i < 6 else width
        bars[:, x_start:x_end] = color

    return bars

def main():
    display_mode = decklink_output.DisplayMode.HD1080p25

    output = decklink_output.DeckLinkOutput()

    if not output.initialize():
        print("Failed to initialize Blackmagic device")
        return

    settings = output.get_video_settings(display_mode)
    settings.format = decklink_output.PixelFormat.YUV10

    now = datetime.now()
    microseconds = now.microsecond
    frames_per_second = settings.framerate
    frame_number = int((microseconds / 1000000.0) * frames_per_second)

    tc = decklink_output.Timecode()
    tc.hours = now.hour
    tc.minutes = now.minute
    tc.seconds = now.second
    tc.frames = frame_number
    tc.drop_frame = False

    output.set_timecode(tc)

    if not output.setup_output(settings):
        print("Failed to setup output")
        return

    print(f"Output configured: {settings.width}x{settings.height} @ {settings.framerate}fps")
    print(f"Starting output with time-of-day timecode: {tc}")

    bars = create_color_bars(settings.width, settings.height)
    yuv_data = decklink_output.rgb_float_to_yuv10(bars, settings.width, settings.height)
    output.set_frame_data(yuv_data)

    # Display the first frame to start output
    if not output.display_frame():
        print("Failed to display frame")
        return

    print("Output running. Jam syncing timecode...")

    time.sleep(0.1)

    now = datetime.now()
    microseconds = now.microsecond
    frame_number = int((microseconds / 1000000.0) * frames_per_second)

    tc.hours = now.hour
    tc.minutes = now.minute
    tc.seconds = now.second
    tc.frames = frame_number

    output.set_timecode(tc)
    print(f"Jam synced to: {tc}")
    print("Press Ctrl+C to stop...")
    print()  # New line for the updating timecode display

    try:
        frame_time = 1.0 / frames_per_second
        while True:
            # Display frame to update timecode
            output.display_frame()
            current_tc = output.get_timecode()
            print(f"Current timecode: {current_tc}", end='\r')
            time.sleep(frame_time)
    except KeyboardInterrupt:
        print("\nStopping...")

    output.stop_output()
    output.cleanup()
    print("Done")

if __name__ == "__main__":
    main()
