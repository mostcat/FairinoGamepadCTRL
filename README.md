# Fairino Gamepad CTRL

使用蓝牙 / USB 游戏手柄（Xbox、PS4、Switch Pro 等）通过 `StartJOG` 点动接口直接控制法奥六轴协作机械臂。

GUI 采用黑客终端风格，支持中英文切换、手柄震动反馈、实时指令日志。

---

## 运行环境

| 项目 | 版本 / 说明 |
|------|------------|
| 操作系统 | Windows 10 / 11 |
| Python | >= 3.8 |
| pygame | >= 2.0（`pip install pygame`） |
| Fairino Python SDK | `pip install fairino` |
| 机器人 | 法奥 FR05 / FR07 / FR10 等，已开启 Modbus Slave 或 TCP 直连 |
| 手柄 | 任何被 SDL 识别的 HID 手柄（Xbox 360/One/Series X、PS4/PS5、Switch Pro、8BitDo 等） |

## 快速启动

```bash
# 1. 安装依赖
pip install pygame fairino

# 2. 确认机械臂 IP — 打开 teach pendant → 设置 → 网络

# 3. 连接手柄（蓝牙配对或 USB 直插），等系统识别完成

# 4. 启动程序（--robot-ip 为必填，--joystick-id 可选，默认 0）
python test_gamepad_control.py --robot-ip 192.168.1.222
# 多手柄环境可指定手柄 ID：
python test_gamepad_control.py --robot-ip 192.168.1.222 --joystick-id 1

# 5. 程序会显示 "ready. press any button on gamepad..."，即可操作
```

> ⚠️ `--robot-ip` 为**必填参数**，无默认值，必须显式提供；`--joystick-id` 可选，未指定时默认 `0`。
> ⚠️ 启动前请确保机械臂处于 **Auto 模式 + Servo ON**。模拟器环境无此限制。

---

## 基本配置过程

1. **网络连通** — 用网线把 PC 接到机械臂控制器，`ping 192.168.1.222`（示例 IP）能通即可。IP 不一致就改控制器端，启动时通过 `--robot-ip` 传入。
2. **控制器上电** — 打开控制柜主开关， Teach Pendant 屏幕点亮后进入主界面。
3. **切换 Auto 模式** — Teach Pendant → 系统设置 → 模式切换 → **Auto**。手动模式无法执行外部程序。
4. **松开急停 + Servo ON** — 释放物理急停按钮，在 Teach Pendant 上点击"伺服上电"。屏幕状态栏应显示 `Servo ON`。
5. **安装 Python 依赖** — `pip install pygame fairino`。
6. **连接手柄** — USB 直插或蓝牙配对。Windows "设备和打印机"里能看到手柄图标即已识别。
7. **验证手柄** — 见下一节。
8. **启动本程序** — `python test_gamepad_control.py --robot-ip <机械臂IP>`，看到 `ready. press any button on gamepad...` 后即可操作。

---

## 游戏手柄验证

正式操控机械臂前，**务必先用手柄测试网站确认所有按键 / 摇杆 / 扳机都正常响应**，避免因手柄故障导致误动作：

