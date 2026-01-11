"""
Library Snapshot Generator
Processes all MP3s in the library and saves their ID3 metadata to a JSON file.
"""

import os
import sys
import logging
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.services.snapshot_service import SnapshotService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_generator():
    # 1. Load configuration
    config_path = Path('config/connections.json')
    if not config_path.exists():
        logger.error("config/connections.json not found!")
        return

    with open(config_path, 'r') as f:
        config = json.load(f)

    # 2. Identify folders to scan
    # We use local drive mappings if possible
    drive_map = config.get('drive_map', {})
    scan_folders = []
    
    if drive_map:
        for remote, local in drive_map.items():
            if os.path.exists(local):
                scan_folders.append(local)
    
    base_path = config.get('base_songs_path')
    if base_path and os.path.exists(base_path):
        if base_path not in scan_folders:
            scan_folders.append(base_path)

    if not scan_folders:
        logger.error("No valid folders found to scan! Check your drive_map in config.")
        return

    logger.info(f"Preparing to scan: {scan_folders}")

    # 3. Initialize snapshot service
    cache_path = Path('config/metadata_snapshot.json')
    service = SnapshotService(str(cache_path))
    
    # Optional: Load existing cache to skip or update
    # service.load_cache()

    # 4. Generate snapshot
    try:
        service.generate_snapshot(scan_folders, max_workers=20)
        print("\n" + "="*50)
        print(f"SUCCESS: Snapshot generated with {len(service.metadata_cache)} entries.")
        print(f"Output: {cache_path}")
        print("="*50)
    except Exception as e:
        logger.error(f"Snapshot generation failed: {e}")

if __name__ == "__main__":
    run_generator()
