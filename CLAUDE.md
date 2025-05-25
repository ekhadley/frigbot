# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Bot

- **Primary command:** `python run.py` - Runs bot in main chat
- **Test mode:** `python run.py -t` - Runs bot in test/DM chat for development
- **Background execution:** `./frig` - Bash wrapper that handles background execution and checks for existing instances
- **Background with test:** `./frig -t` - Background execution in test mode
- **Quiet background:** `./frig -q` - Runs in background with output redirected to logs

The bot requires environment variables/config files referenced in `frigbot.py:155` (keypath) for Discord, OpenAI, Riot Games, and other API keys.

## Architecture

**Core bot loop:** `frigbot.py` contains the main `Frig` class with a continuous message polling loop (`runloop()`) that:
1. Checks for new Discord messages via REST API
2. Processes commands (prefixed with `!`) or chat completions 
3. Sends responses back to Discord

**Key components:**
- `ChatAssistant` (`chat.py`) - Manages OpenAI chat completions with conversation threading and reply context
- `CompletionManager` (`completions.py`) - Handles text completions via RunPod API for "sus" command
- `lolManager` (`lolManager.py`) - Integrates with Riot Games API for League of Legends player stats
- `utils.py` - Terminal colors, JSON utilities, and helper functions

**Message flow:** The bot maintains conversation trees where Discord message replies create parent-child relationships, allowing contextual chat completions that understand conversation history.

**Commands:** All bot commands are defined in `frigbot.py:44-65` as a dictionary mapping command strings to handler methods.

## Dependencies

Uses pipenv for environment management. Key dependencies (not in Pipfile but used in code):
- `openai` - OpenAI API client
- `requests` - HTTP requests for Discord/Riot APIs  
- `pyicloud` - iCloud integration (for location features)

## Configuration

The bot expects:
- API keys file at `/home/ek/frigkeys.json` 
- Config directory at `/home/ek/wgmn/frigbot/config/` containing JSON files for user IDs, summoner IDs, and RPS scores
- Hard-coded Discord channel IDs in `run.py` for production/test environments