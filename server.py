#!/usr/bin/env python3
"""Telegram MCP Server — full user account access for OpenClaw."""

import asyncio
import base64
import os
import tempfile
from datetime import datetime, timezone

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from telethon import TelegramClient
from telethon.tl.types import (
    Channel,
    Chat,
    User,
    Message,
    MessageMediaDocument,
    MessageMediaPhoto,
    MessageMediaWebPage,
)
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    os.environ.get("TELEGRAM_SESSION_NAME", "session"),
)

mcp = FastMCP("telegram", log_level="WARNING")

# Global client instance
_client: TelegramClient | None = None


async def get_client() -> TelegramClient:
    global _client
    if _client is None or not _client.is_connected():
        _client = TelegramClient(SESSION, API_ID, API_HASH)
        await _client.connect()
        if not await _client.is_user_authorized():
            raise RuntimeError(
                "Session not authorized. Run `python auth.py` first to authenticate."
            )
    return _client


def _format_entity(entity) -> dict:
    if isinstance(entity, User):
        return {
            "type": "user",
            "id": entity.id,
            "first_name": entity.first_name or "",
            "last_name": entity.last_name or "",
            "username": entity.username or "",
            "phone": entity.phone or "",
            "bot": entity.bot,
        }
    elif isinstance(entity, Channel):
        return {
            "type": "channel" if entity.broadcast else "supergroup",
            "id": entity.id,
            "title": entity.title,
            "username": entity.username or "",
            "participants_count": getattr(entity, "participants_count", None),
        }
    elif isinstance(entity, Chat):
        return {
            "type": "group",
            "id": entity.id,
            "title": entity.title,
            "participants_count": getattr(entity, "participants_count", None),
        }
    return {"type": "unknown", "id": getattr(entity, "id", None)}


def _format_message(msg: Message) -> dict:
    result = {
        "id": msg.id,
        "date": msg.date.isoformat() if msg.date else None,
        "sender_id": msg.sender_id,
        "text": msg.text or "",
        "reply_to_msg_id": msg.reply_to.reply_to_msg_id if msg.reply_to else None,
    }

    if msg.media:
        if isinstance(msg.media, MessageMediaPhoto):
            result["media"] = {"type": "photo"}
        elif isinstance(msg.media, MessageMediaDocument):
            doc = msg.media.document
            attrs = {type(a).__name__: a for a in (doc.attributes if doc else [])}
            if "DocumentAttributeAudio" in attrs:
                audio = attrs["DocumentAttributeAudio"]
                result["media"] = {
                    "type": "voice" if audio.voice else "audio",
                    "duration": audio.duration,
                    "title": getattr(audio, "title", None),
                }
            elif "DocumentAttributeVideo" in attrs:
                video = attrs["DocumentAttributeVideo"]
                result["media"] = {
                    "type": "video_note" if video.round_message else "video",
                    "duration": video.duration,
                }
            elif "DocumentAttributeSticker" in attrs:
                result["media"] = {"type": "sticker"}
            elif "DocumentAttributeFilename" in attrs:
                result["media"] = {
                    "type": "file",
                    "filename": attrs["DocumentAttributeFilename"].file_name,
                    "size": doc.size if doc else None,
                }
            else:
                result["media"] = {"type": "document", "mime": doc.mime_type if doc else None}
        elif isinstance(msg.media, MessageMediaWebPage):
            result["media"] = {"type": "webpage"}

    return result


# --- Tools ---


@mcp.tool()
async def list_chats(limit: int = 50, offset: int = 0) -> list[dict]:
    """List all chats (DMs, groups, channels). Returns id, type, title/name.
    Use offset for pagination."""
    client = await get_client()
    dialogs = await client.get_dialogs(limit=limit + offset)
    results = []
    for d in dialogs[offset : offset + limit]:
        info = _format_entity(d.entity)
        info["unread_count"] = d.unread_count
        info["last_message_date"] = d.date.isoformat() if d.date else None
        # Use dialog name as canonical title
        info["name"] = d.name
        results.append(info)
    return results


@mcp.tool()
async def get_chat_info(chat_id: str) -> dict:
    """Get detailed info about a chat by ID or username (e.g. '@username' or numeric ID)."""
    client = await get_client()
    entity = await client.get_entity(int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id)
    return _format_entity(entity)


@mcp.tool()
async def read_messages(
    chat_id: str,
    limit: int = 30,
    offset_id: int = 0,
    search: str = "",
) -> list[dict]:
    """Read messages from a chat. Use search to filter by text content.
    offset_id: get messages before this message ID (for pagination).
    Returns newest first."""
    client = await get_client()
    entity = await client.get_entity(int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id)
    messages = await client.get_messages(
        entity,
        limit=limit,
        offset_id=offset_id,
        search=search if search else None,
    )
    return [_format_message(m) for m in messages if isinstance(m, Message)]


