"""
Live preview with high-quality capture capability.

Uses 8-bit BGRA format for fast preview.
Press 'c' to capture a high-quality frame and save as 16-bit TIFF.
"""

import cv2
import numpy as np
import time
import json
from pathlib import Path
import imageio.v3 as iio
from blackmagic_io import BlackmagicInput, PixelFormat

def capture_high_quality_frame(input_device):
    """
    Capture a high-quality frame and save as 16-bit TIFF.

    Temporarily switches to YUV10 mode, captures one frame,
    saves it, then returns control to caller.
    """
    input_device.stop_capture()

    if not input_device._input.start_capture(PixelFormat.YUV10.value):
        print("Failed to restart in YUV10 mode")
        input_device._input.start_capture(PixelFormat.BGRA.value)
        input_device._capturing = True
        return

    input_device._capturing = True

    frame_with_metadata = input_device.capture_frame_with_metadata(timeout_ms=5000)

    if frame_with_metadata is None:
        print("Failed to capture high-quality frame")
        input_device.stop_capture()
        input_device._input.start_capture(PixelFormat.BGRA.value)
        input_device._capturing = True
        return

    rgb_float = frame_with_metadata['rgb']
    rgb_uint16 = (rgb_float * 65535).astype(np.uint16)

    output_dir = Path("captures")
    output_dir.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"capture_{timestamp}.tif"

    iio.imwrite(filename, rgb_uint16, extension=".tif")

    metadata = {
        'timestamp': timestamp,
        'width': frame_with_metadata['width'],
        'height': frame_with_metadata['height'],
        'format': frame_with_metadata['format'],
        'mode': frame_with_metadata['mode'],
        'colorspace': frame_with_metadata['colorspace'],
        'eotf': frame_with_metadata['eotf'],
        'input_narrow_range': frame_with_metadata['input_narrow_range']
    }

    if 'hdr_metadata' in frame_with_metadata:
        metadata['hdr_metadata'] = frame_with_metadata['hdr_metadata']

    json_filename = filename.with_suffix('.json')
    with open(json_filename, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Saved: {filename}")
    print(f"       {json_filename}")
    print(f"  Shape: {rgb_uint16.shape}, dtype: {rgb_uint16.dtype}")
    print(f"  Format: {frame_with_metadata['format']}")
    print(f"  Colorspace: {frame_with_metadata['colorspace']}")
    print(f"  EOTF: {frame_with_metadata['eotf']}")

    input_device.stop_capture()
    input_device._input.start_capture(PixelFormat.BGRA.value)
    input_device._capturing = True

def simple_preview(device_index=0, scale=1.0):
    """
    Continuously capture and display frames using BGRA format.

    Args:
        device_index: DeckLink device to use
        scale: Display scale factor (e.g., 0.5 for half size)
    """
    with BlackmagicInput() as input_device:
        if not input_device.initialize(device_index, pixel_format=PixelFormat.BGRA):
            print("Failed to initialize device with BGRA format")
            return

        print("Waiting for signal...")

        window_name = "Capture Preview"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        frame_count = 0
        start_time = time.time()
        last_fps_update = start_time
        fps_frame_count = 0
        current_fps = 0.0
        metadata = None

        try:
            while True:
                rgb_frame = input_device.capture_frame_as_uint8()

                if rgb_frame is None:
                    print("Failed to capture frame")
                    continue

                frame_count += 1
                fps_frame_count += 1

                if frame_count == 1:
                    format_info = input_device.get_detected_format()
                    if format_info:
                        print(f"Detected format: {format_info['mode']} "
                              f"({format_info['width']}x{format_info['height']} "
                              f"@ {format_info['framerate']} fps)")

                    # Capture metadata once for display
                    frame_with_metadata = input_device.capture_frame_with_metadata(timeout_ms=1000)
                    if frame_with_metadata:
                        metadata = {
                            'mode': frame_with_metadata['mode'],
                            'format': frame_with_metadata['format'],
                            'eotf': frame_with_metadata['eotf'],
                            'colorspace': frame_with_metadata['colorspace']
                        }
                        print(f"  Mode: {metadata['mode']}, "
                              f"Format: {metadata['format']}, "
                              f"EOTF: {metadata['eotf']}, "
                              f"Matrix: {metadata['colorspace']}")

                now = time.time()
                if now - last_fps_update >= 1.0:
                    current_fps = fps_frame_count / (now - last_fps_update)
                    fps_frame_count = 0
                    last_fps_update = now

                display_frame = rgb_frame

                if scale != 1.0:
                    new_width = int(rgb_frame.shape[1] * scale)
                    new_height = int(rgb_frame.shape[0] * scale)
                    display_frame = cv2.resize(rgb_frame, (new_width, new_height))

                bgr_frame = cv2.cvtColor(display_frame.astype(np.uint8), cv2.COLOR_RGB2BGR)

                # Display FPS in top right (right-justified)
                if current_fps > 0:
                    fps_text = f"FPS: {current_fps:.1f}"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.6
                    thickness = 2
                    text_size = cv2.getTextSize(fps_text, font, font_scale, thickness)[0]
                    text_x = bgr_frame.shape[1] - text_size[0] - 10
                    cv2.putText(bgr_frame, fps_text, (text_x, 30),
                               font, font_scale, (0, 255, 0), thickness)

                # Display metadata in top left
                if metadata:
                    y_offset = 30
                    mode_text = f"Mode: {metadata['mode']}"
                    cv2.putText(bgr_frame, mode_text, (10, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    y_offset += 30

                    format_text = f"Format: {metadata['format']}"
                    cv2.putText(bgr_frame, format_text, (10, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    y_offset += 30

                    eotf_text = f"EOTF: {metadata['eotf']}"
                    cv2.putText(bgr_frame, eotf_text, (10, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    y_offset += 30

                    matrix_text = f"Matrix: {metadata['colorspace']}"
                    cv2.putText(bgr_frame, matrix_text, (10, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                cv2.imshow(window_name, bgr_frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break
                elif key == ord('c'):
                    print("\nCapturing high-quality frame...")
                    capture_high_quality_frame(input_device)
                    print("Resuming preview...")
                    time.sleep(0.5)

        except KeyboardInterrupt:
            print("\nStopping preview...")

        cv2.destroyAllWindows()


if __name__ == "__main__":
    import sys

    device_index = 0
    scale = 0.5

    if len(sys.argv) > 1:
        device_index = int(sys.argv[1])
    if len(sys.argv) > 2:
        scale = float(sys.argv[2])

    print(f"Starting preview on device {device_index} at {scale}x scale")
    print("Press 'c' to capture high-quality frame (16-bit TIFF)")
    print("Press 'q' or ESC to quit")

    simple_preview(device_index, scale)
