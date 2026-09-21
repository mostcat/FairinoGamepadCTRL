# Fairino Gamepad CTRL

Control a Fairino 6-axis collaborative robot directly via **StartJOG** using any Bluetooth / USB gamepad (Xbox, PS4, Switch Pro, 8BitDo, etc.).

Hacker-terminal style GUI. Bilingual (中文 / EN) via the top-right toggle. Force feedback rumble on errors, jog failures and soft-limit hits. Real-time command log (last 30).

---

## Requirements

| Item | Version / Note |
|------|---------------|
| OS | Windows 10 / 11 |
| Python | >= 3.8 |
| pygame | >= 2.0 — `pip install pygame` |
| Fairino Python SDK | `pip install fairino` |
| Robot | Fairino FR05 / FR07 / FR10 / etc. — connected via TCP |
| Gamepad | Any HID controller recognised by SDL (Xbox 360/One/Series X, PS4/PS5, Switch Pro, 8BitDo…) |

## Quick Start

```bash
# 1. Install dependencies
pip install pygame fairino

# 2. Confirm robot IP — teach pendant → Settings → Network

# 3. Connect your gamepad (USB directly or Bluetooth pairing). Wait until Windows shows "Ready".

# 4. Run (--robot-ip is required, --joystick-id is optional, default 0)
python test_gamepad_control.py --robot-ip 192.168.1.222
# For multiple gamepads, specify the ID:
python test_gamepad_control.py --robot-ip 192.168.1.222 --joystick-id 1

# 5. The console prints "ready. press any button on gamepad..." — you're good.
```

> ⚠️ `--robot-ip` is a **required argument** with no default — it must be supplied explicitly. `--joystick-id` is optional and defaults to `0`.
> ⚠️ Make sure the robot is in **Auto mode + Servo ON** before moving. Simulator environments have no such restriction.

---

## Basic Setup Procedure

1. **Network connectivity** — Connect the PC to the robot controller via Ethernet. `ping 192.168.1.222` (example IP) should reply. If the IP differs, change it on the controller and pass it via `--robot-ip` at launch.
2. **Power on the controller** — Switch on the main breaker; wait until the teach pendant lights up and shows the main screen.
3. **Switch to Auto mode** — Teach Pendant → System Settings → Mode Switch → **Auto**. Manual mode rejects external programs.
4. **Release E-stop + Servo ON** — Release the physical emergency-stop button, then tap "Servo ON" on the teach pendant. The status bar must show `Servo ON`.
5. **Install Python deps** — `pip install pygame fairino`.
6. **Connect the gamepad** — Plug in via USB or pair over Bluetooth. A gamepad icon should appear in Windows "Devices and Printers".
7. **Verify the gamepad** — See the next section.
8. **Launch the program** — `python test_gamepad_control.py --robot-ip <robot_ip>`. Once you see `ready. press any button on gamepad...`, you're good to go.

---

## Gamepad Verification

Before driving the robot, **use the online gamepad tester to confirm every stick / trigger / button responds correctly** — a faulty gamepad can cause unintended motion:

