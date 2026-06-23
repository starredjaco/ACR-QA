# ACR-QA LinkedIn Video Script
**Style:** SecureHub-style cinematic | **Length:** ~75 seconds | **Updated:** 2026-06-21

---

## TL;DR — Simplest path to a finished video (Linux, free)

```
1. Install Cursorful Chrome extension → record the dashboard demo in one take (~60s raw)
2. Cursorful auto-adds cursor-follow zoom during/after recording → adjust timing in its editor
3. Create intro + stats + end-card slides in Canva (web) → export as video clips
4. Stitch everything in Kdenlive (Linux native, free) → add music → export MP4
5. Post on LinkedIn
```

Total editing time: ~60–90 minutes for a first version. The demo is the hard part — everything else is assembly.

---

## Before You Record — Checklist

```bash
sudo systemctl start docker          # must be running (exploit verifier needs it)
# Clear stale scan data so results are clean:
rm -f DATA/outputs/*.json
# Start the API + dashboard
.venv/bin/uvicorn FRONTEND.api.main:app --host 0.0.0.0 --port 8000 --reload &
cd dashboard && npm run dev &        # dashboard at :5173
```

Open Chrome to `localhost:5173`. Go to New Scan → "Scan a GitHub Repository".
Pre-type `https://github.com/anxolerd/dvpwa` — **don't hit Scan yet**.

**Why dvpwa:** always produces ~32 findings · 13 HIGH · ECDSA signed · ~34s runtime.
This is the reliable demo path. Do not scan `TESTS/samples/` — the test-path filter
suppresses all findings and prints "Total: 0 · PASSED" on camera.

---

## Video Structure & Timing

### PART 1 — HOOK [0:00–0:10] Black screen, text only
*No tool. Create in Canva as a 10-second video clip.*
*White text on black. Slow fade-in, 2-second hold per line.*

```
"Is your code actually secure?"

[2s pause]

"Or are you just trusting the AI that wrote it?"
```

---

### PART 2 — THE PROBLEM [0:10–0:17] IDE, slow zoom
*Screen recording of Antigravity IDE — dark theme, clean AI-generated Python, big font.*
*Slow zoom toward one function. Looks innocent.*
*Bottom-right text overlay: "Looks fine."*

Record this as a separate OBS clip (5–7 seconds). No audio needed.

---

### PART 3 — THE SCAN [0:17–0:42] Real dashboard — Cursorful records this
*This is the money shot. Record with Cursorful for auto-zoom on the input field and results.*

