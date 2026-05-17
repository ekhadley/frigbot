import type { Color } from "./game"
import { MAX_GUESSES, WORD_LEN, statsForGuesses, annotateStats } from "./game"
import { ANSWERS } from "./words"

type PlayerState = {
  user: { id: string; username: string; avatar: string | null; global_name?: string | null }
  colors: Color[][]
  words?: string[]
  guesses: number
  done: boolean
}

const COLOR_BG: Record<Color, string> = { g: "#538d4e", y: "#b59f3b", _: "#3a3a3c" }

function avatarUrl(user: PlayerState["user"]): string {
  if (user.avatar) return `https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png?size=64`
  const idx = Number(BigInt(user.id) >> 22n) % 6
  return `https://cdn.discordapp.com/embed/avatars/${idx}.png`
}

function annotationsFor(words: string[], solution: string, won: boolean): string[] {
  if (!words.length) return []
  return annotateStats(statsForGuesses(words, solution, ANSWERS), won)
}

export function Spectators({
  players,
  selfId,
  selfDone,
  solution,
}: {
  players: Record<string, PlayerState>
  selfId: string
  selfDone: boolean
  solution: string
}) {
  const others = Object.values(players).filter((p) => p.user.id !== selfId)

  return (
    <aside className="spectators">
      {others.map((p) => {
        const words = p.words ?? []
        const revealed = selfDone && words.length > 0
        const annotations = revealed ? annotationsFor(words, solution, p.done && words[words.length - 1] === solution) : []
        return (
          <div key={p.user.id} className="spec">
            <div className="spec-head">
              <img src={avatarUrl(p.user)} alt="" />
              <span className="name">{p.user.global_name ?? p.user.username}</span>
              {p.done && <span className="badge">{words[words.length - 1] === solution ? `${words.length}/6` : "X/6"}</span>}
            </div>
            {revealed ? (
              <div className="spec-board">
                {Array.from({ length: MAX_GUESSES }).map((_, i) => {
                  const row = p.colors[i]
                  const word = words[i] ?? ""
                  return (
                    <div key={i} className="spec-board-row">
                      {Array.from({ length: WORD_LEN }).map((_, j) => (
                        <div
                          key={j}
                          className="spec-board-cell"
                          style={row ? { background: COLOR_BG[row[j]], borderColor: COLOR_BG[row[j]] } : undefined}
                        >
                          {word[j] ?? ""}
                        </div>
                      ))}
                      {annotations[i] && <div className="spec-board-annotation">{annotations[i]}</div>}
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="wordle-mini">
                {Array.from({ length: MAX_GUESSES }).map((_, i) => {
                  const row = p.colors[i]
                  return (
                    <div key={i} className="wordle-mini-row">
                      {Array.from({ length: WORD_LEN }).map((_, j) => (
                        <span
                          key={j}
                          className="pip"
                          style={{ background: row ? COLOR_BG[row[j]] : "transparent", border: row ? "none" : "1px solid #3f4147" }}
                        />
                      ))}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )
      })}
    </aside>
  )
}
