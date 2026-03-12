# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FrigBot is a Discord bot that provides chat completions via OpenRouter, image generation, League of Legends stats, and various utility commands. Built on discord.py with slash commands and event-driven message handling.

## Running the Bot

**Start/check the systemd service:**
```bash
./frig
```
Starts the service if not running, shows status if already running.

**Run in test mode (test channel with instant command sync):**
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

**frigbot.py - Main bot class (`FrigBot`)**
- Composition pattern: owns a `discord.Client` + `app_commands.CommandTree`
- Event-driven: `on_ready` initializes the assistant and syncs slash commands, `on_message` handles chat completions
- `_msg_to_dict()` adapter converts `discord.Message` to dict format that chat.py expects (keeps chat.py untouched)
- `OLD_BOT_ID` maps old userbot messages to current bot ID for transition continuity
- All slash commands registered in `_register_commands()` as closures over `self`
- `interaction_check` restricts all commands to `self.channel_id`
- Sync API calls (LLM, Riot, Tenor) wrapped in `asyncio.to_thread()`
- State persistence through `state.json` for RPS scores and model configuration
- `load_state()` / `save_state()` instance methods for state management
- Provides `log(level, event_type, message, data)` helper for structured JSON logging

**chat.py - LLM integration (`ChatAssistant`)**
- Builds proper `user`/`assistant` role-annotated message history from dicts (bot messages get `assistant` role, others get `user` role with `"Author: content"` prefix)
- Consecutive same-role messages are merged (required by both OpenRouter and Anthropic APIs)
- `resolveMentions()` resolves `<@ID>` Discord mentions to `@name`; `formatMessage()` adds author prefix
- Calls OpenRouter API for chat completions with optional web search plugin (disabled by default)
- Supports reasoning mode in chat completions
- Dynamic model switching at runtime
- `generate_image()` standalone function for image generation via OpenRouter (not part of the class)
- `fixLinks()` helper reformats markdown links for Discord compatibility
- Receives log function from FrigBot for structured event logging

**AnthropicChat.py - Anthropic direct API integration (`AnthropicChatAssistant`)**
- Subclass of `ChatAssistant`, inherits context building (`makeContext`), `formatMessage`, `resolveMentions`
- Uses Anthropic SDK directly instead of OpenRouter for `claude-*` models
- Web search tool enabled by default (`web_search_20250305`)
- Memory tool enabled by default (`memory_20250818`) via `LocalMemoryTool`
- When memory is enabled, uses `client.beta.messages.tool_runner().until_done()` for the agentic loop (auto-executes memory tool calls)
- When memory is disabled, falls back to `client.messages.create()`
- Model routing: when user sets a `claude-*` model via `/setmodel`, `frigbot.py` swaps to this backend

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
- Receives log function from FrigBot for structured event logging

**run.py - Entry point**
- Command-line interface with `-t/--test` flag for test mode
- Reads `DISCORD_CHANNEL_ID`, `DISCORD_GUILD_ID`, and optionally `DISCORD_TEST_CHANNEL_ID` from env
- Test mode uses test channel ID with guild-specific (instant) command sync
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

**utils.py - Utility functions and constants**
- Terminal ANSI color codes (for console logging)
- `TIER_COLORS` dict maps League tier names to hex color values (for Discord embeds)
- `contains_scrambled()` for fuzzy string matching
- `split_resp()` for splitting long messages

### Configuration Files

**state.json** - Runtime state (auto-saved)
- Current chat/image model names
- RPS game scores per user
- Bot start time

**Keys are stored in `.env`** (loaded by `python-dotenv` in `run.py`):
- `DISCORD_TOKEN` - Bot token (from Discord developer portal)
- `DISCORD_CHANNEL_ID` - Main channel ID for bot operations
- `DISCORD_GUILD_ID` - Server/guild ID for slash command sync
- `DISCORD_TEST_CHANNEL_ID` - (optional) Test channel ID for `-t` mode
- `OPENROUTER_API_KEY` - OpenRouter API key
- `RIOT_API_KEY` - Riot API key
- `TENOR_API_KEY` - Tenor API key
- `ANTHROPIC_API_KEY` - Anthropic API key (for direct Claude model access)

### Message Flow

1. discord.py `on_message` event fires for new messages
2. Messages from bots or wrong channel are ignored
3. Reply-to-bot or @mention triggers chat completion:
   a. Fetch last 100 messages via `channel.history()`
   b. Convert to dicts via `_msg_to_dict()`, pass to `makeContext()` → `getCompletion()` via `asyncio.to_thread()`
   c. Show typing indicator while processing
   d. Split response on `<split>`, first part via `message.reply()`, rest via `channel.send()`
4. 10% chance Easter egg: scrambled "itysl" → random gif

### Slash Commands

All commands use discord.py `app_commands.CommandTree`. Restricted to configured channel via `interaction_check`.

| Command | Params | Notes |
|---------|--------|-------|
| `/help` | — | Ephemeral |
| `/model` | — | Shows chat + image model |
| `/setmodel` | `model: str` | Deferred. Validates via OpenRouter, swaps backend for claude models |
| `/setimgmodel` | `model: str` | Deferred. Validates image output modality |
| `/img` | `prompt: str` | Deferred. Sends image as `discord.File` |
| `/rps` | `choice: Choice[str] \| None` | Optional. None = show score |
| `/gif` | `query: str` | Deferred |
| `/roll` | `max: Range[int, 1]` | Type-validated |
| `/lp` | `summoner: str` | Deferred. Embed with RANKED_SOLO_5x5 |
| `/piggies` | — | Deferred. Embed with all summoners sorted |
| `/coin` | — | |
| `/uptime` | — | |
| `/poem` | — | |

To add a new slash command:
1. Add the command function inside `_register_commands()` with `@self.tree.command()` decorator
2. For sync API calls, use `await interaction.response.defer()` + `asyncio.to_thread()` + `interaction.followup.send()`
3. Add description to `help_cmd` lines list

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
- System: `bot_started`, `bot_starting`, `commands_synced`, `state_saved`, `state_loaded`
- Messages: `new_message`, `message_error`
- Chat: `chat_requested`, `chat_completed`, `chat_failed`, `chat_api_request`, `chat_api_response`, `chat_api_error`, `chat_usage`, `chat_empty_response`, `chat_timeout`
- Tool runner: `tool_runner_started`, `tool_runner_done`
- Web search: `web_search_used`
- Memory tool: `memory_view`, `memory_view_done`, `memory_create`, `memory_create_done`, `memory_str_replace`, `memory_str_replace_done`, `memory_insert`, `memory_insert_done`, `memory_delete`, `memory_delete_done`, `memory_rename`, `memory_rename_done` (plus `_error` variants)
- Models: `model_changed`, `model_error`
- Images: `image_requested`, `image_generated`, `image_failed`, `image_api_request`, `image_api_response`, `image_api_error`
- LoL: `lol_init`, `lol_lookup`, `lol_success`, `lol_api_error`, `lol_parse_error`, `lol_match_history`, `lol_list_summoners`
- Games: `rps_new_player`, `rps_played`

ChatAssistant and lolManager receive the log function from FrigBot during initialization and use it for all their logging.

### Chat Completion Behavior

The bot responds to messages if:
- Message is a reply to one of the bot's previous messages
- Bot is @mentioned
- 10% chance if message contains scrambled "itysl" (Easter egg → random gif)

System prompt is configured in chat.py with personality and Discord-specific constraints (no emojis, compact messages, splits for length limit).
