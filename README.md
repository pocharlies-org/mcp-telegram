# mcp-telegram

MCP server for Telegram **user accounts** (not bots). Connects via MTProto using [Telethon](https://github.com/LonamiWebs/Telethon), giving full access to all chats, DMs, groups, channels, and media.

## Features

- Read messages from any chat (DMs, groups, channels)
- Send messages and reply to specific messages
- Download and send media (photos, videos, voice notes, files)
- Search messages globally or per-chat
- List group/channel participants
- Forward and delete messages
- Track unread chats

## Setup

1. Get API credentials from [my.telegram.org](https://my.telegram.org)
2. Install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Configure `.env`:

```bash
cp .env.example .env
# Edit .env with your api_id and api_hash
```

4. Authenticate (one-time, interactive):

```bash
python auth.py
```

5. Run the MCP server:

```bash
python server.py
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `list_chats` | List all chats with unread counts |
| `read_messages` | Read messages with search and pagination |
| `read_message` | Read a single message with sender info |
| `send_message` | Send text, optionally as reply |
| `download_media` | Download media from a message |
| `send_file` | Send files, voice/video notes |
| `search_messages` | Global or per-chat search |
| `get_participants` | List group/channel members |
| `forward_message` | Forward between chats |
| `delete_message` | Delete own messages |
| `get_unread_chats` | Chats with unread messages |
| `mark_as_read` | Mark chat as read |
| `get_chat_info` | Chat/user details |
| `get_me` | Authenticated account info |

## MCPorter Integration

Add to `~/.mcporter/mcporter.json`:

```json
{
  "telegram": {
    "command": "/path/to/mcp-telegram/venv/bin/python3",
    "args": ["/path/to/mcp-telegram/server.py"]
  }
}
```
