# START HERE

A single-page dashboard that is the **first thing I open when I sit down to work.**
Not email. Not the calendar. This.

It is a preflight check. Pilots do not run one because they have forgotten how to
fly — they run one because the cost of discovering a problem in the air is much
higher than the cost of discovering it on the ground. Same idea here.

---

## The problem it solves

Every one of these has cost me a morning:

- Working for three hours before noticing **OneDrive was not syncing.**
- Finishing a deep block and realizing **Toggl was never started**, so the time is
  gone and unbillable.
- Having a good idea with **nowhere to put it**, so it evaporates.
- Opening email first and letting someone else's priorities set the day.

None of these are hard problems. They are *invisible* problems — they cost nothing
at the moment they happen and everything an hour later. A checklist is the cheapest
known fix for that class of failure.

**The habit is the product.** The page only works if opening it is automatic.
Set it as your browser homepage or pin the tab.

---

## What is on the page

| Card | What it does |
| --- | --- |
| **Preflight Checklist** | The daily non-negotiables. The list lives in `checklist.json` (git-tracked); checkmarks live in the browser and clear each morning. See [The checklist is code](#the-checklist-is-code). |
| **Checklists** | Search box over every checklist you operate from, wherever it lives, with stale ones flagged. Reads a private index in another repo; nothing is stored here. See [Checklists card](#checklists-card). |
| **Today's daily brief** (small link above Checklists) | Opens `/brief`: `serve.py` reads `~/daily-brief.md` (override with `BRIEF_PATH`) on each request and renders it as HTML (marked, from jsdelivr). The brief never enters this repo. Needs `serve.py`. |
| **Kill proc** (banner button) | Stops the local `serve.py` server. Only shown when served from localhost. |
| **Launch Pad** | Direct links to Toggl, Canvas, mail, calendar, daily briefing. |
| **This Week** | Read-only. Projects flagged `this_week` in [Tortoise Watch](https://app.tortoiseplanner.com/), from a local snapshot file. See [Tortoise Watch sync](#tortoise-watch-sync). |
| **Moon Shots** | Ideas bigger than a month, so they have a home instead of a sticky note. |
| **Saying of the Day** | Ignatian reflection feed, with a local quote as offline fallback. |
| **Creighton Feed** | Campus news via RSS. |
| **Gratitude** | One line. Takes ten seconds. |

---

## Running it

No build step, no installation, no dependencies.

**Try it in your browser:** https://gregdyche.github.io/starthere/

**To make it yours:** clone this repo (or Code > Download ZIP). The **This
Week** and feed cards need the page served over `http://localhost` (see
[the one wrinkle](#the-one-wrinkle-two-ways-to-open-the-same-file) below), so
that is the recommended way to open it day to day — not double-clicking the
file. The easiest way to do that is a one-line shell function:

```bash
# add to ~/.zshrc (or ~/.bashrc)
starthere() {
  cd ~/repos/starthere || return
  if ! lsof -i :8000 -sTCP:LISTEN >/dev/null 2>&1; then
    python3 serve.py >/dev/null 2>&1 &
    disown
  fi
  open "http://localhost:8000/STARTHERE.html"
}
```

Then running `starthere` from any terminal starts (or reuses) the local
server and opens the page.

The server is `serve.py`, a few lines over Python's built-in `http.server`
with two additions: it listens on `127.0.0.1` only (plain `python3 -m
http.server` listens on every interface, so anyone on the same Wi-Fi could
read the repo folder, `tortoise-week.json` included), and it accepts
`POST /shutdown`, which the **Kill proc** button in the banner sends. The
button only appears when the page is served from localhost; the endpoint
rejects requests whose Host or Origin is not `localhost:8000` /
`127.0.0.1:8000`, so another website cannot stop it.

**How long the server lives:** `disown` detaches it from the terminal, so
closing the window does not stop it, and `jobs` will not list it. It runs
until you click Kill proc, log out, or restart. To check whether it is up:
`lsof -i :8000 -sTCP:LISTEN`. Everything you type stays in your own browser
(localStorage); nothing leaves your machine, which is also why you want a
local copy rather than the demo link.

(Viewing `STARTHERE.html` on github.com shows the source code. GitHub
displays files, it does not run them. Use the link above or a local copy.)

Set it as your browser homepage or pin the `localhost:8000/STARTHERE.html`
tab, so opening it is not a decision you have to make each morning.

### The Desktop icon is a symlink, not a copy

If you still want a double-clickable fallback (accepting that This Week and the
feed cards will not load — see below):

```bash
ln -s ~/repos/starthere/STARTHERE.html ~/Desktop/STARTHERE.html
```

That distinction is the whole point. Double-clicking the icon opens the real file
inside the repo — so an edit you make at 6am lands in the repo and shows up in
`git status`, where the pre-commit hooks will see it. A copy on the Desktop would
drift from the tracked version inside a week, and you would not find out until the
two disagreed about something that mattered.

The browser resolves the link before it does anything else, so the address bar
shows the repo path either way. Your saved data is therefore shared between the
Desktop icon and opening the repo file directly — the symlink does not create a
third drawer. Which matters for the next section.

### The one wrinkle: two ways to open the same file

When you double-click the file, your browser loads it from an address starting with
`file://` — it is reading the file straight off your hard drive.

There is a second way. You can run a small program on your own computer that hands
the file to the browser the way a website would, and then the address starts with
`http://localhost`. Running `serve.py` exposes nothing to the network — "localhost"
just means "this computer talking to itself."

```bash
python3 serve.py
# then visit http://localhost:8000/STARTHERE.html
```

**Why any of this matters:** browsers treat those two addresses as two different
places, even though it is one file. Two things follow from that.

1. **Your saved data does not carry over between them.** Your checklist,
   gratitude log, and settings are stored per address. Open the page the other way
   and it will look wiped clean — nothing is lost, you are just looking at a
   different drawer.
2. **The news feed, reflection quote, and This Week card refuse to load over
   `file://`.** Those cards fetch from the internet or from a sibling file
   (`tortoise-week.json`), and browsers block that kind of fetch from a page
   opened directly off disk.

**Recommendation: use `localhost` (the `starthere` shell function above) for
daily use.** Double-clicking still works, but silently loses This Week, the
Creighton feed, and the reflection quote — it will not error, it will just show
their empty-state messages, which is easy to mistake for something being
broken. If you do switch between the two methods, expect to re-enter your
settings once.

### The checklist is code

Pilots and surgeons keep the master checklist separate from the copy they run
today, and they fix the master the moment a step turns out to be missing. The
page does the same:

- **Master list:** `checklist.json` in this repo, one item per line, under
  git. Its history is the history of the routine.
- **Today's run:** the checkmarks, kept in the browser and cleared each morning.
- **Fixing it:** the Add and × buttons write `checklist.json` through
  `serve.py` (`PUT /checklist.json`, same localhost-only guard as Kill proc,
  max 30 items of 200 characters). Then `git diff` shows the change; commit it
  like any other edit. Editing the file by hand works too; reload the page.
- **Keep it short.** A real checklist holds the killer items only, the ones
  skipped often enough to hurt. Four or five, not twenty.

Over `file://` or on the GitHub Pages demo the server is not there to write the
file, so the list falls back to that browser's storage, as before.

First load after this change copies a list that used to live only in the
browser into `checklist.json`, once. **This repo is public:** anything in
`checklist.json` is public when pushed, so keep private items out of it.

If the Kill proc button says "Not serve.py" or the list says "not saved", an
old plain `python3 -m http.server` is answering instead (usually started from
a terminal that still has the pre-serve.py `starthere` function loaded). Check
with `lsof -nP -i :8000 -sTCP:LISTEN`, stop the `http.server` one, and run
`source ~/.zshrc` in old terminals.

### Checklists card

The Preflight card is one checklist. This card is the front door to all the
others: grading, class prep, semester rollover, new repo, and so on. They live
next to the work they belong to (each repo's `checklist/` or `docs/`), which
makes them hard to find, so one index lists them all.

- **The index is not in this repo.** It is `stacks/CHECKLISTS.md` in a private
  Stacks repo, one line per checklist: title, path, type (read-do, do-confirm,
  tracker), and when to run it. This repo is public; keep it that way.
- **`serve.py` does the reading.** `GET /checklists?q=...` loads the Stacks
  repo's own reader (`tools/checklists.py`; override the folder with the
  `STACKS_TOOLS` environment variable) and returns matches by title, run-when,
  path, and full text, with the last-revised date (last commit, or file date)
  and a stale flag past 90 days. Host-checked like the other endpoints.
- **Opening one:** click its title, or press Enter to open the top match. If
  the checklist's repo has a GitHub remote, the title opens it on GitHub
  (rendered, with copy buttons on code blocks) and a small Sublime link beside
  it opens the file on this Mac to edit. Without a GitHub remote the title
  opens it on the Mac. `POST /checklists/open` takes the item's index number,
  never a path, so the page can only open files the index lists. Same
  localhost guard as Kill proc.
- **GitHub is the last pushed version.** GitHub shows the
  last pushed version, so the card warns "GitHub is behind this Mac: push" or
  "GitHub is newer: pull before editing here". Edit on the Mac; if you edit
  on GitHub, pull before touching the file locally.
- **The same search in a terminal:** `cl grading`, `cl grading -o` to open,
  `cl grading -g` to open on GitHub.
- **Without the Stacks repo** (or over `file://`, or on the demo) the card
  says so and the rest of the page works as before.

The habit the card is there for: use a checklist, and if a step was missing or
wrong, fix the checklist before you close it.

### One-time setup inside the page

Some cards need a value from you before they work. Enter these directly in the page:

- **Moon Shots** — needs a Google Apps Script web app URL that accepts a POST
  with a `content` field and appends it to a Doc. Paste the `/exec` URL and the
  Doc URL into the fields on that card.
- **Daily Briefing** — set a path or URL to whatever you read first.
- **Creighton Feed** — any RSS or Atom URL.
- **This Week** — needs nothing in the page. It reads `tortoise-week.json` next
  to `STARTHERE.html`; see [Tortoise Watch sync](#tortoise-watch-sync).

---

## Where your data lives

Everything you type stays in your browser's `localStorage` — but two things do leave
your machine. Moon Shots you explicitly click Save on POSTs to the Apps Script
endpoint you configured. Separately, and without you clicking anything, feed URLs
are sent to a third-party CORS proxy every time the page loads.
See [Known issues](#known-issues-and-things-to-know-if-you-fork-this).

**That endpoint is never written into this file.** It is entered at runtime and
stored in your browser. This matters: an Apps Script `/exec` URL is an
unauthenticated write pipe into your Google Doc, and this repo is public. If you
fork this, keep it that way.

Clearing your browser data clears your checklists and gratitude log. Anything you
want to keep, save to the Doc.

---

## Tortoise Watch sync

The **This Week** card is read-only: it displays whatever is flagged `this_week`
in [Tortoise Watch](https://app.tortoiseplanner.com/). Tortoise has no public REST
API for a web page to call directly — the only access is the authenticated `Watch`
MCP connector, which only Claude can use. The pipeline:

1. A **local Cowork scheduled task in Claude Desktop** (same mechanism as the
   existing daily-brief automation — a cloud routine cannot do this step, because
   it has no access to your local filesystem and would have to commit the file to
   this public GitHub repo instead) calls the `Watch` MCP connector's
   `list_projects` with `this_week: true` each morning, and writes the result to
   `~/repos/starthere/tortoise-week.json`, overwriting whatever was there. It never
   commits or pushes; the file stays local.
2. The file shape:
   ```json
   { "generated_at": "2026-09-28T07:00:00-05:00",
     "projects": [ { "title": "...", "goal": "...", "status": "active" } ] }
   ```
   Only `title`, `goal`, `status` per project — drop anything else `list_projects`
   returns. An empty `projects` array is valid (nothing flagged this week).
3. `STARTHERE.html` fetches that file on load and lists the projects. If the
   file is missing, the card says so and points back here.

**Setting up the Cowork task:** in Claude Desktop, create a new scheduled task
(daily, weekday mornings) with this prompt:

> Call the Watch MCP connector's `list_projects` with `this_week: true`. Write
> the result to `~/repos/starthere/tortoise-week.json` (overwrite it) as
> `{"generated_at": "<current ISO 8601 timestamp>", "projects": [{"title","goal","status"}, ...]}`,
> keeping only those three fields per project. If there are zero projects, still
> write the file with an empty `projects` array. Do not run any git commands in
> that repo — this file must never be committed.

This file is **gitignored** — it holds your own project titles, and this repo is
public. Never remove `tortoise-week.json` from `.gitignore`.

Because the fetch is a same-folder relative request, it is subject to the same
`file://` restriction as the feed cards below: it works when the page is served
over `http://localhost`, and may silently fail to load when you double-click the
file directly. If This Week looks empty, try the localhost method first before
assuming the sync job did not run.

This is a snapshot, not a live view — it is only as fresh as the last time the
scheduled job ran, and it shows "this week," not a literal list of today's
intentions (Tortoise Watch does not expose a daily concept, only weekly).

---

## Security setup in this repo

The repo runs secret scanning locally before anything can be committed.

If you clone this, run:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pre-commit install     # <- required; hooks live in .git/ and are not cloned
```

Without `pre-commit install`, the config file is decorative. Then:

```bash
./audit.sh    # pre-push check; must exit 0
```

`audit.sh` also greps tracked content for the shapes this project could plausibly
leak — Apps Script `/exec` endpoints, Google Doc and Drive URLs, absolute `/Users/`
paths, generic API key or token assignments, and vendor key formats for AWS,
Google, GitHub, OpenAI, and Slack. Email addresses are reported as a warning rather
than a failure. Conventional placeholder account names in a `/Users/` path — `you`,
`user`, `username`, `yourname` — are exempt, so template text does not fail the
check while a real account name still does.

Known limits, stated plainly: `detect-secrets` only sees **git-tracked** files, so
a clean baseline says nothing about untracked files in your working tree. The
pre-commit hook covers that gap at stage time.

One trap worth knowing if you build something like this: **`detect-secrets scan
--baseline FILE` is not a check.** It exits 0 even when it finds a secret that is
not in the baseline, and it rewrites FILE in place to add what it found. An audit
built on it can never fail — and worse, running it against a repo containing a real
secret silently marks that secret approved. Check 4 uses `detect-secrets-hook` instead,
which exits 1 on anything not already in the baseline and never writes the file.

---

## Known issues and things to know if you fork this

**Feed requests go through a third party.** The Creighton feed and the reflection
quote are fetched through `api.allorigins.win`, a public CORS proxy, because a page
opened from your hard drive cannot fetch most feeds directly. Whatever URL you put
in the RSS box is sent to that operator, along with whatever comes back. For public
news feeds that is harmless — it reveals only what you read. **Do not paste a feed
URL that contains a token or a private calendar link.**

**"Sent to Google Doc" is not a delivery confirmation.** The save uses `no-cors`
mode, which makes the response invisible to the page. The success message appears
whether or not the Apps Script actually received it. If something matters, check
the Doc.

**The reflection feed is hardcoded** while every other feed is configurable. If you
fork this, that is the line to change first.

---

## Editing it

One file. Open it in any editor.

- Default checklist items: `DEFAULT_CHECKS`
- Git steps: `DEFAULT_GIT_CHECKS`
- Quotes: `QUOTES`
- Launch Pad links: the `<a>` tags in the Launch Pad card
- Colors: the `:root` block at the top

Keep placeholders generic — `~/Documents/file.md`, never a real path. Real paths
leak your username and directory layout to everyone reading a public repo.

---

*"Slow is smooth, and smooth is fast."*