> 🎮 **[https://hardwaretester.com/gamepad](https://hardwaretester.com/gamepad)**

打开网址后按任一手柄按键即可开始检测，检查项：

- 左右摇杆 X/Y 轴是否归零、是否满幅
- LT / RT 扳机行程是否线性
- ABXY / LB RB / Select Start / 方向键是否全部识别
- 震动测试（网站会触发一次 rumble）

任一项异常请先换手柄或驱动，不要带病上机。

---

## 手柄按键映射

### 模式 1 — 笛卡尔空间 (CARTESIAN)

| 控件 | 功能 |
|------|------|
| 左摇杆 Y 轴 | X 轴前后（FWD / REV） |
| 左摇杆 X 轴 | Y 轴左右（LEFT / RIGHT） |
| 右摇杆 Y 轴 | Z 轴升降（UP / DOWN） |
| 右摇杆 X 轴 | Rx 旋转 |
| LT 扳机 | Ry 负方向 |
| RT 扳机 | Ry 正方向 |
| 方向键 ↑ / ↓ | Rz 正负旋转 |
| **LB / RB** | **在笛卡尔模式下无效果（灰显）** |
| A | 切换坐标系 BASE → TOOL → WOBJ |
| B | 急停（ImmStopJOG） |
| X | 速度 +10% |
| Y | 故障复位（ResetAllError） |
| Select | 切换到关节模式 |
| Start | 归位：先清错，再优先多轴联动 MoveJ；失败则从 J6 起逐轴回退 |

### 模式 2 — 关节空间 (JOINT)

| 控件 | 功能 |
|------|------|
| 左摇杆 Y 轴 | J4 |
| 左摇杆 X 轴 | J5 |
| 右摇杆 Y 轴 | J3 |
| 右摇杆 X 轴 | J6 |
| LT / RT | J4 负 / 正 |
| LB / RB | J3 负 / 正 |
| 方向键 ↑ / ↓ | J1 负 / 正 |
| 方向键 ← / → | J2 负 / 正 |
| A | 切换到笛卡尔模式 |
| B | 急停 |
| X | 速度 +10% |
| Y | 故障复位 |
| Select | 切换到笛卡尔模式 |
| Start | 归位：先清错，再优先多轴联动 MoveJ；失败则从 J6 起逐轴回退 |

### 速度曲线

摇杆幅度 → `norm = (amplitude - DEAD_ZONE) / (1 - DEAD_ZONE)` → `vel = norm^0.5 × JOG_VEL_MAX`

gamma=0.5 曲线让小幅度推杆更灵敏：30% 推杆 → 55% 速度（线性的话只有 30%）。

---

## 面板区域说明

```
┌────────────────────────────────────────────────────┐
│ > MODE: CARTESIAN  COORD: BASE            [EN/中文]│  ← 语言切换按钮
├────────────────────────────────────────────────────┤
│  == GAMEPAD ==      │  == ROBOT ==                 │
│  L-Y  X_AXIS ━━━    │  MODE=... VEL=...           │
│  L-X  Y_AXIS ━━     │  [TCP]                      │
│  ...                │    X / Y / Z / Rx / Ry / Rz │
│  A [切换坐标系]     │  J1 ████████░░ 45.0d        │
│  B [急停]          │  J2 ...                      │
│  ...               │  ...                         │
├────────────────────────────────────────────────────┤
│ [-] COMMAND LOG  (last 30)                         │
│ [12:03:21] StartJOG  X d=1 v=35                   │
│ [12:03:23] ImmStopJOG  AXIS ref=2 nb=1 tags=['X'] │
│ ...                                                │
├────────────────────────────────────────────────────┤
│ [-] HELP / KEYMAP                                  │
├────────────────────────────────────────────────────┤
│ SEL=MODE  A=COORD  B=STOP  ...                     │
└────────────────────────────────────────────────────┘
```

## 震动反馈

| 场景 | 震动效果 |
|------|---------|
| B 键急停 | 长震 350ms 强马达 |
| 关节到达软限位 | 哒-哒-哒 3 次脉冲（100ms × 3，间隔 60ms） |
| StartJOG 返回非 0 | 短震 150ms 弱提示 |
| Start 回 HOME 失败 | 中震 250ms |

使用 `pygame.joystick.Joystick.rumble(strong, weak, duration_ms)`。不支持震动的廉价 / 蓝牙手柄会自动跳过，不影响主流程。

---

## 配置项（文件顶部）

| 常量 | 默认值 | 说明 |
|------|--------|------|
| `--robot-ip` (CLI) | **无默认值，必填** | 机械臂控制器 IP，通过命令行参数传入 |
| `--joystick-id` (CLI) | `0` | 多手柄环境下选择第几个，可选参数 |
| `DEAD_ZONE` | `0.15` | 摇杆中立死区 |
| `JOG_DIST` | `300.0` | StartJOG 的运动距离（mm 或 deg） |
| `JOG_VEL_DEFAULT` | `20` | 启动时的速度百分比 |
| `JOG_VEL_MAX` | `100` | 摇杆满幅对应最大速度 |
| `JOG_ACC` | `100` | 加减速 |
| `VEL_RESTART_THRESHOLD` | `5` | 速度差值小于此值不重启 JOG |
| `CONTROL_HZ` | `30` | JOG/RPC 处理频率 |
| `RENDER_FPS` | `30` | GUI 绘制频率 |
| `SOFT_LIMIT` | 见代码 | 6 轴硬限位保护值 |
| `SOFT_MARGIN` | `1.0` | 软限位余量（模拟器可设 1.0，真机建议 5.0） |
| `HOME_JOINTS_OVERRIDE` | `[65.349, -84.108, -115.447, -53.205, 90.854, -21.0]` | 归位目标关节位（严格按多轴联动页面配置） |
| `LOG_MAX_LINES` | `30` | LOG 缓冲区行数 |
| `WIN_W / WIN_H` | `960×860` | 窗口分辨率 |

### HOME 关节位

归位目标关节位已严格按多轴联动页面配置固定：

```python
HOME_JOINTS_OVERRIDE = [65.349, -84.108, -115.447, -53.205, 90.854, -21.0]
# J1=65.349  J2=-84.108  J3=-115.447  J4=-53.205  J5=90.854  J6=-21
```

### Start 归位流程

按下 **Start** 键后，程序按以下策略归位，全程在 LOG 区记录归位方式与过程：

1. **清错** — 调用 `ResetAllError()` 清除控制器当前报警。
2. **优先多轴联动** — 调用 `MoveJ(target, vel=50)` 让 6 轴同时求解归位。若成功到位，流程结束。
3. **回退：逐轴调整** — 若多轴 `MoveJ` 返回非 0 或未到位，则从 **J6 → J1** 依次调用 `MoveJ` 单轴归位（其余轴保持当前位置）。
4. **实时异常监测** — 每一轴 MoveJ 后轮询关节位置：
   - 关节约 2 秒未动（卡死 / 到限位）→ 判定异常；
   - 超过 15 秒未到位 → 判定超时；
   - 读不到关节数据 → 判定异常。
5. **异常清除** — 检测到异常时立即 `ImmStopJOG()` + `ResetAllError()` 清除当前调整状态，然后继续下一轴。

LOG 关键字：`HOME`（归位主流程）、`HOME_CLR`（清除状态）、`METHOD=`（归位方式）。

---

## 主循环架构

为了保证摇杆响应即时，整个循环按**优先级**分层：

```
┌─ 120Hz 原始值采集 ──┐   摇杆 / hat / 按钮 不经过任何 RPC / sleep
│  joy.get_axis / get_hat │   每 ~8ms 执行一次
└────────────────────────┘
          ↓ 每个 while 迭代
┌─ event pump ──────────┐   pygame 事件、窗口关闭、ESC、语言切换按钮
└────────────────────────┘
          ↓
┌─ 10Hz 缓存刷新 ──────┐   _refresh_cache() → GetActualTCPPose / GetActualJointPosDegree
└────────────────────────┘   独立 tick，失败静默
          ↓
┌─ 30Hz control tick ──┐   _process_axes / _process_hat / _process_buttons / _check_limits
│  StartJOG / ImmStopJOG │   sleep 已缩到 2ms（模拟器）
└────────────────────────┘
          ↓
┌─ 30Hz render tick ────┐   只读缓存 → 不做任何 RPC
│  _draw_window()        │   摇杆条、TCP、关节条、LOG、帮助区
└────────────────────────┘
```

**关键设计**：render tick 只读缓存，不直接调 RPC。这意味着即使某个 `GetActual*` 阻塞了，UI 仍然以 30fps 刷新上一次的摇杆 / 状态。

---

## 日志示例

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

多轴失败时的回退日志示例：

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

## 故障排查

| 现象 | 可能原因 | 解决 |
|------|---------|------|
| 启动时 "RPC连接失败" | IP 不通 / 控制器未开 | 检查 `--robot-ip` 是否正确，ping 机械臂 IP，确认 Teach Pendant 已联网 |
| 手柄轴条不动 | 手柄识别 ID ≠ 0 | 启动时加 `--joystick-id N`，或插 USB 看设备管理器枚举顺序 |
| 中文显示为方框 | 字体无中文 | 确认 `simhei.ttf`（黑体）存在于 `C:/Windows/Fonts/` |
| StartJOG 返回非 0 | 机器人不在 Auto / 急停中 | 切 Auto + 松急停 + Servo ON |
| 关节到极限自动停 | 正常保护 | 把 `SOFT_LIMIT` 改大点（仅模拟器），或 `SOFT_MARGIN` 减小 |
| 震动没反应 | 手柄不支持 / 驱动问题 | 廉价蓝牙手柄多半不支持 rumble，程序已静默跳过 |
| LOG 刷屏 | 摇杆一直大幅抖动 | `_amplitude_to_vel` 的 gamma 曲线会减弱摇杆敏感端，`DEAD_ZONE=0.15` 也能过滤 |

---

## 依赖 Fairino SDK 的函数

- `Robot.RPC(ip)` — 建立 XML-RPC 连接
- `StartJOG(ref, nb, direction, dist, vel, acc)` — 持续点动
- `ImmStopJOG()` — 立即停止所有 JOG
- `GetActualTCPPose()` — 读取当前 TCP 位姿
- `GetActualJointPosDegree()` — 读取当前关节角（度）
- `MoveJ(joints, tool, user, vel)` — 关节空间直线运动
- `ResetAllError()` — 故障复位

---

## 免责条款

本项目仅作为技术演示与学习用途，**不构成任何形式的安全保证**。机械臂是高速运动设备，操作不当可能造成设备损坏、财产损失或人身伤害。

- 使用本程序前请**充分了解机械臂的安全操作规程**，阅读厂家官方手册。
- 务必在**有物理防护**的环境下试运行，操作人员应能随时触及急停按钮。
- 作者（们）不对因使用或误用本程序而产生的任何直接或间接损失负责。
- 用户自行承担一切使用风险；继续运行本程序即视为已阅读并接受本条款。

**By running this software you acknowledge that you have read and accepted the disclaimer above.**
