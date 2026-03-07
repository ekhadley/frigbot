# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FrigBot is a Discord bot that provides chat completions via OpenRouter, image generation, League of Legends stats, and various utility commands. The bot polls Discord's API for new messages and responds based on command prefixes or chat context.

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
- State persistence through `state.json` for RPS scores and model configuration
- Supports loading from saved state via `Frig.load_from_state_dict()`
- Provides `log(level, event_type, message, data)` helper method for structured JSON logging
- Passes log function to ChatAssistant and lolManager for unified logging
- Image generation via standalone `generate_image()` function (always uses OpenRouter API key)

**chat.py - LLM integration (`ChatAssistant`)**
- Builds proper `user`/`assistant` role-annotated message history from Discord messages (bot messages get `assistant` role, others get `user` role with `"Author: content"` prefix)
- Consecutive same-role messages are merged (required by both OpenRouter and Anthropic APIs)
- `resolveMentions()` resolves `<@ID>` Discord mentions to `@name`; `formatMessage()` adds author prefix
- Calls OpenRouter API for chat completions with optional web search plugin (disabled by default)
- Supports reasoning mode in chat completions
- Dynamic model switching at runtime
- `generate_image()` standalone function for image generation via OpenRouter (not part of the class)
- `fixLinks()` helper reformats markdown links for Discord compatibility
- Receives log function from Frig for structured event logging

**AnthropicChat.py - Anthropic direct API integration (`AnthropicChatAssistant`)**
- Subclass of `ChatAssistant`, inherits context building (`makeContext`), `formatMessage`, `resolveMentions`
- Uses Anthropic SDK directly instead of OpenRouter for `claude-*` models
- Web search tool enabled by default (`web_search_20250305`)
- Memory tool enabled by default (`memory_20250818`) via `LocalMemoryTool`
- When memory is enabled, uses `client.beta.messages.tool_runner().until_done()` for the agentic loop (auto-executes memory tool calls)
- When memory is disabled, falls back to `client.messages.create()`
- Model routing: when user sets a `claude-*` model via `!setmodel`, `frigbot.py` swaps to this backend

**memory_tool.py - Anthropic memory tool (`LocalMemoryTool`)**
- Subclass of `BetaAbstractMemoryTool` from the Anthropic SDK
- Filesystem-backed: maps virtual `/memories/...` paths to `{project_root}/memories/` on disk
- Implements 6 methods: `view`, `create`, `str_replace`, `insert`, `delete`, `rename`
- Path traversal protection prevents escaping the `memories/` directory
- Claude uses this to persist information across conversations (user preferences, context, etc.)
- The `memories/` directory is gitignored (runtime data)

**lolManager.py - Riot API integration**
- Fetches ranked League of Legends data by summoner PUUID
- Summoner PUUIDs stored in `data/summonerPUUIDs.json`
- Handles multiple queue types (RANKED_SOLO_5x5, RANKED_FLEX_SR)
- Has `match_history()` method (partially implemented)
- Receives log function from Frig for structured event logging

**run.py - Entry point**
- Command-line interface with `-t/--test` flag for test mode
- Loads bot state from `state.json` on startup
- Initializes logging via `setup_logging()` before starting bot

**logger_config.py - Logging configuration**
- JSONL (JSON Lines) formatted file logging with structured event data
- Size-based log rotation at 50MB (`MAX_LOG_FILE_SIZE` constant)
- Timestamped log files: `logs/frigbot_YYYYMMDD_HHMMSS_NNN.jsonl`
- Retains all log files indefinitely (no automatic cleanup)
- Plain text console output (no colors)
- Custom `JsonFormatter` outputs one JSON object per line
- Custom `SizedRotatingFileHandler` creates new files when size limit reached
- Log entries structured as: `{timestamp, level, name, message, data: {event_type, ...fields}}`
- Each line is a valid JSON object for easy parsing and streaming

**utils.py - Discord message formatting utilities**
- ANSI color codes for Discord message formatting (used in `!piggies` rank display)
- Two sets of color codes: standard ANSI (for terminals) and Discord ANSI (prefixed with `a`)
- `rankColors` dict maps tier names to Discord ANSI colors
- `contains_scrambled()` for fuzzy string matching
- `split_resp()` for splitting long messages
- Note: These color codes are for Discord messages, not terminal/logging output

