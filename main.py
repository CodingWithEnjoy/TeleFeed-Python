import json
import logging
import sys
import time
from fetcher import TelegramFetcher
from exporter import Exporter
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    try:
        channels = Config.load_channels()
    except Exception as e:
        logging.error(f"Failed to load config.json: {e}")
        sys.exit(1)

    fetcher = TelegramFetcher()
    exporter = Exporter()

    for channel in channels:
        logging.info(f"Processing channel: {channel}")
        try:
            # Now uses the same fetch_channel_data() function signature
            data = fetcher.fetch_channel_data(channel)
            
            if data:
                exporter.export_to_json(channel, data)
                logging.info(f"Successfully exported {len(data['posts'])} posts for {channel}")
            else:
                logging.error(f"No data returned for {channel}")
            
        except Exception as e:
            logging.error(f"Failed to process channel {channel}: {e}")
            continue

if __name__ == "__main__":
    main()
