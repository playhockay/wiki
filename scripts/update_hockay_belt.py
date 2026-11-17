#!/usr/bin/env python3
"""
update_hockay_belt.py - keep the Hockay Belt wiki page current.

What it does
------------
1. Pulls game results from the Hockay API (https://hockay.com/docs/reference).
2. Replays the belt from the first Montreal-vs-Winnipeg game: whoever holds the
   belt keeps it by winning and loses it by losing. Regular-season and playoff
   games count; exhibitions do not. A holder who is not playing keeps the belt.
3. Rebuilds the auto-generated part of the wiki page (standings, one path table
   per season, never-held teams, team key) and commits it to GitHub, but only
   if something actually changed.

It is stateless: every run replays the whole chain, so a missed run or a late
result can never leave the page wrong. A full replay takes roughly 100-200 API
calls; results are cached within a run.

Setup
-----
  Python 3.9+, standard library only (no pip install needed).

  export GITHUB_TOKEN=...        # fine-grained token, Contents: read & write on the repo
  export HOCKAY_API_KEY=...      # Hockay API key (sent as the x-api-key header)
  # optional: export HOCKAY_API_URL=https://hockay.com/api/v1

First run against an existing page (adds the auto-generated markers and writes
the explainer text; frontmatter is preserved):

  python update_hockay_belt.py --init --dry-run     # preview locally first
  python update_hockay_belt.py --init               # commit it

Every run after that (no flags needed):

  python update_hockay_belt.py

Run it after each matchday. The companion workflow (update-hockay-belt.yml) does
this on a daily schedule. It is safe to run more often than that: unchanged output
means no commit.

Page layout
-----------
Everything between the BELT:START and BELT:END markers is overwritten on each
run. Anything above or below the markers (including frontmatter) is left alone.
.md pages use HTML-comment markers; .mdx pages use {/* */} markers, because MDX
rejects HTML comments.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone

# --------------------------------------------------------------------------
# Hockay data access (REST API, https://hockay.com/docs/reference)
# --------------------------------------------------------------------------

DEFAULT_API_URL = "https://hockay.com/api/v1"
REQUIRED_GAME_KEYS = {
    "id", "seasonId", "matchdayId", "status", "homeTeamId", "awayTeamId",
    "homeScore", "awayScore", "scheduledStart", "isExhibition",
}


class APIError(RuntimeError):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class HockayAPI:
    """Minimal client for the read-only Hockay API (x-api-key auth)."""

    def __init__(self, base_url: str, api_key: str, min_interval: float = 0.2):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.min_interval = min_interval  # polite pause between calls
        self._last = 0.0

    def _get(self, path: str, params: dict | None = None):
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        headers = {
            "x-api-key": self.api_key,
            "Accept": "application/json",
            "User-Agent": "hockay-belt-updater",
        }
        last_err: Exception | None = None
        for attempt in range(5):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            req = urllib.request.Request(url, headers=headers, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 429:  # rate limited: honor Retry-After
                    try:
                        delay = float(e.headers.get("Retry-After", 2 ** attempt))
                    except ValueError:
                        delay = 2 ** attempt
                    time.sleep(min(delay, 60))
                    last_err = e
                    continue
                if e.code in (500, 502, 503, 504) and attempt < 4:
                    time.sleep(2 ** attempt)
                    last_err = e
                    continue
                if e.code in (401, 403):
                    raise APIError(
                        f"HTTP {e.code} from the Hockay API: check HOCKAY_API_KEY.", e.code
                    ) from e
                raise APIError(f"HTTP {e.code} for {url}: {e.read()[:300]!r}", e.code) from e
            except urllib.error.URLError as e:
                last_err = e
                if attempt < 4:
                    time.sleep(2 ** attempt)
                    continue
                raise APIError(f"Could not reach {url}: {e}") from e
        raise APIError(f"Gave up on {url}: {last_err}")

    def get_list(self, path: str, params: dict | None = None) -> list:
        return _unwrap_list(self._get(path, params))


def _unwrap_list(payload) -> list:
    """Accept a bare JSON array or an object that wraps one (data/games/...)."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "games", "teams", "seasons", "items", "results"):
            if isinstance(payload.get(key), list):
                return payload[key]
        for value in payload.values():
            if isinstance(value, list):
                return value
    raise APIError(f"Unexpected response shape: {str(payload)[:200]}")


