# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FrigBot is a Discord bot that provides chat completions via OpenRouter, image generation, League of Legends stats, and various utility commands. The bot polls Discord's API for new messages and responds based on command prefixes or chat context.

## Running the Bot

**Start the bot (foreground):**
```bash
./frig
```

**Start with test chat ID (DMs instead of group chat):**
```bash
./frig -t
```

**Start as systemd daemon (background):**
```bash
./frig -q
```

**Stop the daemon:**
```bash
./frigkill
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
- State persistence through `state.json` for RPS scores and model configuration
- Supports loading from saved state via `Frig.load_from_state_dict()`

**chat.py - LLM integration (`ChatAssistant`)**
- Tree-structured message history via `Message` class with parent/child relationships
- Each Discord message becomes a node; replies create branches in the conversation tree
- Calls OpenRouter API for chat completions with optional web search plugin
- Supports both chat and image generation models
- Dynamic model switching at runtime

**lolManager.py - Riot API integration**
- Fetches ranked League of Legends data by summoner PUUID
- Summoner PUUIDs stored in `summonerPUUIDs.json`
- Handles multiple queue types (RANKED_SOLO_5x5, RANKED_FLEX_SR)

**run.py - Entry point**
- Command-line interface with `-t/--test` flag for test mode
- Loads bot state from `state.json` on startup

**utils.py - Terminal formatting utilities**
- ANSI color codes for console output
- `contains_scrambled()` for fuzzy string matching

### Configuration Files

**state.json** - Runtime state (auto-saved)
- Current chat/image model names
- RPS game scores per user
- Bot start time and paths

**Keys are stored externally** at `/home/ek/frigkeys.json` with this structure:
```json
{
  "discord": "Bot token",
  "openrouter": "API key",
  "riot": "API key",
  "tenor": "API key"
}
```

### Message Flow

1. `runloop()` polls for new messages every 2 seconds
2. `getNewMessage()` checks if message is new and not from bot itself
3. `getResponseToNewMessage()` routes to command handlers or chat completion
4. For chat: `ChatAssistant.addMessageFromChat()` builds conversation tree
5. `ChatAssistant.getCompletion()` calls OpenRouter with message history
6. Response is split by `<split>` token and sent as multiple Discord messages

### Command System

Commands are defined in `Frig.commands` dict (frigbot.py:52-70). Each maps a string like `"!help"` to a handler method. Handlers receive the raw Discord message dict and return strings or lists of strings to send.

To add a new command:
1. Add handler method to `Frig` class
2. Register in `self.commands` dict in `__init__`
3. Add description to `help_resp()` command_descriptions dict

### Chat Completion Behavior

The bot responds to messages if:
- Message is a reply to one of the bot's previous messages (`requiresResponse()`)
- Bot is @mentioned (`botTaggedInMessage()`)
- 10% chance if message contains scrambled "itysl" (easter egg)

System prompt is configured in chat.py:62-74 with personality and Discord-specific constraints (no emojis, compact messages, splits for length limit).
