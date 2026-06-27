import type { Session } from "./discord"
import type { GameKind } from "./ws"

// Guest sessions (website dev) share the same backend rooms as the real Discord
// activity, so their boards leak into spectators for normal users. This button
// purges the guest's persisted board for the current game/date.
export function DevTools({ session, game, date }: { session: Session; game: GameKind; date: string | null }) {
  if (session.sdk !== null || !date) return null

  const clearData = async () => {
    const r = await fetch("/api/board/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game, puzzle_date: date, user_id: session.user.id }),
    })
    if (!r.ok) throw new Error(`clear failed: ${r.status}`)
  }

  return (
    <div className="dev-tools">
      <button onClick={clearData}>Clear my guest data</button>
    </div>
  )
}