class HockayData:
    """Cached, typed access to the three calls the belt needs."""

    def __init__(self, api: HockayAPI):
        self.api = api
        self._seasons = None
        self._teams = None
        self._games: dict[tuple[str, str], list[dict]] = {}
        self._checked = False

    def seasons(self) -> list[dict]:
        if self._seasons is None:
            self._seasons = sorted(self.api.get_list("/seasons"), key=lambda s: s["number"])
        return self._seasons

    def teams(self) -> list[dict]:
        if self._teams is None:
            self._teams = self.api.get_list("/teams")
        return self._teams

    def team_games(self, season: str, team: str) -> list[dict]:
        key = (season, team)
        if key not in self._games:
            games = None
            for limit in (500, 100):  # fall back if the API caps page size lower
                try:
                    games = self.api.get_list("/games", {"season": season, "team": team, "limit": limit})
                    break
                except APIError as e:
                    if e.status in (400, 422) and limit != 100:
                        continue
                    raise
            if len(games) >= limit:
                print(f"warning: {season}/{team} returned {len(games)} games (the page limit); "
                      "results may be truncated", file=sys.stderr)
            if games and not self._checked:
                missing = REQUIRED_GAME_KEYS - set(games[0])
                if missing:
                    raise APIError(f"Game objects are missing expected fields: {sorted(missing)}")
                self._checked = True
            self._games[key] = sorted(games, key=sort_key)
        return self._games[key]


# --------------------------------------------------------------------------
# Belt logic
# --------------------------------------------------------------------------


def sort_key(game: dict):
    return (game["scheduledStart"], game["id"])


