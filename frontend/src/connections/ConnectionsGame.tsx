import { useEffect, useState } from "react"
import type { Session } from "../discord"
import { Board } from "./Board"
import { Spectators } from "./Spectators"
import type { Game, Puzzle, Solved } from "./game"
import { initGame, submit, toggle, shuffle, revealNext, seededShuffle, MAX_MISTAKES } from "./game"
import { saveJson, loadJson } from "../storage"
import { useGameRoom } from "../ws"
import { DevTools } from "../DevTools"

const storageKey = (userId: string, date: string) => `connections:${userId}:${date}`

function hydrate(game: Game, mine: any): Game {
  const solved: Solved[] = mine.solved.map((s: { level: number }) => {
    const g = game.puzzle.answers.find((a) => a.level === s.level)!
    return { level: g.level, group: g.group, members: g.members }
  })
  const solvedMembers = new Set(solved.flatMap((s) => s.members))
  const all = game.puzzle.answers.flatMap((a) => a.members)
  const remaining = seededShuffle(all, game.puzzle.id).filter((w) => !solvedMembers.has(w))
  const done = solved.length === 4 ? "win" : mine.mistakes >= MAX_MISTAKES ? "lose" : null
  return { ...game, attempts: mine.attempts, solved, remaining, mistakes: mine.mistakes, done, selected: [] }
}

function mergeSaved(fresh: Game, saved: Partial<Game> | null): Game {
  if (!saved) return fresh
  return {
    ...fresh,
    attempts: saved.attempts ?? [],
    solved: saved.solved ?? [],
    mistakes: saved.mistakes ?? 0,
    done: saved.done ?? null,
    remaining: saved.remaining ?? fresh.remaining,
  }
}

export function ConnectionsGame({ session }: { session: Session }) {
  const [game, setGame] = useState<Game | null>(null)

  useEffect(() => {
    ;(async () => {
      const res = await fetch("/api/puzzle/connections")
      const puzzle = (await res.json()) as Puzzle
      const fresh = initGame(puzzle)
      const isDev = !location.hostname.endsWith("discordsays.com")
      const saved = isDev ? null : loadJson<Partial<Game>>(storageKey(session.user.id, puzzle.date))
      setGame(mergeSaved(fresh, saved))
    })()
  }, [session.user.id])

  const payload = game && {
    attempts: game.attempts.map((a) => ({ words: a.words, levels: a.levels, correct: a.correct })),
    solved: game.solved.map((x) => ({ level: x.level })),
    mistakes: game.mistakes,
    done: game.done !== null,
  }
  const date = game?.puzzle.date ?? null
  const players = useGameRoom("connections", date, session.user, payload)

  // Restore our own board from the server when another device is further along.
  useEffect(() => {
    if (!game || !location.hostname.endsWith("discordsays.com")) return
    const mine = players[session.user.id]
    if (!mine?.attempts || mine.attempts.length <= game.attempts.length) return
    setGame(hydrate(game, mine))
  }, [players, game])

  useEffect(() => {
    if (!game) return
    saveJson(storageKey(session.user.id, game.puzzle.date), {
      attempts: game.attempts,
      solved: game.solved,
      mistakes: game.mistakes,
      done: game.done,
      remaining: game.remaining,
    })
  }, [game])

  if (!game) return <div className="loading">Loading puzzle…</div>

  return (
    <>
      <Spectators players={players} selfId={session.user.id} />
      <Board
        game={game}
        onToggle={(w) => setGame(toggle(game, w))}
        onSubmit={() => setGame(submit(game))}
        onShuffle={() => setGame(shuffle(game))}
        onDeselect={() => setGame({ ...game, selected: [] })}
        onReorder={(newRemaining) => setGame({ ...game, remaining: newRemaining })}
        onReveal={() => setGame(revealNext(game))}
      />
      <DevTools session={session} game="connections" date={date} />
    </>
  )
}
