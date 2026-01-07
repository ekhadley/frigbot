"""
MCP server providing Discord tools for frig.

Tools:
- scroll_up: Fetch more messages from the Discord channel
- send_message: Send a message to the Discord channel
"""

import os
import json
import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("frig-discord")

# Discord API configuration from environment
DISCORD_TOKEN = os.environ.get("FRIG_DISCORD_TOKEN")
CHANNEL_ID = os.environ.get("FRIG_CHANNEL_ID")
TRIGGER_MESSAGE_ID = os.environ.get("FRIG_TRIGGER_MESSAGE_ID")
DISCORD_API = "https://discordapp.com/api/v9"


def get_headers():
    return {"Authorization": DISCORD_TOKEN}


@mcp.tool()
def scroll_up(count: int = 20) -> str:
    """
    Fetch more messages from the Discord channel for context.

    Args:
        count: Number of messages to fetch (default 20, max 100)

    Returns:
        Messages formatted as "author: content" with timestamps
    """
    if not DISCORD_TOKEN or not CHANNEL_ID:
        return "Error: Discord credentials not configured"

    count = min(count, 100)

    url = f"{DISCORD_API}/channels/{CHANNEL_ID}/messages?limit={count}"
    if TRIGGER_MESSAGE_ID:
        # Get messages before and including the trigger
        url = f"{DISCORD_API}/channels/{CHANNEL_ID}/messages?limit={count}&before={TRIGGER_MESSAGE_ID}"

    resp = requests.get(url, headers=get_headers())
    if not resp.ok:
        return f"Error fetching messages: {resp.status_code}"

    messages = resp.json()

    # Format messages (they come newest-first, reverse for chronological)
    formatted = []
    for msg in reversed(messages):
        author = msg.get("author", {}).get("global_name") or msg.get("author", {}).get("username", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")[:19].replace("T", " ")

        # Note attachments
        attachments = msg.get("attachments", [])
        attachment_note = ""
        if attachments:
            attachment_note = f" [attachments: {', '.join(a.get('filename', 'file') for a in attachments)}]"

        # Note if it's a reply
        reply_note = ""
        if msg.get("referenced_message"):
            ref_author = msg["referenced_message"].get("author", {}).get("global_name", "someone")
            reply_note = f" (replying to {ref_author})"

        formatted.append(f"[{timestamp}] {author}{reply_note}: {content}{attachment_note}")

    return "\n".join(formatted)


@mcp.tool()
def send_message(content: str, reply_to: str | None = None) -> str:
    """
    Send a message to the Discord channel.

    Args:
        content: The message content to send
        reply_to: Optional message ID to reply to (defaults to trigger message)

    Returns:
        Confirmation or error message
    """
    if not DISCORD_TOKEN or not CHANNEL_ID:
        return "Error: Discord credentials not configured"

    # Default to replying to the trigger message
    if reply_to is None:
        reply_to = TRIGGER_MESSAGE_ID

    # Split long messages
    max_len = 2000
    chunks = []
    remaining = content
    while remaining:
        if len(remaining) <= max_len:
            chunks.append(remaining)
            break
        # Try to split at newline or space
        split_at = remaining[:max_len].rfind("\n")
        if split_at < max_len // 2:
            split_at = remaining[:max_len].rfind(" ")
        if split_at < max_len // 2:
            split_at = max_len
        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:].lstrip()

    sent_ids = []
    for i, chunk in enumerate(chunks):
        post_data = {"content": chunk}

        # Only reply to the first message
        if i == 0 and reply_to:
            post_data["message_reference"] = {
                "message_id": reply_to,
                "channel_id": CHANNEL_ID
            }

        resp = requests.post(
            f"{DISCORD_API}/channels/{CHANNEL_ID}/messages",
            json=post_data,
            headers=get_headers()
        )

        if not resp.ok:
            return f"Error sending message: {resp.status_code} - {resp.text}"

        sent_ids.append(resp.json().get("id"))

    return f"Sent {len(chunks)} message(s): {', '.join(sent_ids)}"


if __name__ == "__main__":
    mcp.run()
