import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging
import time
import random
import json

class TelegramFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
    def _get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
    def _rate_limit(self):
        """Random delay to avoid rate limits"""
        delay = random.uniform(2, 5)
        time.sleep(delay)
        
    def fetch_posts(self, channel_username):
        """
        Fetch posts from a public Telegram channel via telesco.pe
        This mimics the Go version's web scraping approach
        """
        self._rate_limit()
        
        try:
            url = f"https://telesco.pe/{channel_username}"
            logging.info(f"Fetching posts from {url}")
            
            response = self.session.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            posts = []
            # Find all message containers - telesco.pe uses specific classes
            message_blocks = soup.find_all('div', class_='tgme_widget_message')
            
            logging.info(f"Found {len(message_blocks)} message blocks for {channel_username}")
            
            for block in message_blocks[:20]:  # Limit to 20 posts like the Go version
                post = self._parse_message_block(block)
                if post:
                    posts.append(post)
                    
            return posts
            
        except Exception as e:
            logging.error(f"Error fetching posts from {channel_username}: {e}")
            raise
            
    def _parse_message_block(self, block):
        """Parse a single message block into structured data"""
        try:
            # Get message ID
            message_id = 0
            id_match = re.search(r'message(\d+)', block.get('data-post', ''))
            if id_match:
                message_id = int(id_match.group(1))
            
            # Get message text
            text_div = block.find('div', class_='tgme_widget_message_text')
            message_text = ""
            if text_div:
                # Preserve HTML formatting like the Go version
                message_text = str(text_div.decode_contents()) if hasattr(text_div, 'decode_contents') else text_div.get_text()
                # Clean up the HTML a bit
                message_text = message_text.strip()
            
            # Get date
            date_tag = block.find('time')
            date_str = ""
            unix_time = 0
            if date_tag and date_tag.get('datetime'):
                date_str = date_tag['datetime']
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    unix_time = int(dt.timestamp())
                except:
                    pass
            
            # Get views
            views = 0
            views_span = block.find('span', class_='tgme_widget_message_views')
            if views_span:
                views_text = views_span.get_text().strip()
                views_match = re.search(r'([\d.]+)(K|M)?', views_text)
                if views_match:
                    value = float(views_match.group(1))
                    suffix = views_match.group(2)
                    if suffix == 'K':
                        value *= 1000
                    elif suffix == 'M':
                        value *= 1000000
                    views = int(value)
            
            # Extract media
            media = []
            
            # Photos
            photo_wraps = block.find_all('a', class_='tgme_widget_message_photo_wrap')
            for photo in photo_wraps:
                style = photo.get('style', '')
                bg_match = re.search(r"url\('([^']+)'\)", style)
                if bg_match:
                    # Convert thumbnail URL to full size
                    thumb_url = bg_match.group(1)
                    full_url = thumb_url.replace('-thumb', '')
                    media.append({
                        "type": "photo",
                        "url": full_url,
                        "width": 0,
                        "height": 0
                    })
            
            # Videos
            video_tags = block.find_all('video')
            for video in video_tags:
                src = video.get('src', '')
                if src:
                    media.append({
                        "type": "video",
                        "url": src
                    })
            
            # Files/Documents
            doc_divs = block.find_all('div', class_='tgme_widget_message_document')
            for doc in doc_divs:
                title_div = doc.find('div', class_='tgme_widget_message_document_title')
                file_url = ""
                if title_div and title_div.find('a'):
                    file_url = title_div.find('a').get('href', '')
                media.append({
                    "type": "file",
                    "url": file_url,
                    "name": title_div.get_text().strip() if title_div else ""
                })
            
            # Extract hashtags, mentions, links
            hashtags = re.findall(r'#\w+', message_text)
            mentions = re.findall(r'@\w+', message_text)
            
            # Extract links from HTML
            links = []
            if text_div:
                for a_tag in text_div.find_all('a'):
                    href = a_tag.get('href', '')
                    if href and href.startswith('http'):
                        links.append(href)
            # Also find links in text
            text_links = re.findall(r'https?://[^\s<>"]+', message_text)
            links.extend([l for l in text_links if l not in links])
            
            # Get sender name if forwarded
            sender_name = ""
            fwd_div = block.find('div', class_='tgme_widget_message_forwarded_from')
            if fwd_div:
                sender_name = fwd_div.get_text().strip()
            
            return {
                "id": message_id,
                "message": message_text,
                "date": date_str,
                "edited": False,
                "views": views,
                "forwards": 0,
                "replies": 0,
                "sender_name": sender_name,
                "media": media,
                "hashtags": hashtags,
                "mentions": mentions,
                "links": links
            }
            
        except Exception as e:
            logging.error(f"Error parsing message block: {e}")
            return None
            
    def get_channel_info(self, channel_username):
        """Get channel info from the public page"""
        self._rate_limit()
        
        try:
            url = f"https://telesco.pe/{channel_username}"
            response = self.session.get(url, headers=self._get_headers(), timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get channel title
            title = channel_username
            title_div = soup.find('div', class_='tgme_channel_info_header_title')
            if title_div:
                title = title_div.get_text().strip()
            
            # Get channel photo
            photo_url = ""
            photo_img = soup.find('img', class_='tgme_page_photo_image')
            if photo_img and photo_img.get('src'):
                photo_url = photo_img['src']
            
            # Try to get member count
            id_num = 0
            counter_div = soup.find('div', class_='tgme_channel_info_counter')
            if counter_div:
                counter_text = counter_div.get_text()
                id_match = re.search(r'(\d+)', counter_text.replace(' ', ''))
                if id_match:
                    id_num = int(id_match.group(1))
            
            return {
                "id": id_num,
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