**Shot sequence:**
1. Dashboard loaded. Slow zoom toward input box.
2. Type `github.com/anxolerd/dvpwa` → click Scan.
3. First 3 seconds of tools firing — **keep this at real speed** (shows it's live, not fake).
4. **Speed-ramp the middle** (seconds 4–30 of the scan) to 5–8× speed in editing.
   This compresses the wait to ~5 seconds while showing tools ticking — looks cinematic, not fake.
5. **Slow back to real speed** for the last 2 seconds when results land.
6. Results slam in: `32 findings · 13 HIGH · ECDSA signed · Rekor logged`
7. **Stay here for 4 seconds.** Zoom into the result count.
8. Click into one HIGH finding: SQL injection · file path · line number · evidence snippet.
9. Slow zoom into the finding card. **Stay here for 3 seconds.**

*The speed-ramp on your raw real footage is not faking anything — only fabricated UI would.*
*In Kdenlive: right-click clip → "Change Speed" → set middle portion to 700–800%.*

---

### PART 4 — THE NUMBERS [0:42–0:58] Black screen, one stat per beat
*Create in Canva. White bold text on black, 2–3 seconds each. Beat-sync to music.*

```
96.4% precision.

8 / 8 CVEs caught.

Beats Semgrep. Beats Snyk. Out-recalls GPT-5.5 at $0.

3,147 tests.  9 months.  1 person.
```

---

### PART 5 — END CARD [0:58–1:15]
*Create in Canva. Dark background, logo or project name centered.*

```
ACR-QA
The Trust Layer for AI-Generated Code

Open Source  ·  github.com/ahmed-145/ACR-QA
```

*Hold 15 seconds — LinkedIn viewers pause here to read the link.*

---

## Production Stack (Linux — verified)

### Step 1 — Record the demo (Part 3)
**Cursorful** — Chrome extension, works on Linux (Chrome / Brave / Edge)
→ Install: Chrome Web Store → search "Cursorful Screen Recorder"
→ Click extension icon → Start Recording → records the browser tab
→ Cursor-follow zoom happens automatically during recording
→ After recording: open built-in editor to adjust zoom timing/intensity
→ Export MP4

**Why not OBS for the demo:** OBS doesn't auto-zoom. Use OBS for the IDE shot (Part 2)
where you just want a clean screen capture with no zoom effects.

### Step 2 — Record the IDE shot (Part 2)
**OBS Studio** — Linux native, free
```bash
sudo apt install obs-studio
```
Create a 5-second scene: Window Capture → Antigravity IDE → dark theme Python code.
Slow zoom = add a "Video Zoom" filter in OBS or just do it in Kdenlive post.

**Why OBS and not Antigravity IDE's built-in recording:**
Antigravity IDE (Google's 2026 AI IDE) does have screen sharing in Agent Mode — it streams
your screen *to the AI agent* so it can observe and help you code. That streaming session
does not produce a polished exportable MP4. It's a coding-assistance tool, not a video editor.
Use Antigravity IDE as the *subject* (open it, write some Python, look dramatic) and OBS to
capture the output. The dark AI IDE aesthetic looks very impressive in a 5-second shot.

### Step 3 — Create text cards (Parts 1, 4, 5)
**Canva** (web, free) — `canva.com/video-editor`
→ New design → Video → 1920×1080
→ Black background → add text → use slow "Fade" animation
→ Export as MP4 (free plan supports this)

### Step 4 — Stitch + speed-ramp + music
**Kdenlive** — Linux native, free
```bash
sudo apt install kdenlive
```
- Import: Part 1 (Canva), Part 2 (OBS), Part 3 (Cursorful), Part 4 (Canva), Part 5 (Canva)
- Speed-ramp Part 3: right-click middle portion → "Change Speed" → 700%
- Add music track: download free track from Pixabay (pixabay.com/music)
  → Style: "dark ambient tech" or "cyberpunk tension"
  → Lower to 20% volume under the scan, raise during stats cards
- Add auto-captions to any spoken parts (or keep the whole thing silent with text only)

### Step 5 — Export
- Format: MP4 · H.264 · 1920×1080 · 30fps
- LinkedIn max: 5GB / 10 minutes. Aim < 200MB.

---

## The 34-second scan — cut it or not?

**Cut (speed-ramp) it.** 34 seconds of progress bar is half the video and people scroll.

The right edit:
- Keep the first **3 seconds real speed** (tools firing = trust signal)
- Speed **middle 28 seconds to 5–8×** (compressed to ~4–5s, shows it's working)
- Slow back for the **last 3 seconds** when results land (dramatic reveal)

Total scan portion: ~10–12 seconds in the final video instead of 34.

This is not faking — you're showing real footage at a different speed.
The trust signals (tool names, result count, attestation badge, finding details) are all visible and real.

---

## Do NOT use these on Linux
- **AutoZoom** — Windows/macOS desktop app, no Linux version yet
- **FocuSee** — Windows/macOS only
- **CapCut Desktop** — no Linux client
- **Descript** — no Linux client

**Web-based alternatives if Cursorful doesn't work:**
- **Cursorfly** — open-source Chrome extension, same idea as Cursorful
- **Zoomflow** — Chrome extension with auto-zoom editor
- **Canva video editor** — can also do the stitching if you don't want to install Kdenlive