> 🎮 **[https://hardwaretester.com/gamepad](https://hardwaretester.com/gamepad)**

Open the URL and press any button on your gamepad to start. Check:

- Left/right stick X/Y recenter to zero and reach full range
- LT / RT triggers travel linearly across the full pull
- ABXY / LB RB / Select Start / D-pad are all recognised
- Rumble test (the site fires one rumble pulse)

If anything is off, fix the gamepad or driver first — never operate the robot with a broken controller.

---

## Button Mapping

### Mode 1 — Cartesian (CARTESIAN)

| Input | Function |
|-------|----------|
| Left stick Y | X axis FWD / REV |
| Left stick X | Y axis LEFT / RIGHT |
| Right stick Y | Z axis UP / DOWN |
| Right stick X | Rx rotation |
| LT trigger | Ry negative |
| RT trigger | Ry positive |
| D-pad ↑ / ↓ | Rz positive / negative |
| **LB / RB** | **No effect in Cartesian mode (grayed out)** |
| A | Cycle coordinate system BASE → TOOL → WOBJ |
| B | Emergency stop (`ImmStopJOG`) |
| X | Speed +10% |
| Y | Fault reset (`ResetAllError`) |
| Select | Switch to Joint mode |
| Start | Home: clear faults first, then prefer multi-axis `MoveJ`; fall back to single-axis from J6 |

### Mode 2 — Joint Space (JOINT)

| Input | Function |
|-------|----------|
| Left stick Y | J4 |
| Left stick X | J5 |
| Right stick Y | J3 |
| Right stick X | J6 |
| LT / RT | J4 negative / positive |
| LB / RB | J3 negative / positive |
| D-pad ↑ / ↓ | J1 negative / positive |
| D-pad ← / → | J2 negative / positive |
| A | Switch to Cartesian mode |
| B | Emergency stop |
| X | Speed +10% |
| Y | Fault reset |
| Select | Switch to Cartesian mode |
| Start | Home: clear faults first, then prefer multi-axis `MoveJ`; fall back to single-axis from J6 |

### Velocity Curve

Stick deflection → `norm = (amplitude - DEAD_ZONE) / (1 - DEAD_ZONE)` → `vel = norm^0.5 × JOG_VEL_MAX`

The gamma=0.5 curve makes small deflections feel snappier: 30% stick → 55% speed (vs. 30% with a linear curve).

---

## Panel Layout

```
┌────────────────────────────────────────────────────────┐
│ > MODE: CARTESIAN  COORD: BASE              [EN/中文] │  ← language toggle
├────────────────────────────────────────────────────────┤
│  == GAMEPAD ==          │  == ROBOT ==                │
│  L-Y  X_AXIS ━━━        │  MODE=... VEL=... STICK=... │
│  L-X  Y_AXIS ━━         │  [TCP]                      │
│  ...                    │    X / Y / Z / Rx / Ry / Rz │
│  A  [COORD]             │  J1 ████████░░░  45.0d      │
│  B  [STOP]             │  J2 ...                      │
│  ...                   │  ...                         │
├────────────────────────────────────────────────────────┤
│ [-] COMMAND LOG  (last 30)                            │
│ [12:03:21] StartJOG  X d=1 v=35                       │
│ [12:03:23] ImmStopJOG  AXIS ref=2 nb=1 tags=['X']     │
│ ...                                                   │
├────────────────────────────────────────────────────────┤
│ [-] HELP / KEYMAP                                     │
├────────────────────────────────────────────────────────┤
│ SEL=MODE  A=COORD  B=STOP  ...                        │
└────────────────────────────────────────────────────────┘
```

## Force-Feedback Rumble

| Scenario | Effect |
|----------|--------|
| B button emergency stop | Long 350ms strong-motor rumble |
| Joint hits soft limit | 3 pulses (100ms × 3, 60ms gap each) |
| `StartJOG` returns non-zero | Short 150ms weak hint |
| Start HOME fails | Medium 250ms rumble |

Uses `pygame.joystick.Joystick.rumble(strong, weak, duration_ms)`. Cheap / Bluetooth gamepads that don't support rumble are auto-detected and skipped silently.

---

## Configuration (top of the file)

| Constant | Default | Description |
|----------|---------|-------------|
| `--robot-ip` (CLI) | **no default, required** | Controller IP, passed via command line |
| `--joystick-id` (CLI) | `0` | Pick which controller if multiple are plugged in (optional) |
| `DEAD_ZONE` | `0.15` | Stick center dead zone |
| `JOG_DIST` | `300.0` | Distance fed to `StartJOG` (mm or deg depending on ref frame) |
| `JOG_VEL_DEFAULT` | `20` | Speed % at boot |
| `JOG_VEL_MAX` | `100` | Full-stick speed ceiling |
| `JOG_ACC` | `100` | Acceleration |
| `VEL_RESTART_THRESHOLD` | `5` | Speed delta below this won't restart a running JOG |
| `CONTROL_HZ` | `30` | JOG / RPC tick rate |
| `RENDER_FPS` | `30` | GUI draw rate |
| `SOFT_LIMIT` | see code | 6-axis hard-limit protection table |
| `SOFT_MARGIN` | `1.0` | Margin inside the hard limits (simulator OK at 1.0, real robot ≈ 5.0) |
| `HOME_JOINTS_OVERRIDE` | `[65.349, -84.108, -115.447, -53.205, 90.854, -21.0]` | Home target joints (fixed per the multi-axis page) |
| `LOG_MAX_LINES` | `30` | Rolling log buffer size |
| `WIN_W / WIN_H` | `960×860` | Window size |

### HOME Joints

The home target joints are fixed strictly per the multi-axis page:

```python
HOME_JOINTS_OVERRIDE = [65.349, -84.108, -115.447, -53.205, 90.854, -21.0]
# J1=65.349  J2=-84.108  J3=-115.447  J4=-53.205  J5=90.854  J6=-21
```

### Start Home Procedure

Pressing **Start** runs the following homing strategy; every step is logged in the LOG panel:

1. **Clear faults** — call `ResetAllError()` to clear any active controller alarm.
2. **Prefer multi-axis** — call `MoveJ(target, vel=50)` so all 6 axes solve home together. If it reaches the target, done.
3. **Fallback: single-axis** — if multi-axis `MoveJ` returns non-zero or doesn't reach the target, home one axis at a time **from J6 down to J1** (other axes hold their current position).
4. **Real-time anomaly monitoring** — after each axis's `MoveJ`, poll the joint position:
   - joint stops moving for ~2 s (stuck / limit hit) → anomaly;
   - not reached within 15 s → timeout;
   - cannot read joint data → anomaly.
5. **Clear on anomaly** — on anomaly, immediately `ImmStopJOG()` + `ResetAllError()` to clear the current adjustment state, then continue to the next axis.

Log keywords: `HOME` (homing main flow), `HOME_CLR` (state clear), `METHOD=` (homing method).

---

## Main-Loop Architecture

Stick responsiveness is the top priority — the loop is strictly layered by **priority**:

```
┌─ 120Hz raw input capture ──┐   Axis / hat / button reads, zero RPC, zero sleep
│  joy.get_axis / get_hat     │   ~8 ms per pass, always runs first
└─────────────────────────────┘
          ↓ every while iteration
┌─ event pump ───────────────┐   pygame events: quit, ESC, mouse click (lang toggle)
└─────────────────────────────┘
          ↓
┌─ 10Hz cache refresh ──────┐   GetActualTCPPose / GetActualJointPosDegree
└─────────────────────────────┘   independent tick, failures swallowed
          ↓
┌─ 30Hz control tick ───────┐   _process_axes / _process_hat / _process_buttons / _check_limits
│  StartJOG / ImmStopJOG      │   sleeps reduced to 2 ms (simulator)
└─────────────────────────────┘
          ↓
┌─ 30Hz render tick ─────────┐   read cache only — **no RPC inside draw**
│  _draw_window()             │   stick bars, TCP, joint bars, log, help
└─────────────────────────────┘
```

**Key insight**: the render tick never calls RPC. If a `GetActual*` call blocks, the UI keeps painting the last cached values at 30 fps while the control tick stays responsive.

---

## Sample Log Output

```
[12:03:18] CONNECT  -> OK 192.168.1.222
[12:03:18] RESET_ALL_ERR -> 0
[12:03:18] GAMEPAD  -> id=0 Xbox 360 Controller
[12:03:19] HOME     -> MANUAL [65.349, -84.108, -115.447, -53.205, 90.854, -21.0]
[12:03:19] INIT     -> MODE=JOINT VEL=20%
[12:03:25] SELECT   -> MODE CARTESIAN
[12:03:26] StartJOG -> X d=1 v=35
[12:03:28] ImmStopJOG -> AXIS ref=2 nb=1 tags=['X']
[12:03:30] HOME     -> START target=[65.349, -84.108, -115.447, -53.205, 90.854, -21.0]
[12:03:30] HOME     -> ResetAllError ret=0
[12:03:30] HOME     -> METHOD=multi-axis MoveJ
[12:03:32] HOME     -> DONE multi-axis MoveJ OK
```

Fallback log when multi-axis fails:

```
[12:03:30] HOME     -> METHOD=multi-axis MoveJ
[12:03:31] HOME     -> multi-axis MoveJ FAIL ret=-1, fallback single-axis
[12:03:31] HOME     -> METHOD=single-axis from J6 to J1
[12:03:31] HOME     -> J6 MoveJ -10.000 -> -21.000
[12:03:33] HOME     -> J6 OK -> -21.000
[12:03:33] HOME     -> J5 MoveJ 80.000 -> 90.854
[12:03:34] HOME     -> J5 STUCK at 85.200 (target 90.854)
[12:03:34] HOME     -> J5 ANOMALY detected, clear & continue
[12:03:34] HOME_CLR -> ImmStop+ResetAllError ret=0
[12:03:34] HOME     -> J4 MoveJ -50.000 -> -53.205
...
[12:03:40] HOME     -> DONE single-axis sequence finished
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "RPC connect failed" at boot | Wrong IP / controller offline | Verify `--robot-ip`, `ping <robot_ip>`, check teach pendant networking |
| Stick bars don't move | Gamepad ID ≠ 0 | Add `--joystick-id N` at launch, or re-plug and check Windows Device Manager enumeration order |
| Chinese text renders as boxes | Font missing glyphs | Make sure `simhei.ttf` (SimHei) exists in `C:/Windows/Fonts/` |
| `StartJOG` returns non-zero | Robot not in Auto / E-stop latched | Switch Auto + release E-stop + Servo ON |
| Auto-stops at joint limit | Normal protection | Widen `SOFT_LIMIT` (simulator only) or reduce `SOFT_MARGIN` |
| No rumble at all | Gamepad unsupported / missing driver | Most cheap Bluetooth pads can't rumble — program skips silently |
| Log scrolls too fast | Stick drift / tremor | Gamma curve + `DEAD_ZONE=0.15` should absorb most of it |

---

## Fairino SDK Functions Used

- `Robot.RPC(ip)` — open XML-RPC connection
- `StartJOG(ref, nb, direction, dist, vel, acc)` — continuous point-to-point jog
- `ImmStopJOG()` — stop all JOGs immediately
- `GetActualTCPPose()` — current TCP pose
- `GetActualJointPosDegree()` — current joint angles (deg)
- `MoveJ(joints, tool, user, vel)` — joint-space straight-line motion
- `ResetAllError()` — clear all faults

---

## Disclaimer

This project is intended for technical demonstration and learning purposes only and **does not constitute any form of safety guarantee**. A robot arm is high-speed moving equipment; improper operation may cause equipment damage, property loss, or personal injury.

- Before using this program, please **fully understand the safety operating procedures of the robot arm** and read the manufacturer's official manual.
- Always test in an **environment with physical safeguards**, and ensure the operator can reach the emergency-stop button at all times.
- The author(s) shall not be liable for any direct or indirect losses arising from the use or misuse of this program.
- Users assume all risks associated with use; running this program constitutes acceptance of these terms.

**By running this software you acknowledge that you have read and accepted the disclaimer above.**
