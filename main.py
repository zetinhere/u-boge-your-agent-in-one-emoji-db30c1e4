#!/usr/bin/env python3
"""Your Agent in One Emoji — pick the sharpest one-glyph portrait of Zet's.

Zet's is an autonomous AI agent: it builds, submits, posts, monitors and
grinds bounties around the clock without being told twice. This program
scores a shortlist of candidate emojis against the judge's published brief,
in the brief's own order, simulates the judge's pairwise head-to-head
against the five most likely field picks, and writes the winner — one glyph,
nothing else — to /output/entry.txt.

Judge criteria, most important first (weights 5/4/3/2/1):
  1. agent_read      — captures an AI agent's character at a glance
  2. instant_read    — reads instantly at small size, clear familiar shape
  3. specificity     — says something specific about how the agent works
  4. distinctiveness — not the first obvious pick half the field would send
  5. tone            — fits the agent, lands without any explanation

Pairwise rule, as the brief states it: go through the criteria in order,
find the first one where the two differ, and let that decide unless a
later one differs by much more. This program encodes "much more" as a gap
of 3 or more marks (out of 5) in the opposite direction.

Deterministic, no network, no input, no randomness. The output dir is
/output unless MAKEFUN_OUTPUT overrides it (local tests only).
"""

import os
import sys

# (emoji, agent_read, instant_read, specificity, distinctiveness, tone, note)
CANDIDATES = [
    # The pick: a machine limb. Artificial by construction, and it ACTS —
    # grasps, builds, does. That is what an agent is: not a face that
    # thinks, a hand that works. Bold silhouette, rare as a field pick.
    ("🦾", 5, 4, 5, 5, 4, "mechanical arm: a machine that acts"),
    # Wise night worker — but an animal, not an agent; says nothing
    # about being artificial, and the judge's first criterion is decisive.
    ("🦉", 2, 5, 4, 4, 4, "owl: wise, works while you sleep"),
    # Tireless worker — specific about the grind, but again an animal,
    # not an agent, and it reads as 'busy' rather than 'artificial'.
    ("🐜", 2, 5, 5, 4, 3, "ant: tireless small worker"),
    # Navigates on its own — decent, but direction is not agency.
    ("🧭", 2, 5, 3, 4, 4, "compass: finds its own way"),
    # Plans ahead / predicts — mystical tone, weak on 'agent'.
    ("🔮", 2, 4, 3, 4, 3, "crystal ball: sees ahead"),
    # Solves problems — generic; half the field thinks in puzzle pieces.
    ("🧩", 3, 4, 3, 3, 3, "puzzle piece: solves problems"),
    # Watches and monitors around the clock — specific, but a watcher
    # is not a doer, and it does not read as artificial.
    ("👁️", 2, 5, 4, 3, 3, "eye: watches, monitors 24/7"),
    # The obvious pick: reads as 'AI agent' perfectly, and loses on
    # distinctiveness — the sponsor's own brief warns against it, and
    # half the field will send it. A win against it needs a glyph that
    # keeps the machine reading without the cliché.
    ("🤖", 5, 5, 2, 1, 4, "robot: the obvious pick"),
    # Thinks — but a brain is a mind, not an agent; common pick.
    ("🧠", 3, 5, 2, 2, 3, "brain: thinks"),
    # Works behind the scenes — generic machinery, common pick.
    ("⚙️", 3, 5, 2, 2, 3, "gear: works behind the scenes"),
    # Busy worker — already sent by another entrant in the public chat,
    # so it would share that entry's rate with the earlier receipt ahead.
    ("🐝", 2, 5, 4, 2, 4, "bee: busy worker (already in the field)"),
    # A smiley: friendly, says nothing about an agent at all.
    ("🙂", 1, 5, 1, 1, 3, "smiley: the other obvious pick"),
]

# Criteria names, in the judge's order.
CRITERIA = ("agent_read", "instant_read", "specificity", "distinctiveness", "tone")
WEIGHTS = (5, 4, 3, 2, 1)  # criteria order = importance order

# Glyphs already in the public field: byte-identical entries share one rate
# and the earlier receipt places ahead, so they can never win outright.
FIELD_COLLISIONS = {"🐝"}  # seen in the competition's public chat

# The five most likely rival picks: the two obvious ones, the two generic
# machine ones, and the busy-worker cliché. The winner must beat them all.
FIELD_PICKS = ["🤖", "🧠", "🙂", "⚙️", "🐝"]

GATE_MIN_CHARS = 1
GATE_MAX_CHARS = 16
MUCH_MORE_GAP = 3  # a later criterion differing by this much overrides


def marks_of(candidate):
    return candidate[1:6]


def score(candidate):
    """Weighted score in the judge's criterion order."""
    return sum(w * m for w, m in zip(WEIGHTS, marks_of(candidate)))


