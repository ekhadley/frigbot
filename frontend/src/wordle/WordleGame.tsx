import { useEffect, useState } from "react"
import type { Session } from "../discord"
import { Board } from "./Board"
import { Spectators } from "./Spectators"
import type { Game, WordlePuzzle, WordleSettings } from "./game"
import { initGame, colorsFor, computeStats, avgBits, DEFAULT_SETTINGS, MAX_GUESSES } from "./game"
import { ANSWERS } from "./words"
import { saveJson, loadJson } from "../storage"
import { useGameRoom } from "../ws"
import { DevTools } from "../DevTools"

const storageKey = (userId: string, date: string) => `wordle:${userId}:${date}`
const SETTINGS_KEY = "wordle:settings"

type Saved = { guesses: string[]; done: "win" | "lose" | null }

export function WordleGame({ session }: { session: Session }) {
  const [game, setGame] = useState<Game | null>(null)
  const [settings, setSettings] = useState<WordleSettings>(
    () => loadJson<WordleSettings>(SETTINGS_KEY) ?? DEFAULT_SETTINGS,
  )

  useEffect(() => {
    saveJson(SETTINGS_KEY, settings)
  }, [settings])

  useEffect(() => {
    ;(async () => {
      const res = await fetch("/api/puzzle/wordle")
      const puzzle = (await res.json()) as WordlePuzzle
      const fresh = initGame(puzzle)
      const isDev = !location.hostname.endsWith("discordsays.com")
      const saved = isDev ? null : loadJson<Saved>(storageKey(session.user.id, puzzle.print_date))
      setGame(saved ? { ...fresh, guesses: saved.guesses, done: saved.done } : fresh)
    })()
  }, [session.user.id])

  const payload = game && {
    guesses: game.guesses.length,
    colors: colorsFor(game),
    words: game.guesses,
    done: game.done !== null,
  }
  const date = game?.puzzle.print_date ?? null
  const players = useGameRoom("wordle", date, session.user, payload)

  // Restore our own board from the server when another device is further along.
  useEffect(() => {
    if (!game || !location.hostname.endsWith("discordsays.com")) return
    const words: string[] | undefined = players[session.user.id]?.words
    if (!words || words.length <= game.guesses.length) return
    const done = words[words.length - 1] === game.solution ? "win" : words.length >= MAX_GUESSES ? "lose" : null
    setGame({ ...game, guesses: words, current: "", done })
  }, [players, game])

  useEffect(() => {
    if (!game) return
    saveJson(storageKey(session.user.id, game.puzzle.print_date), {
      guesses: game.guesses,
      done: game.done,
    })
    if (game.done === "win" && session.guildId) {
      const reportedKey = `wordle:reported:${session.user.id}:${game.puzzle.print_date}`
      if (!localStorage.getItem(reportedKey)) {
        const stats = computeStats(game, ANSWERS)
        const body = {
          guild_id: session.guildId,
          puzzle_date: game.puzzle.print_date,
          user_id: session.user.id,
          username: session.user.global_name ?? session.user.username,
          guesses: game.guesses.length,
          avg_bits: stats ? avgBits(game, stats) : null,
        }
        fetch("/api/wordle/solve", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        })
          .then((r) => {
            if (!r.ok) throw new Error(`solve report failed: ${r.status}`)
            localStorage.setItem(reportedKey, "1")
          })
          .catch((e) => console.error("solve report failed", e))
      }
    }
  }, [game])

  if (!game) return <div className="loading">Loading puzzle…</div>

  return (
    <>
      <Spectators
        players={players}
        selfId={session.user.id}
        selfDone={game.done !== null}
        solution={game.solution}
      />
      <Board game={game} onChange={setGame} settings={settings} onSettingsChange={setSettings} />
      <DevTools session={session} game="wordle" date={date} />
    </>
  )
}
