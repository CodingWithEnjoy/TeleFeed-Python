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
            # Get channel info
            channel_info = fetcher.get_channel_info(channel)
            
            # Get posts - pass just the username, not a URL
            posts = fetcher.fetch_posts(channel)
            
            data = {
                "info": channel_info,
                "posts": posts,
                "last_updated": int(time.time())
            }
            
            exporter.export_to_json(channel, data)
            logging.info(f"Successfully exported {len(posts)} posts for {channel}")
            
        except Exception as e:
            logging.error(f"Failed to process channel {channel}: {e}")
            continue

if __name__ == "__main__":
    main()
