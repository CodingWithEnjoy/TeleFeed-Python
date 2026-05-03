import json
import logging
import sys
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
            # The original Go app used telesco.pe RSS feeds.
            # We'll mimic that approach for public data.
            url = f"https://telesco.pe/{channel}/rss"
            posts = fetcher.fetch_posts(url)
            channel_info = fetcher.get_channel_info(channel)
            
            data = {
                "info": channel_info,
                "posts": posts,
                "last_updated": int(time.time())
            }
            
            exporter.export_to_json(channel, data)
            logging.info(f"Successfully exported {len(posts)} posts for {channel}")
            
        except Exception as e:
            logging.error(f"Failed to process channel {channel}: {e}")
            # Continue with next channel, just like the Go version does
            continue

if __name__ == "__main__":
    import time
    main()