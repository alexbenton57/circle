# Surface Milestone Orchestration

Work is split into serial tickets. Each implementation ticket is handled by one GPT-6 Luna Light subagent at a time; review the completed ticket and append a brief report below before starting the next.

## Ticket sequence

1. **Max host scaffold and protocol draft:** create a separate Surface host and record the app/Max message schema.
2. **Max input bridge:** wire keyboard note input through an additive route into the existing note manager without changing the cgsSynth host behavior. Coordinate aspect compensation is handled by the Python input adapter in Ticket 4, leaving Max's fixed Y transform unchanged.
3. **Max telemetry bridge:** serialize plotter-style ratio groups and idle heartbeat from Max to the app.
4. **Python transport and input model:** implement device-independent XY handling and the agreed TUIO/keyboard/telemetry transport.
5. **PySide6 application slice:** build the agreed landscape interface, keyboard, gesture surface, XY/status/readout display, and retained raw trace; connect it to the transport.

After each ticket, record files changed, key decisions, checks performed, and remaining manual verification. Do not start a later ticket until the prior one is reviewed and its brief report is recorded.

## Ticket reports

### Ticket 1 — Max host scaffold and protocol draft

- **Result:** Completed this foundation scope. Added `Circle/extras/circleApp_Surface.maxpat` as a separate copy of `Circle/extras/circleApp_cgsSynth.maxpat`; it is inside the repository's linked Max package, and the original host remains unchanged. Recorded a tentative UDP/OSC schema in `Surface/SPEC.md`: existing TUIO input on 3333, app keyboard notes on 3334 (`/circle/note`), and Max ready/features telemetry on 3335 (`/circle/ready`, `/circle/features`).
- **Checks:** Confirmed the existing controller's TUIO input and feature signal buses by source inspection. No tests or Max runtime checks run for this ticket.
- **Remaining:** Max receiver/sender objects are not wired; the proposed schema is not operational. Keyboard routing is Ticket 2 and feature conversion/serialization plus heartbeat are Ticket 3. Python aspect compensation is Ticket 4. Sound and real message exchange remain unverified.

### Ticket 2 — Max input bridge reconnaissance (superseded; no code changes)

- **Result:** The first implementation attempt stopped before editing because the note-manager route was unclear. Follow-up source inspection found `circleSynth_Minilab`'s `gen circleSynth_ctrl_noteManager` inputs: pitch, velocity, and bend. The new OSC note event can be routed directly to pitch/velocity with bend left at its existing zero state.
- **Checks:** Inspected the Max patch cords and confirmed the existing controller's Y expression is `(1-y)*1.42`.
- **Remaining:** Implement the OSC note receiver/route. Aspect compensation is moved to the Python TUIO adapter to avoid changing the Max transform.

### Ticket 2 — Max keyboard input bridge

- **Result:** Added UDP 3334 `/circle/note` handling to the Surface host and routed pitch/velocity through optional inlets on the existing controller and Minilab abstraction into the monophonic note manager. The existing cgsSynth host is unchanged. Updated the abstraction inlet metadata and removed unrelated JSON reformatting.
- **Checks:** Reviewed focused Max patch diffs and confirmed the route is connected to note-manager pitch/velocity inputs; existing bend path remains as before. No tests or Max runtime checks were run.
- **Remaining:** OSC reception, note on/off behavior, and resulting sound require manual verification in Max. Telemetry and heartbeat remain Ticket 3.

### Ticket 3 — Max telemetry bridge (serialization unresolved)

- **Result:** No patch changes. Source inspection found the 90-channel signal carries five 18-value feature groups inside the controller's scoped bus. The host cannot access it directly. Max's documented `mc.snapshot~` emits channel/value events individually, so the agreed flat feature OSC list cannot be assumed to emerge from a simple snapshot object.
- **Checks:** Inspected feature signal routing and the official Cycling '74 `mc.snapshot~` reference. No Max runtime checks were run.
- **Remaining:** Validate a Surface-specific feature outlet and a reliable list-packing/send path in Max before adding `/circle/features`. Python transport/UI may proceed against the agreed draft schema. Ready heartbeat is also deferred with the telemetry path.

