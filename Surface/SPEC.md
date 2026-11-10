# Surface Prototype Specification

## Purpose

Build a Windows application in Python with PySide6 for the Surface Pro 4. It replaces the existing iPad gesture interface and external MIDI keyboard while retaining Max/MSP for CGL analysis and sound generation. Development and initial integration testing will run on the main laptop with Max on the same machine; the app will then be evaluated on the Surface alongside the mechanical rig.

## Agreed behaviour

- The gesture area accepts Surface touch, Surface Pen, and mouse click-and-drag for laptop development. Gesture processing is independent of the input device. Only one gesture pointer may be active; ignore additional pointers until the active one lifts.
- Gesture position is sent continuously from pointer down through release, without added smoothing. The app displays the normalized XY position it sends to Max.
- The top status bar shows the measured rate of successfully sent position packets. Raw input tracing and the derived CGS curve have independent visibility toggles.
- The on-screen keyboard is one octave, C4–B4 (MIDI pitches 60–71), monophonic, and latching. Pressing the active key stops its note; pressing another key replaces it. The app sends MIDI-style pitch and velocity values to Max (velocity 100 on, 0 off; bend fixed at zero) for routing into existing note handling. Pitch bend and pedal controls are not required initially.
- CGL feature extraction, analysis, and sound control remain in Max. Python may reconstruct a theoretical two-ellipse curve from Max-derived telemetry for visualization only; that rendering calculation has no effect on sound or the Max CGL signal. Keep the renderer independent of the input device so a future galvanometer path can provide equivalent feature data.
- The raw traced curve is plotted from input samples and retained after release until the next gesture. It can be hidden independently from the derived two-ellipse CGS curve, which is reconstructed from Max feature telemetry for display only.
- The landscape layout places the rotated keyboard at the left edge, with its front edge against that edge. The gesture area occupies the remaining area at full screen height; readouts remain compact.

## Proposed integration

- Create a separate `circleApp_Surface.maxpat` based on `circleApp_cgsSynth.maxpat`; leave the existing cgsSynth host patch unchanged. Reuse its controller, map, and engine abstractions rather than duplicating the synth chain. Add only optional, backward-compatible interfaces to shared controller code where needed, and check that the existing cgsSynth still works.
- Reuse the synth controller's existing TUIO input on UDP port 3333 for XY gesture data.
- Coordinate mapping needs to account for the existing cgsSynth transform: X uses the TUIO X value directly, while Y is inverted and multiplied by 1.42. The Python TUIO adapter will compensate using the gesture area's aspect ratio so equal screen distances map to equal XY distances in Max. Keep the existing cgsSynth transform unchanged.
- Add a small message path from the app to Max for keyboard note events, avoiding virtual MIDI routing software. Max routes these events into its existing note handling.
- Gesture and note control remain app-to-Max. Max now sends a separate feature return stream to the app on UDP 3335; it does not send a ready heartbeat.
- Max and the Surface host patch are started manually. The app does not launch Max; gesture and note events are sent without waiting for a reply. Events sent while Max is closed are dropped by UDP and are not queued.
- `Surface/app.py` has a `REQUIRE_MAX_HANDSHAKE` switch, disabled because this host sends feature telemetry but no `/circle/ready` heartbeat. Enable it only after Max sends that heartbeat again.
- Keep transport code separate from gesture processing and UI code so future mechanical XY input can use the same processing and Max communication components.

## CGL telemetry and plotter-style readouts

The Surface host sends Max feature channels to the app as `/circle/feature (channel, value)` over UDP 3335. `mc.snapshot~ 100` samples at 10 Hz; the app assembles the 90 channel values into five 18-value groups. Preserve cgsSynth's configured `ratiosOfInterest` set: `1, 1.5, 2, 3, 4`; denominator-3 ratios are out of scope. Each feature group is ordered `E`, `Wr`, `W0`, `Asum`, `Abal`, `Phi`, then six Cartesian shape values for each of the low- and high-frequency ellipses. CGL analysis and its parameter conversion remain in Max.

