import shutil
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def sync_test_db(live_path: str, target_filename: str = "JZRS2DB-V5.accdb") -> tuple[str, bool]:
    """
    Syncs the live database to the local Downloads folder for testing.
    
    Returns:
        tuple: (path_to_use, was_copied)
    """
    # Get user's Downloads folder
    try:
        if os.name == 'nt':
            # Windows Downloads path properly resolved
            downloads_path = Path(os.environ['USERPROFILE']) / 'Downloads'
        else:
            # Fallback for other systems
            downloads_path = Path.home() / 'Downloads'
            
        target_path = downloads_path / target_filename
        
        # 1. Try to copy live to target
        if live_path and os.path.exists(live_path):
            try:
                # Ensure target directory exists (should exist but good practice)
                downloads_path.mkdir(parents=True, exist_ok=True)
                
                logger.info(f"Attempting to sync live DB from {live_path} to {target_path}")
                shutil.copy2(live_path, target_path)
                logger.info("Successfully copied live DB to Downloads.")
                return str(target_path), True
            except Exception as e:
                logger.error(f"Failed to copy live DB to Downloads: {e}")
                
        # 2. Fallback: If copy failed or live path missing, check if target already exists
        if target_path.exists():
            logger.info(f"Using existing copy found in Downloads: {target_path}")
            return str(target_path), False
            
    except Exception as e:
        logger.error(f"Critical failure in test DB sync logic: {e}")
        
    return None, False
