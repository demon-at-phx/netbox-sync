import time
import sys
import logging
from app.settings import load_config
from app.logger import setup_logger
from app.sync_engine import SyncEngine

def main():
    # 1. Load Configuration
    try:
        config = load_config("config.ini")
    except Exception as e:
        print(f"Critical Error loading config: {e}")
        sys.exit(1)

    # 2. Setup Logging
    logger = setup_logger(config)
    logger.info("Starting Netbox-PDQ Sync Application")

    # 3. Initialize Sync Engine
    engine = SyncEngine(config, logger)

    # 4. Main Loop
    while True:
        try:
            logger.info("Starting Sync Cycle")
            engine.run_sync()
            logger.info(f"Sync Cycle Completed. Sleeping for {config.getint('General', 'sync_interval')} seconds.")
        except KeyboardInterrupt:
            logger.info("Stopping application...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        
        time.sleep(config.getint('General', 'sync_interval'))

if __name__ == "__main__":
    main()