### Configuration Files

**state.json** - Runtime state (auto-saved)
- Current chat/image model names
- RPS game scores per user
- Bot start time and paths

**Keys are stored in `.env`** (loaded by `python-dotenv` in `run.py`). See `.env.example` for the required variables:
- `DISCORD_TOKEN` - Bot token
- `OPENROUTER_API_KEY` - OpenRouter API key
- `RIOT_API_KEY` - Riot API key
- `TENOR_API_KEY` - Tenor API key
- `ANTHROPIC_API_KEY` - Anthropic API key (for direct Claude model access)

### Message Flow

1. `runloop()` polls for new messages every 2 seconds
2. `getNewMessage()` checks if message is new and not from bot itself
3. `getResponseToNewMessage()` routes to command handlers or chat completion
4. For chat: `ChatAssistant.makeContext()` builds a `list[dict]` with proper `user`/`assistant` roles from the message window
5. `ChatAssistant.getCompletion()` calls OpenRouter with message history
6. Response is split by `<split>` token and sent as multiple Discord messages

### Command System

Commands are defined in `Frig.commands` dict (frigbot.py:54-72). Each maps a string like `"!help"` to a handler method. Handlers receive the raw Discord message dict and return strings or lists of strings to send.

To add a new command:
1. Add handler method to `Frig` class
2. Register in `self.commands` dict in `__init__`
3. Add description to `help_resp()` command_descriptions dict

### Logging Philosophy

**Gigalogging.** Log aggressively. Every operation that could fail, every external API call, every tool invocation, and every response should be logged with full context. Silent failures are bugs. When in doubt, log it.

### Logging System

All logging uses the `log(level, event_type, message, data)` helper method:

```python
self.log('info', 'new_message', "New message received", {'author': msg_author, 'preview': msg_preview})
self.log('error', 'api_error', "API call failed", {'status_code': 403, 'url': url})
```

**Parameters:**
- `level`: Log level string ('info', 'error', 'warning', 'debug')
- `event_type`: Event category string (e.g., 'new_message', 'model_changed', 'lol_lookup')
- `message`: Human-readable message (simple string, no f-strings)
- `data`: Dict of structured event data (optional)

**Event Types:**
- System: `bot_started`, `bot_starting`, `bot_crashed`, `state_saved`, `state_loaded`, `entering_main_loop`
- Messages: `new_message`, `message_error`
- Commands: `command_found`, `command_failed`, `command_unknown`
- Chat: `chat_requested`, `chat_completed`, `chat_failed`, `chat_api_request`, `chat_api_response`, `chat_api_error`, `chat_usage`, `chat_empty_response`, `chat_timeout`
- Tool runner: `tool_runner_started`, `tool_runner_done`
- Web search: `web_search_used`
- Memory tool: `memory_view`, `memory_view_done`, `memory_create`, `memory_create_done`, `memory_str_replace`, `memory_str_replace_done`, `memory_insert`, `memory_insert_done`, `memory_delete`, `memory_delete_done`, `memory_rename`, `memory_rename_done` (plus `_error` variants)
- Discord: `send_failed`
- Models: `model_changed`, `model_error`
- Images: `image_requested`, `image_generated`, `image_failed`, `image_api_request`, `image_api_response`, `image_api_error`
- LoL: `lol_init`, `lol_lookup`, `lol_success`, `lol_api_error`, `lol_parse_error`, `lol_match_history`, `lol_list_summoners`
- Games: `rps_new_player`, `rps_played`

ChatAssistant and lolManager receive the log function from Frig during initialization and use it for all their logging.

### Chat Completion Behavior

The bot responds to messages if:
- Message is a reply to one of the bot's previous messages (`isReplyToBot()`)
- Bot is @mentioned (`botTaggedInMessage()`)
- 10% chance if message contains scrambled "itysl" (easter egg)

System prompt is configured in chat.py:67-77 with personality and Discord-specific constraints (no emojis, compact messages, splits for length limit).
