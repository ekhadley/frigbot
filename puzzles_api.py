import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import streaks_db

CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "")
CONNECTIONS_MIRROR = "https://raw.githubusercontent.com/Eyefyre/NYT-Connections-Answers/main/connections.json"
WORDLE_URL = "https://www.nytimes.com/svc/wordle/v2/{date}.json"
ET = ZoneInfo("America/New_York")

FRONTEND_DIR = Path(__file__).parent / "frontend" / "dist"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def today_et() -> str:
    return datetime.now(ET).date().isoformat()


def yesterday_et() -> str:
    return (datetime.now(ET).date() - timedelta(days=1)).isoformat()


_connections_cache: dict[str, dict] = {}
_wordle_cache: dict[str, dict] = {}


async def fetch_connections(date_str: str) -> dict:
    if date_str in _connections_cache:
        return _connections_cache[date_str]
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(CONNECTIONS_MIRROR)
        r.raise_for_status()
        data = r.json()
    match = next((p for p in data if p["date"] == date_str), None)
    if match is None:
        raise RuntimeError(f"no connections puzzle for {date_str} in mirror")
    for i, a in enumerate(match["answers"]):
        a["level"] = i
    _connections_cache.clear()
    _connections_cache[date_str] = match
    return match


async def fetch_wordle(date_str: str) -> dict:
    if date_str in _wordle_cache:
        return _wordle_cache[date_str]
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0"}) as client:
        r = await client.get(WORDLE_URL.format(date=date_str))
        r.raise_for_status()
        data = r.json()
    if "solution" not in data:
        raise RuntimeError(f"wordle response missing 'solution' for {date_str}: {data}")
    _wordle_cache.clear()
    _wordle_cache[date_str] = data
    return data


@app.get("/api/puzzle/connections")
async def get_connections():
    return await fetch_connections(today_et())


@app.get("/api/puzzle/wordle")
async def get_wordle():
    return await fetch_wordle(today_et())


class TokenReq(BaseModel):
    code: str


@app.post("/api/token")
async def exchange_token(req: TokenReq):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": req.code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        return {"access_token": r.json()["access_token"]}


class SolveReq(BaseModel):
    guild_id: str
    puzzle_date: str
    user_id: str
    username: str | None = None
    guesses: int
    avg_bits: float | None = None


@app.post("/api/wordle/solve")
async def post_solve(req: SolveReq):
    await asyncio.to_thread(
        streaks_db.record_solve,
        req.guild_id, req.puzzle_date, req.user_id, req.username, req.guesses, req.avg_bits,
    )
    return {"ok": True}


class DeleteBoardReq(BaseModel):
    game: str
    puzzle_date: str
    user_id: str


class Room:
    def __init__(self, players: dict[str, dict]):
        self.sockets: set[WebSocket] = set()
        self.players = players

    async def broadcast(self):
        payload = {"type": "state", "players": self.players}
        dead = []
        for ws in self.sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.sockets.discard(ws)


rooms: dict[tuple[str, str], Room] = {}


@app.post("/api/board/delete")
async def delete_board(req: DeleteBoardReq):
    await asyncio.to_thread(streaks_db.delete_board, req.game, req.puzzle_date, req.user_id)
    room = rooms.get((req.game, req.puzzle_date))
    if room is not None:
        room.players.pop(req.user_id, None)
        await room.broadcast()
    return {"ok": True}


def _progress(player: dict) -> tuple[int, int]:
    """Monotonic rank of a board: finished beats unfinished, then more moves wins.
    Used to ignore stale updates from a second device that's behind."""
    moves = len(player.get("words") or player.get("attempts") or [])
    return (1 if player.get("done") else 0, moves)


async def room_for(game: str, date: str) -> Room:
    key = (game, date)
    if key not in rooms:
        players = await asyncio.to_thread(streaks_db.load_boards, game, date)
        rooms[key] = Room(players)
    return rooms[key]


@app.websocket("/ws/{game}/{puzzle_date}")
async def ws_presence(ws: WebSocket, game: str, puzzle_date: str):
    if game not in ("connections", "wordle"):
        await ws.close(code=1008)
        return
    await ws.accept()
    room = await room_for(game, puzzle_date)
    room.sockets.add(ws)
    await ws.send_json({"type": "state", "players": room.players})
    try:
        while True:
            msg = await ws.receive_json()
            if msg.get("type") == "update":
                uid = msg["user"]["id"]
                player = {k: v for k, v in msg.items() if k != "type"}
                current = room.players.get(uid)
                if current is not None and _progress(player) < _progress(current):
                    continue  # a behind device (e.g. other phone) can't regress presence
                room.players[uid] = player
                await asyncio.to_thread(streaks_db.save_board, game, puzzle_date, uid, player)
                await room.broadcast()
    except WebSocketDisconnect:
        room.sockets.discard(ws)
        if not room.sockets:
            rooms.pop((game, puzzle_date), None)


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")
