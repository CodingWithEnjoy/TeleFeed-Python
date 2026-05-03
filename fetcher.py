import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging
import time
import random

class TelegramFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; TeleFeedPython/1.0)'
        })
        
    def _rate_limit(self):
        """Random delay to avoid rate limits, just like the Go version"""
        delay = random.uniform(1, 3)
        time.sleep(delay)
        
    def fetch_posts(self, rss_url):
        """Fetch posts from a public Telegram RSS feed"""
        self._rate_limit()
        
        try:
            response = self.session.get(rss_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'xml')
            
            posts = []
            items = soup.find_all('item')
            
            for item in items[:50]:  # Limit to recent 50 posts
                post = self._parse_post(item)
                if post:
                    posts.append(post)
                    
            return posts
            
        except Exception as e:
            logging.error(f"Error fetching posts from {rss_url}: {e}")
            raise
            
    def _parse_post(self, item):
        """Parse a single RSS item into structured post data"""
        try:
            title = item.find('title').text if item.find('title') else ""
            description = item.find('description').text if item.find('description') else ""
            link = item.find('link').text if item.find('link') else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') else ""
            
            # Extract post ID from link
            post_id = 0
            id_match = re.search(r'/(\d+)$', link)
            if id_match:
                post_id = int(id_match.group(1))
                
            # Extract hashtags, mentions, and links
            hashtags = re.findall(r'#\w+', description)
            mentions = re.findall(r'@\w+', description)
            links = re.findall(r'https?://[^\s<>"]+', description)
            
            # Determine media (simplified from Go version)
            media = []
            if item.find('enclosure'):
                enc = item.find('enclosure')
                media_type = "photo" if "image" in enc.get('type', '') else "video"
                media.append({
                    "type": media_type,
                    "url": enc.get('url', ''),
                    "width": 0,
                    "height": 0
                })
                
            # Parse date
            pub_date_parsed = None
            try:
                pub_date_parsed = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z')
                pub_date_iso = pub_date_parsed.isoformat() + 'Z'
            except:
                pub_date_iso = pub_date
                
            return {
                "id": post_id,
                "message": description,
                "date": pub_date_iso,
                "edited": False,
                "views": 0,  # RSS feeds don't include views
                "forwards": 0,
                "replies": 0,
                "sender_name": title,
                "media": media,
                "hashtags": hashtags,
                "mentions": mentions,
                "links": links
            }
            
        except Exception as e:
            logging.error(f"Error parsing post: {e}")
            return None
            
    def get_channel_info(self, channel_username):
        """Get basic channel info from the public web page"""
        self._rate_limit()
        
        try:
            url = f"https://telesco.pe/{channel_username}"
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = channel_username
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.text.strip()
                
            photo_url = ""
            img = soup.find('img', class_='channel-photo')
            if img and img.get('src'):
                photo_url = img['src']
                
            return {
                "id": 0,
                "title": title,
                "username": channel_username,
                "photo_url": photo_url
            }
            
        except Exception as e:
            logging.error(f"Error getting channel info for {channel_username}: {e}")
            return {
                "id": 0,
                "title": channel_username,
                "username": channel_username,
                "photo_url": ""
            }