# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FrigBot is a Discord bot powered by Claude Code. When triggered, it spawns a Claude Code instance with full terminal access to handle conversations. The bot also provides League of Legends stats and various utility commands.

## Running the Bot

**Start/check the systemd service:**
```bash
./frig
```
Starts the service if not running, shows status if already running.

**Run in test mode (DMs instead of group chat):**
```bash
./frig test
```

**Stop the daemon:**
```bash
./frig kill
```

## Development Setup

**Install dependencies:**
```bash
uv sync
```

The project uses `uv` for dependency management. Virtual environment is in `.venv/`.

## Architecture

### Core Components

**frigbot.py - Main bot class (`Frig`)**
- Message polling loop that checks Discord API every 2 seconds
- Command routing via `self.commands` dict mapping `!command` strings to handler functions
- Spawns Claude Code instances for chat via `invoke_claude()`
- State persistence through `state.json` for RPS scores
- Provides `log(level, event_type, message, data)` helper method for structured JSON logging

**frig_mcp/server.py - Discord MCP tools**
- `scroll_up(count)` - Fetch more messages from Discord channel for context
- `send_message(content, reply_to)` - Send a message to Discord channel
- These are the only custom tools; Claude Code handles everything else natively

**frig_system_prompt.md - Personality and instructions**
- Defines frig's personality for Discord
- Points to frig_home/ as persistent storage
- Explains available tools

**frig_home/ - Frig's persistent storage**
- `journal/` - Notes, memories, conversation summaries
- `scripts/` - Utility scripts frig creates
- `data/` - Any other persistent data
- Frig can organize this however it wants

**lolManager.py - Riot API integration**
- Fetches ranked League of Legends data by summoner PUUID
- Summoner PUUIDs stored in `data/summonerPUUIDs.json`

**run.py - Entry point**
- Command-line interface with `-t/--test` flag for test mode
- Loads bot state from `state.json` on startup

**logger_config.py - Logging configuration**
- JSONL formatted file logging with structured event data
- Size-based log rotation at 50MB
- Log files in `logs/frigbot_YYYYMMDD_HHMMSS_NNN.jsonl`

### Configuration Files

**state.json** - Runtime state (auto-saved)
- RPS game scores per user
- Bot start time and paths

**.claude/settings.json** - Claude Code configuration
- MCP server configuration for frig-discord tools
- Permission settings

**Keys are stored externally** at `/home/ek/frigkeys.json`:
```json
{
  "discord": "Bot token",
  "riot": "API key",
  "tenor": "API key"
}
```

### Message Flow

1. `runloop()` polls for new messages every 2 seconds
2. `getNewMessage()` checks if message is new and not from bot itself
3. `getResponseToNewMessage()` routes to command handlers or Claude Code
4. For chat: `invoke_claude()` spawns Claude Code with the message as prompt
5. Claude Code uses MCP tools to fetch context (`scroll_up`) and reply (`send_message`)
6. Claude Code has full terminal access for anything else it needs

### Command System

Commands are defined in `Frig.commands` dict. Each maps a string like `"!help"` to a handler method. Handlers receive the raw Discord message dict and return strings or lists of strings to send.

To add a new command:
1. Add handler method to `Frig` class
2. Register in `self.commands` dict in `__init__`
3. Add description to `help_resp()` command_descriptions dict

### Chat Behavior

The bot spawns Claude Code when:
- Message is a reply to one of the bot's previous messages (`isReplyToBot()`)
- Bot is @mentioned (`botTaggedInMessage()`)
- 10% chance if message contains scrambled "itysl" (easter egg)

Claude Code instances:
- Receive the trigger message as their prompt
- Have MCP tools for Discord interaction
- Have full terminal access for anything else
- Can read/write to frig_home/ for persistence
- Run with a 2-minute timeout

### Logging Event Types

- System: `bot_started`, `bot_crashed`, `state_saved`, `state_loaded`
- Messages: `new_message`, `message_error`
- Commands: `command_found`, `command_failed`, `command_unknown`
- Chat: `chat_requested`, `claude_invoked`, `claude_completed`, `claude_error`, `claude_timeout`
- LoL: `lol_init`, `lol_lookup`, `lol_success`, `lol_api_error`
- Games: `rps_new_player`, `rps_played`