### Ticket 4 — Python transport and input model

- **Result:** Added device-independent single-pointer gesture and monophonic latch models, plus dependency-free OSC/TUIO transport for gesture coordinates, note messages, heartbeat, and draft feature parsing. TUIO Y compensates for canvas aspect ratio and Max's fixed `1.42` scale. Added cursor release (`alive` with no session) and `fseq`. Readiness gating can be disabled during bring-up.
- **Checks:** Reviewed the model and OSC framing against the existing Max TUIO `set` route and `unpack` fields. No tests were run. Telemetry parse code follows the proposed schema, but Max does not yet emit it.
- **Remaining:** GUI must marshal receive-thread callbacks through Qt signals. Message exchange, latency, note/audio, and telemetry need runtime verification in Max.

### Ticket 5 — PySide6 application slice

- **Result:** Added a PySide6 app with the left-edge rotated octave keyboard, single-pointer touch/pen/mouse gesture canvas, final release sample and TUIO release frame, retained raw trace, XY/status/feature readouts, and Qt signal delivery for transport callbacks. Added `Surface/requirements.txt` with the single runtime dependency. Keyboard stops on disconnect and app close.
- **Checks:** Source-reviewed event flow and wiring to the input model/transport. No tests or GUI/Max runtime checks were run.
- **Remaining:** Max readiness/feature telemetry remain unwired; audible output, touch/pen tracking, orientation feel, latency, and final app packaging need laptop/Surface evaluation.

### Ticket 6 — Surface Max ready heartbeat

- **Result:** Added a load-started 500 ms `/circle/ready 1` OSC heartbeat from the Surface Max host to UDP 3335. After the live check showed the app received no heartbeat, simplified its Max route to send a normal `/circle/ready 1` Max message directly to `udpsend`, which encodes OSC. App sending remains readiness-gated.
- **Checks:** Max host patch parses as JSON and the heartbeat object/connection chain is source-reviewed. No Max runtime check was run.
- **Remaining:** Confirm heartbeat reception/loss detection, Max note/gesture exchange, and audible sound manually. Feature telemetry serialization remains unresolved.

### Ticket 7 — Max feature telemetry (blocked pending Max validation)

- **Result:** No patch changes. The controller exposes 90 channels, and the mapper splits them into five adjacent 18-channel groups. `mc.snapshot~` emits channel identifiers and values separately, but a reliable indexed/ordered packing route into the agreed 90-value OSC schema is not established from source alone.
- **Checks:** Inspected controller and mapper signal routing and Cycling '74's `mc.snapshot~` reference. No Max runtime checks were run.
- **Remaining:** Validate channel-indexed packing and message order in Max 9 before wiring `/circle/features`; otherwise the app could silently label the wrong values. Audible sound and the current heartbeat/input paths also remain for manual verification.

### Ticket 8 — Indexed Max feature stream

- **Result:** Added an optional ninth 90-channel feature outlet to the shared controller and connected it only in the Surface host to `mc.snapshot~ 500`. The host emits each channel as `/circle/feature (channel, value)` on UDP 3335. Channel IDs are explicit, so assembly does not depend on list order. A duplicate Max outlet index was found during live diagnosis and corrected to index 9. Heartbeat remains a direct `/circle/ready 1` message to `udpsend`.
- **Checks:** Reviewed outlet and host wiring; both Max patch files parse as JSON. The repo's feature scope already uses `route voice`, and Cycling '74 documents `mc.snapshot~` channel identifiers before each sample. No Max runtime check was run.
- **Remaining:** Python must assemble all 90 indexed samples into the five 18-value groups. Max telemetry output still needs live validation.

### Ticket 9 — Python indexed feature assembly