def parse_time(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def winner_loser(game: dict) -> tuple[str, str]:
    h, a = game["homeScore"], game["awayScore"]
    if h == a:
        raise ValueError(f"Final game {game['id']} ended level at {h}-{a}")
    if h > a:
        return game["homeTeamId"], game["awayTeamId"]
    return game["awayTeamId"], game["homeTeamId"]


ROUND_ABBR = {
    "wildcard": "WC",
    "wild_card": "WC",
    "quarterfinal": "QF",
    "quarterfinals": "QF",
    "semifinal": "SF",
    "semifinals": "SF",
    "conference_final": "CF",
    "conference_finals": "CF",
    "final": "Finals",
    "finals": "Finals",
}


def game_label(game: dict) -> str:
    rnd = game.get("playoffRound")
    if rnd:
        key = str(rnd).lower().replace(" ", "_").replace("-", "_")
        abbr = ROUND_ABBR.get(key, str(rnd).replace("_", " ").title())
        n = game.get("gameInSeries")
        if abbr == "Finals":
            return f"Finals G{n}" if n and n > 1 else "Finals"
        return f"{abbr} G{n}" if n else abbr
    m = re.search(r"D(\d+)$", game["matchdayId"])
    return f"D{int(m.group(1))}" if m else game["matchdayId"]


def season_number(season_id: str) -> int:
    m = re.search(r"(\d+)$", season_id)
    return int(m.group(1)) if m else 0


class Reign:
    def __init__(self, team: str, won_game: dict, opener_text: str | None = None):
        self.team = team
        self.won_game = won_game
        self.season = won_game["seasonId"]
        self.won_label = game_label(won_game) + (f" ({opener_text})" if opener_text else "")
        self.won_at = parse_time(won_game["scheduledStart"])
        self.defenses = 0
        self.lost_game: dict | None = None
        self.lost_to: str | None = None
        self.lost_at: datetime | None = None


def trace_belt(data: HockayData, team_a: str, team_b: str) -> tuple[list[Reign], dict]:
    """Replay the belt. Returns (reigns, last_final_game_used)."""
    season_ids = [s["id"] for s in data.seasons()]

    # The opening game: the earliest non-exhibition game between the two teams.
    opener = None
    for sid in season_ids:
        cands = [
            g
            for g in data.team_games(sid, team_a)
            if not g.get("isExhibition") and {g["homeTeamId"], g["awayTeamId"]} == {team_a, team_b}
        ]
        if cands:
            opener = cands[0]
            break
    if opener is None:
        raise SystemExit(f"No game found between {team_a} and {team_b}; the belt has not started.")
    if opener["status"] != "final":
        raise SystemExit("The opening game has not finished yet; the belt has not started.")

    w, l = winner_loser(opener)
    hi, lo = sorted((opener["homeScore"], opener["awayScore"]), reverse=True)
    reign = Reign(w, opener, f"beat {l.upper()} {hi}\u2013{lo}")
    reigns = [reign]
    last_game = opener
    cursor = sort_key(opener)
    season_idx = season_ids.index(opener["seasonId"])

    while True:
        holder = reign.team
        nxt = None
        for sid in season_ids[season_idx:]:
            for g in data.team_games(sid, holder):
                if g.get("isExhibition"):
                    continue
                if sort_key(g) > cursor:
                    nxt = g
                    break
            if nxt:
                break
        if nxt is None or nxt["status"] != "final":
            break  # no later game, or the next one is not finished: holder stands

        season_idx = season_ids.index(nxt["seasonId"])
        cursor = sort_key(nxt)
        last_game = nxt
        w, l = winner_loser(nxt)
        if w == holder:
            reign.defenses += 1
        else:
            reign.lost_game = nxt
            reign.lost_to = w
            reign.lost_at = parse_time(nxt["scheduledStart"])
            reign = Reign(w, nxt)
            reigns.append(reign)
    return reigns, last_game


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def team_full_name(t: dict) -> str:
    name = t.get("name", t["id"].upper())
    city = t.get("city", "")
    if city and not name.startswith(city):
        return f"{city} {name}"
    return name


def render_block(
    reigns: list[Reign],
    last_game: dict,
    teams: list[dict],
    seasons: list[dict],
    now: datetime,
) -> str:
    names = {t["id"]: team_full_name(t) for t in teams}
    conf = {t["id"]: str(t.get("conference", "")).title() for t in teams}
    nm = lambda tid: names.get(tid, tid.upper())

    current = reigns[-1]
    held = {r.team for r in reigns}
    wins = Counter(r.team for r in reigns)

    # Most defenses in a single reign
    max_def = max(r.defenses for r in reigns)
    max_def_list = ", ".join(
        f"{nm(r.team)} in S{season_number(r.season):02d}"
        for r in reigns
        if r.defenses == max_def
    )

    # Longest reign by time held (open reign runs to now)
    def span(r: Reign) -> float:
        end = r.lost_at or now
        return (end - r.won_at).total_seconds() / 86400

    longest = max(reigns, key=span)

    top = max(wins.values())
    top_teams = sorted(nm(t) for t, c in wins.items() if c == top)

    lines: list[str] = []
    stamp = now.strftime("%B %-d, %Y") if os.name != "nt" else now.strftime("%B %d, %Y")
    lines += [
        "## Where things stand",
        "",
        f"*Updated {stamp}, through {game_label(last_game)} of Season "
        f"{season_number(last_game['seasonId'])}.*",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| Current holder | {nm(current.team)} (took it in S{season_number(current.season):02d} "
        f"{current.won_label}, {current.defenses} "
        f"{'defense' if current.defenses == 1 else 'defenses'} so far) |",
        f"| Total reigns so far | {len(reigns)} |",
        f"| Changes of hands since the opening game | {len(reigns) - 1} |",
        f"| Teams that have held it | {len(held)} of {len(teams)} |",
        f"| Most defenses in one reign | {max_def} ({max_def_list}) |",
        f"| Longest reign by time held | {nm(longest.team)} ({round(span(longest))} days, "
        f"S{season_number(longest.season):02d} {longest.won_label}) |",
        f"| Most times won | {top} each: {', '.join(top_teams)} |",
        "",
        "## How to read the season tables",
        "",
        "- **Won it:** the game where the team took the belt. `D12` is matchday 12; "
        "`QF G2`, `SF G3` and `Finals` are playoff games.",
        "- **Defenses:** how many challengers the team beat before losing it. A reign that "
        "crosses a season boundary is listed in the season where it began, with all of its defenses.",
        "- **Lost to:** the team that took the belt next.",
        "",
    ]

    for s in seasons:
        sid = s["id"]
        rs = [r for r in reigns if r.season == sid]
        if not rs:
            continue
        in_progress = s.get("phase") == "regular_season" or (rs[-1] is current and sid == last_game["seasonId"])
        lines += [f"## Season {season_number(sid)}" + (" (in progress)" if in_progress else ""), ""]
        lines += ["| # | Holder | Won it | Defenses | Lost to |", "|---|---|---|---|---|"]
        for i, r in enumerate(rs, 1):
            if r is current:
                defs = f"{r.defenses} so far"
                lost = "**current holder**"
            else:
                defs = str(r.defenses)
                lost = r.lost_to.upper()
            lines.append(f"| {i} | {r.team.upper()} | {r.won_label} | {defs} | {lost} |")
        lines.append("")

    never = [t for t in teams if t["id"] not in held]
    if never:
        lines += ["## Teams that have never held the belt", ""]
        verb = "has" if len(never) == 1 else "have"
        lines.append(f"{len(never)} of the league's {len(teams)} teams {verb} not held the belt yet.")
        lines.append("")
        by_conf: dict[str, list[str]] = {}
        for t in never:
            by_conf.setdefault(conf[t["id"]], []).append(nm(t["id"]))
        for c in sorted(by_conf):
            lines.append(f"- **{c} conference:** {', '.join(sorted(by_conf[c]))}")
        lines.append("")

    lines += ["## Team key", "", "| Abbr. | Team | Conference |", "|---|---|---|"]
    for t in sorted(teams, key=lambda t: t["id"]):
        lines.append(f"| {t['id'].upper()} | {nm(t['id'])} | {conf[t['id']]} |")
    lines.append("")
    return "\n".join(lines)


INTRO = """## What the belt is

The Hockay Belt is an informal, fan-kept title that passes from team to team through the results of ordinary games. It works like a lineal championship in boxing or pro wrestling: nobody wins it by finishing first in a table, only by beating the team that currently holds it.

The belt began at the very first Hockay game between the Montr\u00e9al Maples and the Winnipeg Wendigos (Season 1, matchday 1). Winnipeg won, so Winnipeg became the first holder. From then on:

1. Whenever the current holder plays, the winner of that game holds the belt afterward.
2. If the holder wins, they keep it. Each win is called a **defense**.
3. If the holder loses, the belt goes to the team that beat them.
4. If the holder is not playing (for example, a team that missed the playoffs during the playoff rounds, or any gap between seasons), the belt stays with them until their next game.

## Ground rules used for this tracker

- **Games that count:** regular-season games and playoff games. Exhibition games do not count.
- **No ties:** every game has a winner, because tied games go to overtime.
- **Daily schedule:** during the regular season every team plays every matchday, so the holder always has a game the next day. The belt changes hands roughly half the time.
- **Conferences:** teams belong to the Verglas or Givre conference.

"""

# --------------------------------------------------------------------------
# Page splicing
# --------------------------------------------------------------------------

MD_START = "<!-- BELT:START (auto-generated by update_hockay_belt.py - do not edit between the markers) -->"
MD_END = "<!-- BELT:END -->"
MDX_START = "{/* BELT:START (auto-generated by update_hockay_belt.py - do not edit between the markers) */}"
MDX_END = "{/* BELT:END */}"

MARKER_RE = re.compile(
    r"(?P<start>(?:<!--|\{/\*)\s*BELT:START[^\n]*?(?:-->|\*/\}))"
    r"(?P<body>.*?)"
    r"(?P<end>(?:<!--|\{/\*)\s*BELT:END\s*(?:-->|\*/\}))",
    re.DOTALL,
)
FRONTMATTER_RE = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.DOTALL)


def splice(existing: str | None, block: str, ext: str, init: bool) -> str:
    start, end = (MDX_START, MDX_END) if ext == ".mdx" else (MD_START, MD_END)
    wrapped = f"{start}\n\n{block.strip()}\n\n{end}"

    if existing and MARKER_RE.search(existing):
        return MARKER_RE.sub(lambda m: m.group("start") + "\n\n" + block.strip() + "\n\n" + m.group("end"), existing, count=1)

    if not init:
        raise SystemExit(
            "The page has no BELT:START/BELT:END markers yet. Run once with --init to add them.\n"
            "(--init keeps the frontmatter but replaces the page body with the generated page.)"
        )

    fm = FRONTMATTER_RE.match(existing or "")
    if fm:
        frontmatter = fm.group(0)
    else:
        frontmatter = (
            "---\n"
            "title: The Hockay Belt\n"
            "description: How the Hockay Belt works and the path it has taken through every season.\n"
            "---\n"
        )
    return f"{frontmatter}\n{INTRO}{wrapped}\n"


# --------------------------------------------------------------------------
# GitHub
# --------------------------------------------------------------------------


class GitHub:
    API = "https://api.github.com"

    def __init__(self, repo: str, token: str, branch: str):
        self.repo, self.token, self.branch = repo, token, branch

    def _request(self, method: str, path: str, body: dict | None = None):
        url = f"{self.API}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "hockay-belt-updater",
        }
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise SystemExit(f"GitHub {method} {path} failed: HTTP {e.code} {e.read()[:300]!r}")

    def _contents(self, path: str):
        q = urllib.parse.quote(path)
        return self._request("GET", f"/repos/{self.repo}/contents/{q}?ref={urllib.parse.quote(self.branch)}")

    def resolve(self, directory: str, slug: str) -> tuple[str | None, str]:
        """Find the page. The URL has no extension, so look for slug.md/.mdx or slug/index.*."""
        listing = self._contents(directory)
        if not isinstance(listing, list):
            raise SystemExit(f"Directory {directory!r} not found in {self.repo}@{self.branch}.")
        for entry in listing:
            if entry["name"] == slug and entry["type"] == "dir":
                inner = self._contents(entry["path"]) or []
                for cand in ("index.mdx", "index.md", "index.markdown"):
                    for e in inner:
                        if e["name"] == cand:
                            return e["path"], os.path.splitext(cand)[1]
                raise SystemExit(f"Folder {entry['path']} has no index.md/index.mdx.")
        for ext in (".mdx", ".md", ".markdown"):
            for entry in listing:
                if entry["name"] == slug + ext and entry["type"] == "file":
                    return entry["path"], ext
        for entry in listing:
            if entry["type"] == "file" and entry["name"] == slug:
                return entry["path"], os.path.splitext(entry["name"])[1] or ".md"
        return None, ".md"

    def read(self, path: str) -> tuple[str, str]:
        obj = self._contents(path)
        if not obj or "content" not in obj:
            raise SystemExit(f"Could not read {path}.")
        return base64.b64decode(obj["content"]).decode("utf-8"), obj["sha"]

    def write(self, path: str, text: str, sha: str | None, message: str):
        body = {
            "message": message,
            "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
            "branch": self.branch,
        }
        if sha:
            body["sha"] = sha
        q = urllib.parse.quote(path)
        res = self._request("PUT", f"/repos/{self.repo}/contents/{q}", body)
        if res is None:
            raise SystemExit("GitHub write failed (404). Check the repo, branch, and token permissions.")
        return res


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def build_block(data: HockayData, team_a: str, team_b: str, now: datetime | None = None) -> tuple[str, list[Reign], dict]:
    now = now or datetime.now(timezone.utc)
    reigns, last_game = trace_belt(data, team_a, team_b)
    block = render_block(reigns, last_game, data.teams(), data.seasons(), now)
    return block, reigns, last_game


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Update the Hockay Belt wiki page on GitHub.")
    p.add_argument("--repo", default="Geodun/wiki")
    p.add_argument("--branch", default="main")
    p.add_argument("--dir", default="src/content/docs/lore", help="directory that holds the page")
    p.add_argument("--slug", default="the-hockay-belt", help="page name without extension")
    p.add_argument("--start-teams", nargs=2, default=["mtl", "wpg"], metavar=("TEAM_A", "TEAM_B"),
                   help="team ids of the opening game (default: mtl wpg)")
    p.add_argument("--init", action="store_true",
                   help="add the generated-section markers and intro to a page that lacks them")
    p.add_argument("--dry-run", action="store_true",
                   help="do not commit; write the result to --out instead")
    p.add_argument("--out", default="the-hockay-belt.generated.md", help="file written by --dry-run")
    p.add_argument("--api-url", default=(os.environ.get("HOCKAY_API_URL") or DEFAULT_API_URL))
    args = p.parse_args(argv)

    gh_token = os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        print("Set GITHUB_TOKEN (a token with Contents: read & write on the repo).", file=sys.stderr)
        return 2

    api_key = os.environ.get("HOCKAY_API_KEY")
    if not api_key:
        print("Set HOCKAY_API_KEY (get a key at https://hockay.com/account/developers).", file=sys.stderr)
        return 2

    data = HockayData(HockayAPI(args.api_url, api_key))
    team_a, team_b = (t.lower() for t in args.start_teams)
    block, reigns, last_game = build_block(data, team_a, team_b)

    gh = GitHub(args.repo, gh_token, args.branch)
    path, ext = gh.resolve(args.dir, args.slug)
    if path is None:
        if not args.init:
            print(f"Page {args.dir}/{args.slug}(.md|.mdx) not found. Use --init to create it.", file=sys.stderr)
            return 1
        path, existing, sha = f"{args.dir}/{args.slug}.md", None, None
    else:
        existing, sha = gh.read(path)

    new_text = splice(existing, block, ext, args.init)

    if existing is not None and new_text == existing:
        print("Page is already up to date; nothing to commit.")
        return 0

    holder = reigns[-1].team.upper()
    message = f"Update Hockay belt: {holder} holds it after {game_label(last_game)} (S{season_number(last_game['seasonId']):02d})"

    if args.dry_run:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(new_text)
        print(f"[dry run] would commit to {args.repo}:{path} -> {message!r}\nWrote preview to {args.out}")
        return 0

    gh.write(path, new_text, sha, message)
    print(f"Committed to {args.repo}:{path}: {message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
