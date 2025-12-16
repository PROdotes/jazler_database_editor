"""
Test script to verify config file location when running as EXE.
This will be compiled and run to check where the config is created.
"""
import sys
import os

print("=" * 60)
print("CONFIG LOCATION TEST")
print("=" * 60)

print(f"sys.frozen: {getattr(sys, 'frozen', False)}")
print(f"sys.executable: {sys.executable}")
print(f"__file__: {__file__}")

if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
    print(f"Running as EXE")
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Running as script")

print(f"BASE_DIR: {base_dir}")
config_file = os.path.join(base_dir, "config.json")
print(f"CONFIG_FILE: {config_file}")

# Try to create a test file
try:
    test_file = os.path.join(base_dir, "test_write.txt")
    with open(test_file, 'w') as f:
        f.write("Test write successful")
    print(f"✓ Successfully wrote to: {test_file}")
    os.remove(test_file)
    print(f"✓ Successfully deleted test file")
except Exception as e:
    print(f"✗ Error writing to {base_dir}: {e}")

print("=" * 60)
input("Press Enter to exit...")
