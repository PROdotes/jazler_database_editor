"""
Screenshot capture utility for MS Access Database Editor.
This script captures a screenshot of the active application window only.
"""
import pyautogui
import time
from pathlib import Path
from PIL import ImageGrab
import win32gui
import win32ui
import win32con

def capture_active_window():
    """Capture screenshot of the active window only."""
    print("Waiting 2 seconds for window to be ready...")
    time.sleep(2)
    
    # Get the active window
    hwnd = win32gui.GetForegroundWindow()
    
    # Get window dimensions
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bottom - top
    
    print(f"Capturing window: {win32gui.GetWindowText(hwnd)}")
    print(f"Dimensions: {width}x{height}")
    
    # Capture the window
    screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
    
    # Save screenshot
    screenshot_path = Path(__file__).parent / "screenshots" / "app_main_window.png"
    screenshot.save(screenshot_path)
    
    print(f"Screenshot saved to: {screenshot_path}")
    return screenshot_path

if __name__ == "__main__":
    try:
        capture_active_window()
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        print("\nPlease install required packages:")
        print("  pip install pyautogui pillow pywin32")
