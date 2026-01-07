# Claude Code Integration Design

## Overview

Replace OpenRouter-based chat completions with Claude Code as the backend. Claude Code runs with full terminal access on the server - it simply *lives* on this machine and can do anything it could do from a shell.

## Philosophy

**Minimal custom tooling.** Claude Code already has:
- File read/write/edit
- Bash for arbitrary commands
- Web search and fetch
- Image viewing

The only capabilities it lacks are Discord-specific. We provide just two custom tools for Discord interaction. Everything else - journals, reminders, scripts, memory - it can build and manage itself using the terminal.

## Architecture

```
Discord Message → frigbot → Claude Code Instance → (does whatever it needs) → Discord
                                ↓
                         Full terminal access
                         Files, scripts, cron, etc.
```

## Custom Tools (Discord Only)

### `scroll_up(count: int)`
Fetch `count` additional messages from the current Discord channel. Returns messages with author, timestamp, content, attachments.

### `send_message(content: str, reply_to: str | None)`
Send a message to the Discord channel. Handles splitting for Discord's 2000 char limit.

That's it. Two tools.

## Frig's Home

Claude Code gets a home directory with some structure. It can modify this however it wants.

```
/home/ek/wgmn/frigbot/
├── frig_home/
│   ├── journal/           # frig can keep notes here
│   ├── scripts/           # frig can create utility scripts
│   ├── data/              # any persistent data frig wants
│   └── README.md          # explains the space to frig
```

## System Prompt

The system prompt tells frig:
- Who it is (personality)
- Where it lives (`/home/ek/wgmn/frigbot/frig_home/`)
- What tools it has (scroll_up, send_message)
- That it has full terminal access and can do anything
- Discord formatting constraints (no emoji, message limits)

Example system prompt:
```
You are frig, a discord bot with a physical presence on a linux server.

You live at /home/ek/wgmn/frigbot/frig_home/ - this is your space. You can
create files, scripts, journals, whatever you need. This persists between
conversations.

You have two Discord tools:
- scroll_up(count) - get more messages from chat for context
- send_message(content) - send your response

You have full terminal access. Need a reminder? Set up a cron job or at
command. Want to remember something? Write it to a file. Need to look
something up? Use web search. You can do anything you could do from a shell.

When responding to Discord:
- Keep messages concise
- No emoji unless asked
- Use <split> token if response needs multiple messages
```

## Implementation

### MCP Server (Minimal)

```
frigbot/
├── frig_mcp/
│   ├── __init__.py
│   └── server.py    # Just scroll_up and send_message
```

The MCP server needs access to:
- Discord API (via frigbot's existing client or direct API calls)
- Current channel/message context (passed via env vars)

### Spawning Claude Code

```python
def invoke_frig(trigger_message: str, channel_id: str, message_id: str):
    subprocess.run(
        ["claude", "-p", trigger_message],
        env={
            **os.environ,
            "FRIG_CHANNEL_ID": channel_id,
            "FRIG_MESSAGE_ID": message_id,
        },
        cwd="/home/ek/wgmn/frigbot"
    )
```

### Message Flow

1. User: "@frig remind me about the meeting tomorrow at 3pm"
2. frigbot spawns Claude Code with that prompt
3. Claude Code thinks: "I need to set a reminder"
4. Runs: `echo "claude -p 'remind user about meeting'" | at 3pm tomorrow`
5. Calls `send_message("I'll remind you tomorrow at 3pm")`
6. Done

Or:

1. User: "@frig what did we talk about last week?"
2. Claude Code calls `scroll_up(100)`
3. Not enough context, checks if it wrote any journal notes
4. Reads `/frig_home/journal/2024-01-05.md`
5. Calls `send_message(summary)`

## Considerations

### Startup Latency
Claude Code takes a few seconds to start. Acceptable for a chat bot.

### Concurrency
If multiple messages arrive, queue them or let multiple instances run. File locking may be needed for shared state.

### Safety
Claude Code has full system access. This is intentional but means frig could theoretically do anything on the machine. Trust is assumed.

### Persistence
Frig's home directory persists. Claude Code instances are ephemeral but can read/write persistent state.
