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
| **Pomodoro** | 25/5 timer with a completed-blocks count for the day. |
| **Launch Pad** | Direct links to Toggl, Canvas, mail, calendar, daily briefing. |
| **Git Preflight** | The pull → status → add → *check nothing secret is staged* → commit → push sequence. Manual reset. |
| **Daily Intentions** | What I intend to make true today. Appends to a Google Doc. |
| **Moon Shots** | Ideas bigger than a month, so they have a home instead of a sticky note. |
| **Saying of the Day** | Ignatian reflection feed, with a local quote as offline fallback. |
| **Creighton Feed** | Campus news via RSS. |
| **Gratitude** | One line. Takes ten seconds. |

---

## Running it

No build step, no installation, no dependencies. Double-click `STARTHERE.html` and
it opens in your browser. That is the whole thing.

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

- **Daily Intentions / Moon Shots** — needs a Google Apps Script web app URL that
  accepts a POST with a `content` field and appends it to a Doc. Paste the `/exec`
  URL and the Doc URL into the fields on that card.
- **Daily Briefing** — set a path or URL to whatever you read first.
- **Creighton Feed** — any RSS or Atom URL.

---

## Where your data lives

Everything you type stays in your browser's `localStorage` — but two things do leave
your machine. The Intentions and Moon Shots you explicitly click Save on POST to
the Apps Script endpoint you configured. Separately, and without you clicking
anything, feed URLs are sent to a third-party CORS proxy every time the page loads.
See [Known issues](#known-issues-and-things-to-know-if-you-fork-this).

**That endpoint is never written into this file.** It is entered at runtime and
stored in your browser. This matters: an Apps Script `/exec` URL is an
unauthenticated write pipe into your Google Doc, and this repo is public. If you
fork this, keep it that way.

Clearing your browser data clears your checklists and gratitude log. Anything you
want to keep, save to the Doc.

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
