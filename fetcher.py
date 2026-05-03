import requests
import re
import time
import random
import logging
from datetime import datetime

class TelegramFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.172",
        ]
        
    def _get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
    def _rate_limit(self):
        """Random delay to avoid rate limiting - matches Go version's 2-5 second delay"""
        delay = random.uniform(2, 5)
        logging.info(f"  - Waiting {delay:.1f}s before request...")
        time.sleep(delay)
        
    def fetch_channel_data(self, username):
        """
        Fetch channel data exactly like the Go version's fetchChannelData()
        Uses https://t.me/s/{username} instead of telesco.pe
        """
        self._rate_limit()
        
        url = f"https://t.me/s/{username}"
        logging.info(f"Fetching {url}")
        
        try:
            response = self.session.get(
                url, 
                headers=self._get_headers(), 
                timeout=30,
                allow_redirects=True
            )
            
            if response.status_code != 200:
                logging.error(f"HTTP error: {response.status_code}")
                return None
            
            html = response.text
            
            # Extract channel info - matches Go's extractChannelInfo()
            channel_info = self._extract_channel_info(html, username)
            
            # Extract posts - matches Go's extractPostsFromHTML2()
            posts = self._extract_posts(html)
            
            return {
                "info": channel_info,
                "posts": posts,
                "last_updated": int(time.time())
            }
            
        except Exception as e:
            logging.error(f"Failed to fetch channel {username}: {e}")
            raise
    
    def _extract_channel_info(self, html, username):
        """Matches Go's extractChannelInfo() exactly"""
        # Extract channel title from og:title meta tag
        title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        title = title_match.group(1) if title_match else username
        
        # Extract channel photo from og:image meta tag
        photo_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        photo = photo_match.group(1) if photo_match else ""
        
        return {
            "id": 0,  # Not available in HTML, matches Go version
            "title": title,
            "username": username,
            "photo_url": photo
        }
    
    def _extract_posts(self, html):
        """
        Matches Go's extractPostsFromHTML2()
        Finds all tgme_widget_message_wrap divs and parses each one
        """
        # Find all message wrap blocks - exact pattern from Go version
        message_pattern = re.compile(r'<div class="tgme_widget_message_wrap[^>]*>')
        message_blocks = message_pattern.findall(html)
        
        logging.info(f"Found {len(message_blocks)} message wraps in HTML")
        
        if not message_blocks:
            logging.warning("No message wraps found!")
            return []
        
        # Now extract the full HTML for each message block
        posts = []
        # Split HTML by message wrap and parse each section
        sections = re.split(r'<div class="tgme_widget_message_wrap[^>]*>', html)[1:]  # Skip first empty part
        
        for i, section in enumerate(sections[:20]):  # Limit to 20 posts
            try:
                # Find closing div for this message
                post_html = self._extract_post_html(section)
                if post_html:
                    post = self._parse_single_post(post_html, i)
                    posts.append(post)
            except Exception as e:
                logging.error(f"Error parsing post {i}: {e}")
                continue
        
        return posts
    
    def _extract_post_html(self, section):
        """Extract complete post HTML by finding matching closing divs"""
        # Find the end of this message block
        depth = 0
        for i, char in enumerate(section):
            if section[i:i+4] == '<div':
                depth += 1
            elif section[i:i+5] == '</div':
                depth -= 1
                if depth == 0:
                    return section[:i+6]
        return section  # Return whole section if we can't find the end
    
    def _parse_single_post(self, post_html, index):
        """Matches Go's parseSinglePost() exactly"""
        
        # Extract post ID from data-post attribute
        post_id = 0
        id_match = re.search(r'data-post="[^"]*/(\d+)"', post_html)
        if id_match:
            post_id = int(id_match.group(1))
        
        # Extract message text
        message = ""
        message_match = re.search(r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>', post_html, re.DOTALL)
        if message_match:
            # Remove HTML tags but keep text
            message = re.sub(r'<[^>]*>', '', message_match.group(1))
            message = message.strip()
        
        # Extract date from time tag
        date_iso = ""
        post_date = datetime.now()
        date_match = re.search(r'<time datetime="([^"]+)"', post_html)
        if date_match:
            date_iso = date_match.group(1)
            try:
                # Parse ISO 8601 format
                post_date = datetime.fromisoformat(date_iso.replace('Z', '+00:00'))
            except:
                pass
        
        # Extract views
        views = 0
        views_match = re.search(r'<span class="tgme_widget_message_views">([^<]+)</span>', post_html)
        if views_match:
            view_str = views_match.group(1).strip()
            if 'K' in view_str:
                view_str_clean = view_str.replace('K', '')
                try:
                    views = int(float(view_str_clean) * 1000)
                except:
                    pass
            else:
                try:
                    views = int(view_str)
                except:
                    pass
        
        # Extract media URLs
        media = self._extract_media(post_html)
        
        # Extract hashtags, mentions, links from message
        hashtags = re.findall(r'#\w+', message)
        mentions = re.findall(r'@\w+', message)
        links = re.findall(r'https?://[^\s<>"]+', message)
        
        return {
            "id": post_id,
            "message": message,
            "date": date_iso if date_iso else post_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "edited": False,
            "views": views,
            "forwards": 0,
            "replies": 0,
            "sender_name": "",
            "media": media,
            "hashtags": hashtags,
            "mentions": mentions,
            "links": links
        }
    
    def _extract_media(self, post_html):
        """Extract media (photos, videos) from post HTML"""
        media = []
        
        # Extract photo URLs
        photo_matches = re.findall(r'<img[^>]*src="([^"]+)"', post_html)
        for url in photo_matches:
            if 'telegram' in url or 't.me' in url:
                media.append({
                    "type": "photo",
                    "url": url,
                    "width": 0,
                    "height": 0
                })
        
        # Extract video URLs
        video_matches = re.findall(r'<video[^>]*src="([^"]+)"', post_html)
        for url in video_matches:
            media.append({
                "type": "video",
                "url": url
            })
        
        return media
