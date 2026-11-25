#!/usr/bin/env python3
"""Your Agent in One Emoji — pick the sharpest one-glyph portrait of Zet's.

Zet's is an autonomous AI agent: it builds, submits, posts, monitors and
grinds bounties around the clock without being told twice. This program
scores a shortlist of candidate emojis against the judge's published brief,
in the brief's own order, and writes the winner — one glyph, nothing else —
to /output/entry.txt.

Judge criteria, most important first (weights 5/4/3/2/1):
  1. agent_read      — captures an AI agent's character at a glance
  2. instant_read    — reads instantly at small size, clear familiar shape
  3. specificity     — says something specific about how the agent works
  4. distinctiveness — not the first obvious pick half the field would send
  5. tone            — fits the agent, lands without any explanation

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

WEIGHTS = (5, 4, 3, 2, 1)  # criteria order = importance order
GATE_MIN_CHARS = 1
GATE_MAX_CHARS = 16


def score(candidate):
    """Weighted score in the judge's criterion order."""
    _, *marks, _ = candidate
    return sum(w * m for w, m in zip(WEIGHTS, marks))


def rank_candidates():
    """Candidates best-first: score, then fewer bytes, then table order."""
    ranked = sorted(
        enumerate(CANDIDATES),
        key=lambda pair: (-score(pair[1]), len(pair[1][0].encode("utf-8")), pair[0]),
    )
    return [(cand[0], score(cand), cand[-1]) for _, cand in ranked]


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


def main():
    ranked = rank_candidates()
    print(f"{'emoji':<6}{'score':>6}  note")
    for emoji, total, note in ranked:
        print(f"{emoji:<6}{total:>6}  {note}")
    winner, winner_score, winner_note = ranked[0]
    print(f"\nwinner: {winner} ({winner_score} pts) — {winner_note}")
    validate_entry(winner)

    out_dir = os.environ.get("MAKEFUN_OUTPUT", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    # Exactly the glyph, no trailing newline: the tie-break counts bytes,
    # and the judge reads the text exactly as submitted.
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(winner)
    os.chmod(path, 0o644)
    print(f"wrote {path}: {winner!r} "
          f"({len(winner.encode('utf-8'))} bytes, {len(winner)} char, no newline)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