- **Result:** The transport now accepts `/circle/feature (channel, value)` messages, validates channel IDs 1–90 and finite numeric values, and assembles the five groups by channel index. It calls the UI callback only after a full 90-channel sample set; a repeated ID discards an incomplete frame. The user has confirmed the app produces sound through Max.
- **Checks:** Source-reviewed packet parsing and the frame assembler. No tests were run.
- **Remaining:** Reload the updated Surface host in Max and confirm live feature packets reach the app. Verify displayed group/readout values against Max's scopes; heartbeat loss detection and Surface touch behavior also need manual checks.

### Ticket 10 — Long-gesture input throughput

- **Finding:** The canvas retained every point in a Python list and rebuilt a full `QPainterPath` from that list on every repaint. Total path-building work therefore grew roughly quadratically over a long gesture, delaying UI input handling and UDP sends. Per-sample OSC/network work was constant-size.
- **Result:** Replaced the growing list/path rebuild with a fixed-size `QImage` trace canvas updated only for each newest segment. The image is blitted on repaint, retained after release, and cleared for the next gesture. Each normalized sample is sent to Max before trace rendering; the Max data path still sends every sample without throttling, smoothing, or decimation. Reduced feature snapshots from 10 Hz to 2 Hz, keeping telemetry traffic to 180 indexed packets/second.
- **Checks:** Source review confirms no duration-growing trace loop remains and the UDP send precedes image drawing. No tests or timing measurements were run.
- **Remaining:** Restart the Python app and test a one-minute Surface stylus gesture while monitoring Max input rate. If the rate still declines, measure the per-sample TUIO/Max processing path next.

### Ticket 11 — Position rate and plot visibility controls

- **Result:** Added a top-bar position-packet rate, updated every 500 ms from successful UDP sends, plus independent Raw (on by default) and CGS (off by default) toggles. The canvas accepts normalized CGS points and draws them separately; it does not compute the CGS curve.
- **Checks:** Source review confirms rate counting is outside the UI refresh loop and all gesture sends remain unchanged. No tests were run.
- **Remaining:** Connect the CGS renderer to Max telemetry; source choice is settled as Python display reconstruction from Max-derived feature data.

### Ticket 12 — Display-only CGS curve reconstruction

- **Result:** Added a separate standard-library renderer that maps the selected highest-energy Max feature group through the plotter's Model A two-ellipse equations, including Cartesian shape inversion from the repository's `cartToTauS` definition. The app fits returned world-coordinate points into the canvas with equal pixel scale and updates the CGS plot from telemetry. Raw and CGS toggles stay independent. No curve coordinates are sent back to Max.
- **Checks:** Reviewed mapping against `2Ellipse_plotter.py`, `circle_core_TauSCart.genexpr`, and the agreed feature layout. No tests or runtime checks were run. Phase convention remains unverified against synthetic data.
- **Remaining:** Reload Max/app and validate the CGS curve visually against a known synthetic gesture. Verify the plotter's phase/frequency convention and the look on Surface. Python renderer remains display-only; Max still controls CGL analysis and sound.

### Ticket 13 — Max note-route diagnostics

- **Result:** Added temporary Max console taps after the Surface `/circle/note` route and after the Minilab `unpack`, logging the incoming list and its pitch/velocity atoms independently.
- **Checks:** Both edited Max patch files parse as JSON. No Max runtime check has been run.
- **Runtime finding:** The route receives expected pitch/velocity lists, and `unpack` emits expected scalar values. Disconnecting the velocity-to-Gen cable removes the error but also prevents sound.
- **Result:** Changed the note input unpack to float outlets, matching the existing Minilab MIDI path's `flonum` values. During follow-up inspection, found that the pitch-to-Gen cable had been left disconnected; restored it. Diagnostic taps remain.
- **Checks:** Max patch files parse as JSON; both pitch and velocity outlets are wired to the note-manager Gen inputs in the repository copy. Max runtime retest pending.
- **Remaining:** Reload the Minilab abstraction and test notes. If sound works, remove the temporary diagnostic taps; if not, continue tracing note-manager output to the synth engine.

