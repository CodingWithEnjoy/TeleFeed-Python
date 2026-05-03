#  📢 TeleFeed Python

A Python application that fetches posts from public Telegram channels and exports them as structured JSON files with automatic GitHub Actions integration. This is a Python port of the original [ircfspace/teleFeed](https://github.com/ircfspace/teleFeed) Go application.

## ✨ Features

- 🚀 **No API Required** - Uses Telegram's public web view (`t.me/s`)
- 📝 **Complete Post Data** - Message content, dates, views, media, hashtags, mentions
- 🖼️ **Media Extraction** - Photos and videos with URLs
- 🕐 **Real Timestamps** - Accurate dates with Unix timestamps
- 🔄 **Auto-Export** - GitHub Actions runs every 30 minutes
- 🌿 **Clean Repository** - Separate export branch, main stays clean
- 🛡️ **Rate Limit Protection** - Random delays and rotating user agents
- 🐍 **Pure Python** - No compilation needed, easy to modify

## Installation

1. Clone or download this project
2. Install Python (if not already installed)
3. Install Python dependencies
   
   ```bash
   pip install -r requirements.txt
   ```

## 📁 Project Structure

```
TeleFeed-Python/
├── .github/workflows/   # GitHub Actions
├── requirements.txt     # Python dependencies
├── config.json          # Channel configuration
├── main.py              # Main application
├── config.py            # Configuration loader
├── fetcher.py           # Telegram data fetcher
├── exporter.py          # JSON export functionality
└── .gitignore           # Git ignore rules
```

## 🌿 Git Branch Strategy

- **main**: Source code and configuration only
- **export**: Contains JSON export files (auto-updated)

The `export/` folder is gitignored to keep the main branch clean. Export files are automatically pushed to the `export` branch via GitHub Actions.

## Configuration

Edit `config.json` to specify which channels to export:

```json
{
  "channels": [
    "ircfspace",
    "vahidonline",
    "your_channel_name"
  ]
}
```

**Note:** Use only the username part without the `@` symbol.

## 📊 Output Structure

Each channel is exported to `export/{channel_name}.json` with comprehensive data:

```json
{
  "info": {
    "id": 0,
    "title": "Channel Title",
    "username": "channelname",
    "photo_url": "https://cdn.telesco.pe/file/..."
  },
  "posts": [
    {
      "id": 12345,
      "message": "Post content with <a href=\"links\">HTML formatting</a>",
      "date": "2026-05-03T09:30:00Z",
      "edited": false,
      "views": 1500,
      "forwards": 25,
      "replies": 10,
      "sender_name": "Sender Name",
      "media": [
        {
          "type": "photo",
          "url": "https://cdn.telesco.pe/file/...",
          "width": 800,
          "height": 600
        },
        {
          "type": "video", 
          "url": "https://cdn.telesco.pe/file/..."
        }
      ],
      "hashtags": ["#example", "#telegram"],
      "mentions": ["@user"],
      "links": ["https://example.com"]
    }
  ],
  "last_updated": 1777791234
}
```

## 🔄 Auto-Export with GitHub Actions

The project includes automated GitHub Actions that:

- **Run every 30 minutes** - Automatic channel updates
- **Separate branches** - Clean main branch, exports in `export` branch
- **Rate limiting** - Random delays and user agents
- **Error handling** - Continues even if some channels fail
- **Detailed logging** - Summary reports with file statistics

### Branch Strategy
- **main**: Source code and configuration only
- **export**: JSON export files (auto-updated)

## ⚙️ Configuration

Edit `config.json` to specify channels:

```json
{
  "channels": [
    "ircfspace",
    "vahidonline", 
    "your_channel"
  ]
}
```

## 🚀 Deployment

### GitHub Actions (Recommended)
1. Push code to GitHub
2. Enable Actions in repository settings
3. Automatic exports every 30 minutes

## 📋 Requirements

- Python Installed
- Internet connection
- Public Telegram channels only

## ⚠️ Limitations

- **Public channels only** - No private channel support
- **Recent posts** - Limited by Telegram's public feed
- **Rate limits** - Built-in protection but may need adjustments
- **HTML dependency** - May break if Telegram changes web structure
