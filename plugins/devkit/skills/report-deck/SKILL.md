---
name: report-deck
description: Turn any report, review, standup, status update, meeting summary or table of results into a Slides deck (claude.ai Artifact) in the user's design system, plus an .xlsx copy of the main table, without asking about format. Settings (design system, output folder) come from ~/.claude/report-deck.json.
---

# report-deck

Every report is a presentation, not a chat summary, plus a spreadsheet of its main table. Don't ask how to build it, which design system to use or where to save the table.

## Settings

Read `~/.claude/report-deck.json` once:

```json
{
  "design_system": "https://claude.ai/artifact/<id>",
  "design_system_name": "Orchard",
  "xlsx_dir": "~/Documents/reports"
}
```

- No file, or no `design_system`: use the user's default Design System artifact (`Artifact` action `list`, `type: "Design System"`); if none is marked default, use the Slides type's own look.
- No `xlsx_dir`: save next to the working directory in `reports/`.
- Never put the settings' values in a public repo.

## Output, always both

1. **A Slides deck** (Artifact from the Slides type) in that design system.
2. **An Excel copy of the main table** at `<xlsx_dir>/<project>-<topic>-<YYYY-MM-DD>.xlsx`: header row bold on dark, wrapped text, frozen header.

Give both links in the reply, one line each, and say the deck is private until shared from its Share menu.

## Steps

1. `Artifact` action `quickstart`, intent `slides`, `design_systems: false` when the settings name a system.
2. Publish with the Slides `type_url`, a `title` like "<Project> standup <date>", `auto_open: "after_first_write"`.
3. Read the design system in one call: `paths: ["project/README.md", "project/api/tokens.md", "project/tokens.json"]`.
4. Write `project/deck.json` first (full `order`, `sections`, `faces`, and the `designSystems` record), then the cover; publish both with the system's `tokens.json` copied in as the Slides instructions describe.
5. Remaining slides, three per publish. Don't re-read or verify unless asked.

## Look

Follow the design system's tokens and README. Without one: two surface tones, one dark statement slide, one accent for eyebrows and attention, status words always spelled out (never color alone), sentence case, no exclamation marks, no emoji, nothing under 24px on a 1920×1080 slide.

## Content for a status or standup

Typically 6–8 slides: cover with the one-line headline · what moved since last time · the ticket board (table) · the item in flight and its steps to done · new facts or risks · what needs the owner (numbered, dark slide) · next, by person or agent. Use only facts from the session, the tracker or git; never invent numbers. Plain words; ticket keys in tables, not prose.

## The .xlsx

If `openpyxl` isn't installed, use a throwaway virtual environment (`python3 -m venv <tmp>/venv && <tmp>/venv/bin/pip install -q openpyxl`) and run the build with `-I`.

## Updating

To refresh a report made earlier in the conversation, publish the changed slide files to the same deck URL and rewrite the same .xlsx path.
