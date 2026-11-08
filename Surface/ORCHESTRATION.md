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

- **Result:** Completed this foundation scope. Added `Surface/circleApp_Surface.maxpat` as a separate copy of `Circle/extras/circleApp_cgsSynth.maxpat`; original host remains unchanged. Recorded a tentative UDP/OSC schema in `Surface/SPEC.md`: existing TUIO input on 3333, app keyboard notes on 3334 (`/circle/note`), and Max ready/features telemetry on 3335 (`/circle/ready`, `/circle/features`).
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

- **Result:** Added a load-started 500 ms `/circle/ready 1` OSC heartbeat from the Surface Max host to UDP 3335. Enabled readiness-gated sending in the app; while heartbeat is absent, local drawing remains available and outgoing Max input is paused.
- **Checks:** Max host patch parses as JSON and the heartbeat object/connection chain is source-reviewed. No Max runtime check was run.
- **Remaining:** Confirm heartbeat reception/loss detection, Max note/gesture exchange, and audible sound manually. Feature telemetry serialization remains unresolved.

### Ticket 7 — Max feature telemetry (blocked pending Max validation)

- **Result:** No patch changes. The controller exposes 90 channels, and the mapper splits them into five adjacent 18-channel groups. `mc.snapshot~` emits channel identifiers and values separately, but a reliable indexed/ordered packing route into the agreed 90-value OSC schema is not established from source alone.
- **Checks:** Inspected controller and mapper signal routing and Cycling '74's `mc.snapshot~` reference. No Max runtime checks were run.
- **Remaining:** Validate channel-indexed packing and message order in Max 9 before wiring `/circle/features`; otherwise the app could silently label the wrong values. Audible sound and the current heartbeat/input paths also remain for manual verification.

