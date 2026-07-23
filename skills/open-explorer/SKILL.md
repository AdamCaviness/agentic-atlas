---
name: open-explorer
description: >
  Open the Agentic Atlas Explorer, the hosted map of every profile we have already run. We
  keep ready-made profiles of popular agentic methodologies (bmad-method, superpowers,
  spec-kit, openspec, agent-os, task-master, and a dozen more) so you can browse them, set
  what matters to you, and find your fit without profiling anything yourself. Reach for
  /agentic-atlas:run only when you want to profile a tool that is not in the collection.
  Trigger: /agentic-atlas:open-explorer
---

# Open the Explorer

The **Explorer** is the hosted home of Agentic Atlas, an interactive map of every profile we
have already run, at https://adamcaviness.github.io/agentic-atlas/ . We keep ready-made
profiles of popular agentic methodologies there, so most people never need to profile
anything themselves: just browse, set the axes that matter to you, and see which approaches
lean your way. Both ends of every axis are legitimate. The Explorer locates tools, it does
not rank them, and there is no overall score.

## What to do

Open the Explorer in the default browser and print the address so it is reachable either way.
Opening a browser tab is the whole point of this skill, so do it without asking first.

```bash
URL="https://adamcaviness.github.io/agentic-atlas/"
printf 'Explorer: %s\n' "$URL"
# best-effort open in the default browser; never fatal if no opener exists
command -v open        >/dev/null 2>&1 && open "$URL" \
  || { command -v xdg-open >/dev/null 2>&1 && xdg-open "$URL"; } \
  || { command -v powershell.exe >/dev/null 2>&1 && powershell.exe -NoProfile -Command "Start-Process '$URL'"; } \
  || true
```

If no opener is available (a headless or restricted environment), the printed URL is the
fallback: surface it so the user can open it themselves. If the harness can display web pages
inline, you may also offer to open it that way.

## Then, briefly

Tell the user what they will find and how to go further:

- The Explorer hosts the current collection of profiles, popular methodologies we have already
  run, each on the same 13 signed axes. Set only the preferences that matter; untouched axes
  mean no preference, and the map surfaces the approaches that lean your way.
- Every profile page links back to the Explorer through its brand mark, so browsing one
  profile is one click from the whole set.
- To profile a tool that is **not** in the collection (your own repo, a private framework, or
  a fresh release), use `/agentic-atlas:run [path-or-git-url]`.

## Notes

- The address is kept in sync with `_HOME_URL` in `agentic_atlas/report.py`, the same URL the
  profile pages link home to. If the site ever moves, update both.
- This skill is read-only and makes no network calls of its own; it only hands the URL to the
  browser.