@mcp.tool()
async def read_message(chat_id: str, message_id: int) -> dict:
    """Read a single message by ID, including full sender info."""
    client = await get_client()
    entity = await client.get_entity(int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id)
    msg = await client.get_messages(entity, ids=message_id)
    if not msg:
        return {"error": "Message not found"}
    result = _format_message(msg)
    if msg.sender:
        result["sender"] = _format_entity(msg.sender)
    return result


@mcp.tool()
async def send_message(
    chat_id: str,
    text: str,
    reply_to: int | None = None,
) -> dict:
    """Send a text message to a chat. Optionally reply to a specific message ID."""
    client = await get_client()
    entity = await client.get_entity(int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id)
    msg = await client.send_message(entity, text, reply_to=reply_to)
    return _format_message(msg)


@mcp.tool()
async def download_media(chat_id: str, message_id: int) -> dict:
    """Download media from a message. Returns the file path where it was saved."""
    client = await get_client()
    entity = await client.get_entity(int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id)
    msg = await client.get_messages(entity, ids=message_id)
    if not msg or not msg.media:
        return {"error": "No media in this message"}

    download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
    os.makedirs(download_dir, exist_ok=True)

    path = await client.download_media(msg, file=download_dir)
    return {"path": path, "message_id": message_id}


@mcp.tool()
async def send_file(
    chat_id: str,
    file_path: str,
    caption: str = "",
    voice_note: bool = False,
    video_note: bool = False,
    reply_to: int | None = None,
) -> dict:
    """Send a file/photo/video/voice to a chat. Set voice_note=True for voice messages."""
    client = await get_client()
    entity = await client.get_entity(int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id)
    msg = await client.send_file(
        entity,
        file_path,
        caption=caption,
        voice_note=voice_note,
        video_note=video_note,
        reply_to=reply_to,
    )
    return _format_message(msg)


@mcp.tool()
async def search_messages(
    query: str,
    chat_id: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Search messages globally or within a specific chat."""
    client = await get_client()
    entity = None
    if chat_id:
        entity = await client.get_entity(int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id)

    messages = await client.get_messages(
        entity,
        limit=limit,
        search=query,
    )
    results = []
    for m in messages:
        if isinstance(m, Message):
            item = _format_message(m)
            # Include chat info for global search
            if m.chat:
                item["chat"] = _format_entity(m.chat)
            results.append(item)
    return results


@mcp.tool()
async def get_participants(chat_id: str, limit: int = 100) -> list[dict]:
    """Get participants of a group or channel."""
    client = await get_client()
    entity = await client.get_entity(int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id)
    participants = await client.get_participants(entity, limit=limit)
    return [_format_entity(p) for p in participants]


@mcp.tool()
async def get_me() -> dict:
    """Get info about the authenticated Telegram account."""
    client = await get_client()
    me = await client.get_me()
    return _format_entity(me)


@mcp.tool()
async def mark_as_read(chat_id: str) -> dict:
    """Mark all messages in a chat as read."""
    client = await get_client()
    entity = await client.get_entity(int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id)
    await client.send_read_acknowledge(entity)
    return {"status": "ok", "chat_id": chat_id}


@mcp.tool()
async def forward_message(
    from_chat_id: str,
    message_id: int,
    to_chat_id: str,
) -> dict:
    """Forward a message from one chat to another."""
    client = await get_client()
    from_entity = await client.get_entity(
        int(from_chat_id) if from_chat_id.lstrip("-").isdigit() else from_chat_id
    )
    to_entity = await client.get_entity(
        int(to_chat_id) if to_chat_id.lstrip("-").isdigit() else to_chat_id
    )
    result = await client.forward_messages(to_entity, message_id, from_entity)
    if isinstance(result, list):
        return _format_message(result[0])
    return _format_message(result)


@mcp.tool()
async def delete_message(chat_id: str, message_id: int) -> dict:
    """Delete a message (own messages only in most chats)."""
    client = await get_client()
    entity = await client.get_entity(int(chat_id) if chat_id.lstrip("-").isdigit() else chat_id)
    result = await client.delete_messages(entity, [message_id])
    return {"deleted": bool(result), "message_id": message_id}


@mcp.tool()
async def get_unread_chats() -> list[dict]:
    """Get all chats with unread messages."""
    client = await get_client()
    dialogs = await client.get_dialogs(limit=100)
    results = []
    for d in dialogs:
        if d.unread_count > 0:
            info = _format_entity(d.entity)
            info["unread_count"] = d.unread_count
            info["name"] = d.name
            info["last_message_date"] = d.date.isoformat() if d.date else None
            results.append(info)
    return results


if __name__ == "__main__":
    mcp.run(transport="stdio")
