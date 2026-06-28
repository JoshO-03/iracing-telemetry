Phase 0 — Define contracts before writing logic (do this first, ~1 day)
This is the phase that was skipped last time. Before any analysis code:

Write a docs/DATA-MODEL.md (or just a pinned doc) defining, in plain language + a tiny diagram, what these things mean and how they relate: TelemetrySample → Lap → Session; TrackModel → Sector → Corner; CornerPerformance / LapAnalysis. One sentence per field is enough. This is the artifact that stops "apexDist vs apexDistPct" drift — you write it once, and both Python's JSON output and TypeScript's types reference the same names.

Decide the track model JSON schema (the contract between Python and TypeScript) as a versioned schema — you already started this well (schemaVersion: 1 in exportTrackGeometry.py). Extend it now to also include sectors and corners in that same file, so one track has one JSON, not three (okayama.json + okayama_reference.json + a hypothetical 166.json). Decide this shape before phase 2, because corner detection's output needs to slot into it.

Pick the channel-name strategy. You're currently filtering a hardcoded wantedHeaders array in parser.ts. Move this to a small config file/module (e.g. config/channels.ts) — not for genericness for its own sake, but because every car has slightly different available channels (e.g. some cars expose dcBrakeBias, hybrid cars expose extra channels), so this will need to change per car eventually, and you want one place to change it.

Phase 1 — Fix the foundation pipeline (don't rebuild parsing, just make it trustworthy)
The IBT binary parser itself is solid — don't rewrite it. But before building new analysis on top, close the loop so you trust the foundation:

Fix the await bug in getTrackModel / parseLaps.
Pick one getTrackModel (delete the other — trackHelper.ts or analysis/utils.ts).
Generate one real, complete track model JSON for Okayama (geometry + sectors + corners in one file, per the phase 0 schema) so you have a real fixture to build against, not a half-finished one.

Write 2–3 tiny sanity scripts (don't need a formal test framework yet) that load that JSON and your sample telemetry.csv and print obviously-checkable things — e.g. "lap length from telemetry vs track model length, should be within X%." This is your safety net for phase 2+.

Phase 2 — Corner & apex detection, Python prototype (this is where you validate visually)
This is essentially redoing cornerDetection.py, but designed instead of organically grown:

Define the algorithm in words first: what counts as "entering a corner" (your steering/brake/throttle-lift union approach was a genuinely good idea — keep it), what counts as the apex (min-speed point — good), what counts as exit.

Implement it again, but write it as pure functions that take a DataFrame and return plain dicts matching the phase-0 schema — no plotting inside the detection functions. Keep plotting/visualization as separate functions that call the detector and draw the result. (Right now plotting and detection are tangled together in the same file, which makes both harder to trust.)

Validate visually against 2–3 different laps from your one track (even from the same session) — corners should land in consistent places lap-to-lap. This is the actual point of doing it in Python first: you can eyeball-verify before anything depends on it.

Once you trust it, this Python script's only remaining job is: take telemetry CSV → output corners into the track model JSON. It becomes a track-authoring tool, not a runtime analyzer.

Phase 3 — Port corner/apex detection logic into TypeScript

Re-implement the proven algorithm in TypeScript against your Phase-0 types — this should be a fairly mechanical translation now, since the hard thinking already happened in Python.
Test it by running it against the same track JSON + telemetry that you validated visually in Python, and diff the outputs (corner boundaries, apex points) — they should match (or you find out why they don't, which is valuable).

This retires SessionParser.ts's current half-built version — rewrite getCornerAnalysis against the validated approach rather than patching the existing bugs.

Phase 4 — Per-corner performance metrics (TypeScript)
Now build the actual "coaching" metrics on solid ground:

Entry/apex/exit speed, braking point (distance + intensity), throttle pickup point — these are the PROJECT-STATUS.md goals, and they're now straightforward once corners are trustworthy: for each corner's sample window, pull specific values (min speed = apex speed, last sample's speed = exit speed, first sample's speed = entry speed) rather than the open-ended "scan for transitions" approach the current detectBreakingPerformance uses, which has subtle bugs (e.g. it overwrites brakingStartPct every time brake is reapplied, so multi-stab braking zones report wrong start points).

Phase 5 — Lap comparison & delta analysis

Compare two laps' channel values at matching LapDistPct (interpolate since sample timing won't align) — this is what produces the classic "time gained/lost per corner" view.
This is where a garage61-style UI becomes meaningful: speed-trace overlay of two laps, shaded per-corner time delta.

Phase 6 — Minimal UI to actually see results

Doesn't need to be the desktop app yet — a simple local web page (even just rendering charts from the JSON output of phases 3–5) is enough to validate the full pipeline end-to-end and is much faster to iterate on than Electron.
This is also a forcing function: if the UI is awkward to build from your data shapes, that's a sign the analysis layer's output format needs adjusting before you build the real app.

Phase 7 — Live telemetry (the desktop app)

Only once file-based analysis works end-to-end. iRacing's SDK exposes telemetry over shared memory; Node has community SDK wrappers for this (worth researching specifically when you get here — I haven't verified current library options for you, happy to do that closer to the time).
Because you built TelemetrySample/Session as the shared contract from Phase 0, this phase is "write a new data source that produces the same shapes," not a rewrite of the analyzer.


TODO:
- Add apex dection to the track model, plotting an exact point so I know how far drivers are away from the apex