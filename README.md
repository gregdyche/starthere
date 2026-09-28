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
| **Preflight Checklist** | The daily non-negotiables. Checkmarks clear each morning; the items stay. |
| **Launch Pad** | Direct links to Toggl, Canvas, mail, calendar, daily briefing. |
| **Git Preflight** | The pull → status → add → *check nothing secret is staged* → commit → push sequence. Manual reset. |
| **This Week** | Read-only. Projects flagged `this_week` in [Tortoise Watch](https://app.tortoiseplanner.com/), from a local snapshot file. See [Tortoise Watch sync](#tortoise-watch-sync). |
| **Moon Shots** | Ideas bigger than a month, so they have a home instead of a sticky note. |
| **Saying of the Day** | Ignatian reflection feed, with a local quote as offline fallback. |
| **Creighton Feed** | Campus news via RSS. |
| **Gratitude** | One line. Takes ten seconds. |

---

## Running it

No build step, no installation, no dependencies.

**Try it in your browser:** https://gregdyche.github.io/starthere/

**To make it yours:** clone this repo (or Code > Download ZIP), then
double-click your local `STARTHERE.html`. That is the whole thing.
Everything you type stays in your own browser (localStorage); nothing
leaves your machine, which is also why you want a local copy rather
than the demo link.

(Viewing `STARTHERE.html` on github.com shows the source code. GitHub
displays files, it does not run them. Use the link above or a local copy.)

Set it as your browser homepage or pin the tab, so opening it is not a decision you
have to make each morning.

### The Desktop icon is a symlink, not a copy

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
`http://localhost`. Running that server exposes nothing to the network — "localhost"
just means "this computer talking to itself."

```bash
python3 -m http.server 8000
# then visit http://localhost:8000/STARTHERE.html
```

**Why any of this matters:** browsers treat those two addresses as two different
places, even though it is one file. Two things follow from that.

1. **Your saved data does not carry over between them.** Your checklist,
   gratitude log, and settings are stored per address. Open the page the other way
   and it will look wiped clean — nothing is lost, you are just looking at a
   different drawer.
2. **The news and reflection feeds may refuse to load over `file://`.** Those cards
   pull from the internet, and browsers apply stricter rules to pages opened
   directly from disk.

**Recommendation: pick one and stay with it.** For daily use, double-clicking is
simpler — there is no server to remember to start. Only switch to the `localhost`
method if the feed cards will not load, and expect to re-enter your settings once
when you do.

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