As complete feature frames arrive during a local gesture, update the displayed plotter-style parameters and derived curve from the highest-energy group. On release, retain the last valid set and mark the gesture idle; replace it when the next gesture produces valid parameters. Ignore frames while idle so Max's decaying feature values do not erase the last curve.

| Plotter parameter | Mapping from active Max feature group |
|---|---|
| `N/M` | Canonical numerator and denominator for `Wr` (for example, `1.5` as `3/2`) |
| `omega0` | `W0 / Wr`; Max's extractor labels the higher frequency `W0`, while the plotter uses `omega0` for the lower frequency |
| `A0` | `Asum / 2` |
| `Ar` | `2 * Abal - 1` |
| `S1`, `tau1` | Invert the low-frequency ellipse's six Cartesian shape values with `cartToTauS` for display reconstruction |
| `S2`, `tau2` | Invert the high-frequency ellipse's six Cartesian shape values with `cartToTauS` for display reconstruction |
| `phi` | `Phi`, with phase wrapping/sign convention to be checked against a known synthetic gesture |
| — | `E` has no corresponding plotter slider; it may be retained as a diagnostic if useful |

The phase and frequency conventions must be validated against a known synthetic gesture before treating the readouts as exact. The inverse shape conversion is unstable for `tau` near a perfect circle; the Cartesian values themselves remain well-behaved, but the UI should treat `tau` as immaterial near `|S| = 1`.

The CGS curve is reconstructed for display in Python using the plotter's Model A ellipse equations and the selected highest-energy Max feature group. It is centered and fitted to the canvas with equal pixel scale. This renderer does not feed Max or perform CGL feature extraction. `Raw` and `CGS` visibility are controlled independently. The `Phi` phase convention still needs comparison against a known synthetic gesture in Max.

## First sound milestone (completed)

Create a minimal working vertical slice proving responsive gesture input and keyboard events from the app to Max, with audible output. Include the agreed basic layout and XY readout. This was the original one-way sound milestone; feature telemetry and the derived ellipse overlay are the follow-on milestone.

The first milestone must be capable of sending gesture and pitch inputs and producing sound.

## Acceptance criteria

- On the laptop, the app sends live gesture positions through Max's existing TUIO path and Max responds with sound.
- The app displays the normalized XY values it sends. Max-to-Surface telemetry is not part of this milestone.
- The C4–B4 keyboard follows the agreed latch and replacement behaviour, and app shutdown does not leave a note sounding.
- Mouse input works during laptop development. Touch and pen input are checked on the Surface.
- The raw trace is plotted only if the core integrations are working; if included, it remains visible after release until replaced by the next gesture.

## Verification notes

Max 9 is installed. The repo's `Circle` package is linked from `C:\Users\alexb\OneDrive\Documents\Max 9\Packages\Circle` to the repository's `Circle` folder. The user opened `circleApp_cgsSynth.maxpat`; its console reported `udpreceiver: binding to port 3333`, and Windows confirmed Max bound that UDP port. This confirms the receiver is listening, but an app-generated gesture packet and resulting sound have not yet been verified.

Surface touch latency and tracking quality require manual evaluation on the Surface Pro 4. Initial keyboard and telemetry schemas may be designed without Matt's approval; any necessary Max patch changes should be coordinated with him.

## Surface Max bridge

`Circle/extras/circleApp_Surface.maxpat` is a separate host copied from `circleApp_cgsSynth.maxpat`; the original host patch is unchanged. The shared controller's added inputs are optional, and its default mode leaves the existing MIDI paths enabled. Gesture input uses the controller's existing TUIO receiver on UDP 3333. Keyboard OSC arrives on UDP 3334 as `/circle/note (pitch, velocity)`. The Surface host routes the message through `unpack 0. 0.` into separate float inlets on the existing note manager. Surface mode closes the Minilab's external MIDI note, pad, CC, and bend inputs. The host samples the controller's 90-channel feature output at 10 Hz and sends `/circle/feature (channel, value)` to UDP 3335. It does not send a ready heartbeat.

Keep X direct and compensate the app's TUIO Y values so the existing Max transform produces gesture-canvas height/width scaling. For canvas-normalized `y_canvas`, height `H`, and width `W`, send `y_tuio = 1 - (1 - y_canvas) * (H / W) / 1.42`.
