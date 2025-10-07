#!/usr/bin/env python3
"""
Example usage of the Blackmagic DeckLink Output Library

This example demonstrates how to:
1. Display a static frame from a NumPy array
2. Display solid colors
3. Display test patterns
4. Update frames dynamically
"""

import numpy as np
import time
from blackmagic_output import BlackmagicOutput, DisplayMode, create_test_pattern

def example_static_frame():
    """Example: Display a static frame from NumPy array"""
    print("Example 1: Static Frame Output")
    
    # Create a simple gradient test image
    width, height = 1920, 1080
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create a gradient pattern
    for y in range(height):
        for x in range(width):
            frame[y, x] = [
                int(255 * x / width),      # Red gradient
                int(255 * y / height),     # Green gradient
                128                        # Blue constant
            ]
    
    # Display the frame
    with BlackmagicOutput() as output:
        devices = output.get_available_devices()
        print(f"Available devices: {devices}")
        
        if not devices:
            print("No DeckLink devices found!")
            return
        
        # Initialize and display
        if output.initialize(device_index=0):
            print("Device initialized successfully")
            
            if output.display_static_frame(frame, DisplayMode.HD1080p25):
                print("Frame displayed successfully. Press Ctrl+C to stop...")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nStopping output...")
            else:
                print("Failed to display frame")
        else:
            print("Failed to initialize device")

def example_solid_colors():
    """Example: Display different solid colors"""
    print("Example 2: Solid Color Output")
    
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
        (255, 255, 255),# White
        (0, 0, 0),      # Black
    ]
    
    with BlackmagicOutput() as output:
        if not output.initialize():
            print("Failed to initialize device")
            return
        
        print("Cycling through colors. Press Ctrl+C to stop...")
        try:
            for i, color in enumerate(colors):
                color_name = ["Red", "Green", "Blue", "Yellow", "Magenta", "Cyan", "White", "Black"][i]
                print(f"Displaying {color_name}: {color}")
                
                if output.display_solid_color(color, DisplayMode.HD1080p25):
                    time.sleep(2)  # Display each color for 2 seconds
                else:
                    print(f"Failed to display {color_name}")
                    break
        except KeyboardInterrupt:
            print("\nStopping color cycle...")

def example_test_patterns():
    """Example: Display various test patterns"""
    print("Example 3: Test Pattern Output")
    
    patterns = ['gradient', 'bars', 'checkerboard']
    
    with BlackmagicOutput() as output:
        if not output.initialize():
            print("Failed to initialize device")
            return
        
        # Get display mode info
        mode_info = output.get_display_mode_info(DisplayMode.HD1080p25)
        width, height = mode_info['width'], mode_info['height']
        print(f"Display mode: {width}x{height} @ {mode_info['framerate']}fps")
        
        print("Cycling through test patterns. Press Ctrl+C to stop...")
        try:
            for pattern_name in patterns:
                print(f"Displaying {pattern_name} pattern")
                
                # Create test pattern
                frame = create_test_pattern(width, height, pattern_name)
                
                if output.display_static_frame(frame, DisplayMode.HD1080p25):
                    time.sleep(3)  # Display each pattern for 3 seconds
                else:
                    print(f"Failed to display {pattern_name} pattern")
                    break
        except KeyboardInterrupt:
            print("\nStopping pattern cycle...")

def example_dynamic_updates():
    """Example: Update frames dynamically"""
    print("Example 4: Dynamic Frame Updates")
    
    with BlackmagicOutput() as output:
        if not output.initialize():
            print("Failed to initialize device")
            return
        
        # Get display settings
        mode_info = output.get_display_mode_info(DisplayMode.HD1080p25)
        width, height = mode_info['width'], mode_info['height']
        
        # Create initial frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Start with initial frame
        if not output.display_static_frame(frame, DisplayMode.HD1080p25):
            print("Failed to start output")
            return
        
        print("Starting dynamic animation. Press Ctrl+C to stop...")
        
        try:
            frame_count = 0
            while True:
                # Create animated pattern - moving diagonal bars
                frame.fill(0)  # Clear frame
                
                offset = (frame_count * 2) % (width + height)
                
                for y in range(height):
                    for x in range(width):
                        # Create diagonal moving pattern
                        if (x + y - offset) % 40 < 20:
                            frame[y, x] = [255, 255, 255]  # White bars
                        else:
                            frame[y, x] = [0, 0, 100]      # Dark blue background
                
                # Update the frame
                if not output.update_frame(frame):
                    print("Failed to update frame")
                    break
                
                frame_count += 1
                time.sleep(1/25)  # 25 fps update rate
                
        except KeyboardInterrupt:
            print("\nStopping animation...")

def example_from_image_file():
    """Example: Load and display image from file"""
    print("Example 5: Display Image from File")
    
    try:
        from PIL import Image
        import os
        
        # Try to find an image file in current directory
        image_files = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        
        if not image_files:
            print("No image files found in current directory")
            print("Please place a PNG, JPG, or BMP file in the current directory")
            return
        
        image_path = image_files[0]
        print(f"Loading image: {image_path}")
        
        # Load and resize image
        with Image.open(image_path) as img:
            img = img.convert('RGB')  # Ensure RGB format
            img = img.resize((1920, 1080))  # Resize to HD
            frame = np.array(img)
        
        # Display the image
        with BlackmagicOutput() as output:
            if output.initialize():
                if output.display_static_frame(frame, DisplayMode.HD1080p25):
                    print(f"Displaying {image_path}. Press Ctrl+C to stop...")
                    try:
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        print("\nStopping display...")
                else:
                    print("Failed to display image")
            else:
                print("Failed to initialize device")
                
    except ImportError:
        print("PIL (Pillow) not available. Install with: pip install pillow")

def main():
    """Main function to run examples"""
    examples = [
        ("Static Frame", example_static_frame),
        ("Solid Colors", example_solid_colors),
        ("Test Patterns", example_test_patterns),
        ("Dynamic Updates", example_dynamic_updates),
        ("Image from File", example_from_image_file),
    ]
    
    print("Blackmagic DeckLink Output Library Examples")
    print("=" * 50)
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"{i}. {name}")
    
    print("0. Run all examples")
    print()
    
    try:
        choice = input("Select example (0-5): ").strip()
        
        if choice == "0":
            for name, func in examples:
                print(f"\n{'='*20} {name} {'='*20}")
                func()
                print()
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            idx = int(choice) - 1
            name, func = examples[idx]
            print(f"\n{'='*20} {name} {'='*20}")
            func()
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()