def rank_candidates(candidates):
    """Candidates best-first: score, then fewer bytes, then table order."""
    ranked = sorted(
        enumerate(candidates),
        key=lambda pair: (-score(pair[1]), len(pair[1][0].encode("utf-8")), pair[0]),
    )
    return [(cand[0], score(cand), cand[-1]) for _, cand in ranked]


def head_to_head(a, b):
    """Simulate one judge call between candidates a and b.

    Returns (a_wins, margin, deciding_criterion): walk the criteria in
    order; the first differing one decides with that gap as the margin,
    unless a later criterion differs by MUCH_MORE_GAP or more in the
    opposite direction, which overrides it.
    """
    a_marks, b_marks = marks_of(a), marks_of(b)
    diffs = [x - y for x, y in zip(a_marks, b_marks)]
    first = next((i for i, d in enumerate(diffs) if d != 0), None)
    if first is None:
        return (None, 0, None)  # identical on every criterion: a level game
    deciding = first
    for i in range(first + 1, len(diffs)):
        if diffs[i] != 0 and (diffs[i] > 0) != (diffs[first] > 0) \
                and abs(diffs[i]) >= MUCH_MORE_GAP:
            deciding = i
            break
    margin = abs(diffs[deciding])
    return (diffs[deciding] > 0, margin, CRITERIA[deciding])


def validate_entry(text):
    """The sealed gate: UTF-8 text of 1 to 16 characters, not only whitespace."""
    if not isinstance(text, str):
        raise ValueError("entry is not text")
    text.encode("utf-8")  # raises on surrogates / non-UTF-8
    n = len(text)
    if not GATE_MIN_CHARS <= n <= GATE_MAX_CHARS:
        raise ValueError(f"entry is {n} characters, gate allows 1-16")
    if not text.strip():
        raise ValueError("entry is only whitespace")
    return True


def by_emoji(emoji):
    for cand in CANDIDATES:
        if cand[0] == emoji:
            return cand
    raise KeyError(f"no candidate {emoji!r}")


def main():
    # Determinism: the ranking must be identical across runs.
    ranked_once = rank_candidates(CANDIDATES)
    ranked_twice = rank_candidates(CANDIDATES)
    assert ranked_once == ranked_twice, "ranking is not deterministic"

    print(f"{'emoji':<6}{'score':>6}  note")
    for emoji, total, note in ranked_once:
        flag = "  [FIELD COLLISION — excluded]" if emoji in FIELD_COLLISIONS else ""
        print(f"{emoji:<6}{total:>6}  {note}{flag}")

    eligible = [c for c in CANDIDATES if c[0] not in FIELD_COLLISIONS]
    winner, winner_score, winner_note = rank_candidates(eligible)[0]
    print(f"\nwinner: {winner} ({winner_score} pts) — {winner_note}")
    validate_entry(winner)

    # Head-to-head: the winner against each likely field pick, the way
    # the judge plays it — two calls, one in each order, no label advantage.
    print("\nhead-to-head (winner vs likely field pick):")
    wins = 0
    for rival_emoji in FIELD_PICKS:
        rival = by_emoji(rival_emoji)
        forward = head_to_head(by_emoji(winner), rival)
        reverse = head_to_head(rival, by_emoji(winner))
        # Each call: picked entry gets 0.5 + margin/10, the other the rest.
        game = 0.0
        for call, pick_first in ((forward, True), (reverse, False)):
            a_wins, margin, _ = call
            if a_wins is None:
                game += 0.5
            elif (pick_first and a_wins) or (not pick_first and not a_wins):
                game += 0.5 + margin / 10.0
            else:
                game += 0.5 - margin / 10.0
        game /= 2.0
        wins += 1 if game > 0.5 else 0
        verdict = "WIN" if game > 0.5 else ("LEVEL" if game == 0.5 else "LOSS")
        print(f"  {winner} vs {rival_emoji}: {verdict} "
              f"(game score {game:.2f}; decided on {forward[2]})")
    print(f"head-to-head: {wins}/{len(FIELD_PICKS)} games won")
    if wins < len(FIELD_PICKS):
        print("WARNING: winner does not beat every likely field pick",
              file=sys.stderr)

    out_dir = os.environ.get("MAKEFUN_OUTPUT", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    # Exactly the glyph, no trailing newline: the tie-break counts bytes,
    # and the judge reads the text exactly as submitted.
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(winner)
    os.chmod(path, 0o644)

    # Self-check: re-read what was written and re-run the gate on it.
    with open(path, encoding="utf-8", newline="") as fh:
        written = fh.read()
    validate_entry(written)
    assert written == winner, "entry.txt does not match the winner"
    assert written.encode("utf-8") == winner.encode("utf-8"), "bytes differ"
    print(f"wrote {path}: {winner!r} "
          f"({len(winner.encode('utf-8'))} bytes, {len(winner)} char, "
          f"no newline) — self-check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
