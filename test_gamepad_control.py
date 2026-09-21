"""
法奥机械臂游戏手柄控制程序  [HACKER TERMINAL MODE]
===================================================
pygame + Fairino Python SDK，StartJOG点动控制。
模式1 笛卡尔空间 | 模式2 关节空间 | Select切换 | 摇杆幅度定速。
"""

import os
import sys
import time
import argparse
import collections
import pygame
from fairino import Robot

os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"

# ==================== 配置 ====================
# ROBOT_IP 不再设置默认值，必须通过命令行 --robot-ip 显式传入
# JOYSTICK_ID 通过命令行 --joystick-id 可选传入，默认 0
DEAD_ZONE = 0.15
JOG_DIST = 300.0
JOG_VEL_DEFAULT = 20
JOG_VEL_MAX = 100
JOG_ACC = 100
VEL_RESTART_THRESHOLD = 5

CONTROL_HZ = 30
RENDER_FPS = 30

WIN_W, WIN_H = 960, 860

# --- 字体优先顺序（必须支持中文显示）---
FONT_CANDIDATES = [
    "C:/Windows/Fonts/simhei.ttf",          # 黑体 — 等宽 + 完整中文
    "C:/Windows/Fonts/msyh.ttc",            # 微软雅黑
    "C:/Windows/Fonts/simsun.ttc",           # 宋体
    "C:/Windows/Fonts/consola.ttf",          # Consolas 英文 fallback
    "C:/Windows/Fonts/cour.ttf",             # Courier New
]

SOFT_LIMIT = [
    -175.0, 175.0, -175.0, 175.0, -160.0, 160.0,
    -175.0, 175.0, -175.0, 175.0, -175.0, 175.0,
]
SOFT_MARGIN = 1.0  # 模拟器，减小软限位余量

COORD_REFS = [2, 4, 8]

# HOME 关节位（严格按图片配置：多轴联动页面的 J1~J6 值）
# J1=65.349  J2=-84.108  J3=-115.447  J4=-53.205  J5=90.854  J6=-21
HOME_JOINTS_OVERRIDE = [65.349, -84.108, -115.447, -53.205, 90.854, -21.0]
LOG_MAX_LINES = 30

# --- 黑客风配色 ---
BG        = (10, 10, 10)       # 黑
FG_GREEN  = (0, 255, 65)       # 矩阵绿 主色
FG_DIM    = (0, 150, 40)       # 暗绿 次级
FG_CYAN   = (0, 200, 200)      # 青 强调
FG_RED    = (255, 60, 60)      # 红 告警
FG_YELLOW = (220, 220, 80)     # 黄 提示
FG_GRAY   = (80, 100, 80)      # 灰 注释
FG_MUTED  = (40, 70, 40)       # 深灰 边框线

# --- 中英文字典 ---
LANG = {
    "cn": {
        "mode_cn": "笛卡尔空间",
        "mode_joint": "关节空间",
        "coord_base": "基坐标系",
        "coord_tool": "工具坐标系",
        "coord_wobj": "工件坐标系",
        "title_gamepad": "== 手柄状态 ==",
        "title_robot": "== 机械臂状态 ==",
        "btn_coord": "切换坐标系",
        "btn_stop": "急停",
        "btn_vel": "速度+10%",
        "btn_reset": "故障复位",
        "btn_j3_neg": "J3负向",
        "btn_j3_pos": "J3正向",
        "btn_mode": "切换模式",
        "btn_home": "回原点",
        "msg_mode": "模式",
        "msg_speed": "速度",
        "msg_stick": "摇杆",
        "msg_jog": "点动",
        "tcp_title": "[TCP位置]",
        "tcp_x": "X", "tcp_y": "Y", "tcp_z": "Z",
        "tcp_rx": "Rx", "tcp_ry": "Ry", "tcp_rz": "Rz",
        "log_title": "[ 命令日志 ]  (最近30条)",
        "help_title": "[ 操作说明 ]",
        "bar_mode": "当前模式",
        "bar_coord": "坐标系",
        "bar_exit": "退出",
        "bar_select": "切模式",
        "bar_a": "切坐标系",
        "bar_b": "急停",
        "bar_x": "速度+10%",
        "bar_y": "复位",
        "bar_start": "回原点",
        "lang_cn": "中文",
        "lang_en": "EN",
        "hazard_stop": "[急停]",
        "hazard_limit": "[限位保护]",
        "hazard_fail": "[失败]",
        "home_unknown": "无HOME数据",
    },
    "en": {
        "mode_cn": "CARTESIAN",
        "mode_joint": "JOINT",
        "coord_base": "BASE",
        "coord_tool": "TOOL",
        "coord_wobj": "WOBJ",
        "title_gamepad": "== GAMEPAD ==",
        "title_robot": "== ROBOT ==",
        "btn_coord": "COORD",
        "btn_stop": "STOP",
        "btn_vel": "VEL+10",
        "btn_reset": "RESET",
        "btn_j3_neg": "J3-",
        "btn_j3_pos": "J3+",
        "btn_mode": "MODE",
        "btn_home": "HOME",
        "msg_mode": "MODE",
        "msg_speed": "VEL",
        "msg_stick": "STICK",
        "msg_jog": "JOG",
        "tcp_title": "[TCP]",
        "tcp_x": "X", "tcp_y": "Y", "tcp_z": "Z",
        "tcp_rx": "Rx", "tcp_ry": "Ry", "tcp_rz": "Rz",
        "log_title": "[ COMMAND LOG ]  (last 30)",
        "help_title": "[ HELP / KEYMAP ]",
        "bar_mode": "SEL=MODE",
        "bar_coord": "A=COORD",
        "bar_exit": "ESC=QUIT",
        "bar_select": "SEL",
        "bar_a": "A",
        "bar_b": "B",
        "bar_x": "X",
        "bar_y": "Y",
        "bar_start": "STA",
        "lang_cn": "中文",
        "lang_en": "EN",
        "hazard_stop": "[ EMERGENCY STOP ]",
        "hazard_limit": "[ LIMIT ]",
        "hazard_fail": "[ FAIL ]",
        "home_unknown": "HOME UNKNOWN",
    },
}
# =============================================


class GamepadRobotController:

    def __init__(self, robot_ip, joystick_id=0):
        self._cmd_log = collections.deque(maxlen=LOG_MAX_LINES)
        self._click_regions = {}
        self._joystick_id = joystick_id

        print(f">>> connecting {robot_ip} ...")
        self.robot = Robot.RPC(robot_ip)
        time.sleep(2)
        print(">>> connected OK")

        self._log_cmd("CONNECT", f"OK {robot_ip}")

        try:
            ret = self.robot.ResetAllError()
            self._log_cmd("RESET_ALL_ERR", str(ret))
            time.sleep(0.5)
        except Exception as e:
            self._log_cmd("RESET_ALL_ERR", f"ERR {e}")

        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("FAIRINO // GAMEPAD CTRL  [B]=STOP  [ESC]=QUIT")

        # --- 加载等宽字体 ---
        self.font = None
        for fp in FONT_CANDIDATES:
            if os.path.exists(fp):
                try:
                    self.font = pygame.font.Font(fp, 16)
                    self.font_big = pygame.font.Font(fp, 20)
                    self.font_small = pygame.font.Font(fp, 13)
                    self.font_mono = self.font
                    break
                except Exception:
                    continue
        if self.font is None:
            self.font = pygame.font.Font(None, 18)
            self.font_big = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 15)
        self.line_h = self.font_small.get_height() + 2  # 15 来自 font_small

        pygame.joystick.init()
        count = pygame.joystick.get_count()
        if count == 0:
            self.screen.fill(BG)
            s = self.font_big.render("!! NO GAMEPAD DETECTED !!", True, FG_RED)
            self.screen.blit(s, (WIN_W // 2 - s.get_width() // 2, WIN_H // 2))
            pygame.display.flip()
            time.sleep(3)
            sys.exit(1)

        self.joy = pygame.joystick.Joystick(self._joystick_id)
        self.joy.init()
        self._log_cmd("GAMEPAD", f"id={self._joystick_id} {self.joy.get_name()}")

        self.control_mode = 2
        self.coord_idx = 0
        self.vel = JOG_VEL_DEFAULT
        self.running = True
        self.origin_pose = None
        self._jog_active = {}
        self._jog_vel = {}
        self._btn_prev = {}
        self._limit_checked = 0
        self._last_msg = ""
        self._msg_time = 0

        self._axis_raw = [0.0] * 6
        self._hat_raw = (0, 0)
        self._btn_raw = [False] * 16

        self._cached_pose = None
        self._cached_joints = None
        self._cache_time = 0

        self._help_collapsed = False
        self._log_collapsed = False
        self._lang = "cn"          # 当前语言 cn / en
        self._lang_btn_rect = None # 语言切换按钮矩形（点击检测）
        self._rumble_supported = False
        # 检测手柄震动能力（部分蓝牙/廉价手柄不支持）
        try:
            self._rumble_supported = self.joy.get_init()  # 仅占位，真正的检测在首次调用时做
        except Exception:
            pass

        # HOME 关节位
        if HOME_JOINTS_OVERRIDE is not None:
            self._home_joints = list(HOME_JOINTS_OVERRIDE)
            self._log_cmd("HOME", f"MANUAL {self._home_joints}")
        else:
            cur_joints = self._get_joints()
            if cur_joints:
                self._home_joints = [round(j, 2) for j in cur_joints[:6]]
                self._log_cmd("HOME", f"AUTO {self._home_joints}")
            else:
                self._home_joints = None
                self._log_cmd("HOME", "UNKNOWN")

        self._log_cmd("INIT", f"MODE={self._mode_name()} VEL={self.vel}%")
        self._update_origin_pose()
        self._log_cmd("ORIGIN", str(self._fmt_pose(self.origin_pose)))

    # ========== LOG ==========
    def _log_cmd(self, cmd, ret=""):
        ts = time.strftime("%H:%M:%S", time.localtime())
        self._cmd_log.append((ts, cmd, str(ret)))

    # ========== 手柄震动 ==========
    def _rumble(self, strong=0.8, weak=0.5, duration_ms=200):
        """
        触发手柄震动。任何异常（手柄不支持、断连等）都静默忽略。
        strong: 大马达强度 0.0~1.0
        weak:   小马达强度 0.0~1.0
        duration_ms: 持续毫秒
        """
        try:
            if self._rumble_supported:
                self.joy.rumble(strong, weak, duration_ms)
            else:
                # 首次探测
                self.joy.rumble(strong, weak, duration_ms)
                self._rumble_supported = True
        except Exception:
            # 不支持震动的手柄（比如部分蓝牙/廉价手柄）—— 标记以后不再尝试
            self._rumble_supported = False

    def _rumble_stop(self):
        """立即停止所有震动"""
        try:
            if self._rumble_supported:
                self.joy.rumble(0, 0, 0)
        except Exception:
            pass

    def _rumble_pulse(self, count=2, strong=0.8, weak=0.6, each_ms=120, gap_ms=80):
        """连续脉冲震动（比如限位时 哒-哒-哒 三下）"""
        for _ in range(count):
            self._rumble(strong, weak, each_ms)
            time.sleep(gap_ms / 1000.0)

    # ========== 多语言 ==========
    def L(self, key):
        return LANG.get(self._lang, {}).get(key, key)

    # ========== 基础方法 ==========
    def _mode_name(self):
        return self.L("mode_cn") if self.control_mode == 1 else self.L("mode_joint")

    def _coord_name(self):
        keys = ["coord_base", "coord_tool", "coord_wobj"]
        return self.L(keys[self.coord_idx])

    def _coord_ref(self):
        return COORD_REFS[self.coord_idx]

    def _fmt_pose(self, pose):
        if pose is None:
            return "N/A"
        return [round(v, 2) for v in pose]

    def _get_pose(self):
        result = self.robot.GetActualTCPPose()
        if isinstance(result, tuple) and len(result) >= 2:
            return result[1]
        elif isinstance(result, list):
            return result
        return None

    def _get_joints(self):
        result = self.robot.GetActualJointPosDegree()
        if isinstance(result, tuple) and len(result) >= 2:
            return result[1]
        elif isinstance(result, list):
            return result
        return None

    def _update_origin_pose(self):
        self.origin_pose = self._get_pose()
        if self.origin_pose is None:
            print(">>> WARN: origin pose unknown")

    def _set_msg(self, msg):
        self._last_msg = msg
        self._msg_time = time.time()

    def _refresh_cache(self):
        now = time.time()
        if now - self._cache_time < 0.15:
            return
        self._cache_time = now
        self._cached_pose = self._get_pose()
        self._cached_joints = self._get_joints()

    # ========== JOG ==========
    def _start_jog(self, ref, nb, direction, tag, vel=None):
        if vel is None:
            vel = self.vel
        key = (ref, nb, direction)
        if key in self._jog_active:
            old_vel = self._jog_vel.get(key, 0)
            if abs(vel - old_vel) < VEL_RESTART_THRESHOLD:
                return
            self.robot.ImmStopJOG()
            self._jog_active.clear()
            time.sleep(0.002)
        opp_key = (ref, nb, 1 - direction)
        if opp_key in self._jog_active:
            self.robot.ImmStopJOG()
            self._jog_active.clear()
            time.sleep(0.002)
        ret = self.robot.StartJOG(ref, nb, direction, JOG_DIST, vel, JOG_ACC)
        if ret != 0:
            self._set_msg(f"JOG FAIL err={ret}")
            self._log_cmd("StartJOG", f"FAIL ref={ref} nb={nb} d={direction} err={ret}")
            self._rumble(0.5, 0.3, 150)   # JOG失败: 短震一下提示
        else:
            self._jog_active[key] = tag
            self._jog_vel[key] = vel
            self._log_cmd("StartJOG", f"{tag} d={direction} v={vel}")

    def _stop_jog_axis(self, ref, nb):
        stopped = False
        stopped_tags = []
        for d in (0, 1):
            key = (ref, nb, d)
            if key in self._jog_active:
                stopped = True
                stopped_tags.append(self._jog_active[key])
                self._jog_active.pop(key, None)
                self._jog_vel.pop(key, None)
        if stopped:
            self.robot.ImmStopJOG()
            time.sleep(0.002)
            self._log_cmd("ImmStopJOG", f"AXIS ref={ref} nb={nb} tags={stopped_tags}")

    def _stop_all_jog(self):
        if self._jog_active:
            tags = list(self._jog_active.values())
            self.robot.ImmStopJOG()
            self._jog_active.clear()
            self._jog_vel.clear()
            time.sleep(0.002)
            self._log_cmd("ImmStopJOG", f"ALL tags={tags}")

    def _imm_stop(self):
        if self._jog_active:
            tags = list(self._jog_active.values())
            self._log_cmd("ImmStopJOG", f"INSTANT tags={tags}")
            self._rumble(0.9, 0.7, 350)   # 急停: 长震一下
        self.robot.ImmStopJOG()
        self._jog_active.clear()
        self._jog_vel.clear()

    # ========== 软限位 ==========
    def _check_limits(self):
        now = time.time()
        if now - self._limit_checked < 0.5:
            return
        self._limit_checked = now
        joints = self._cached_joints or self._get_joints()
        if not joints:
            return
        for i in range(min(len(joints), len(SOFT_LIMIT) // 2)):
            lo = SOFT_LIMIT[i * 2] + SOFT_MARGIN
            hi = SOFT_LIMIT[i * 2 + 1] - SOFT_MARGIN
            if joints[i] < lo or joints[i] > hi:
                self._set_msg(f"!! LIMIT J{i+1}={joints[i]:.1f}")
                self._rumble_pulse(3, strong=0.7, weak=0.5, each_ms=100, gap_ms=60)
                self._imm_stop()
                time.sleep(0.05)

    # ========== 按键去抖 ==========
    def _btn_pressed(self, idx):
        cur = self.joy.get_button(idx) if self.joy.get_numbuttons() > idx else False
        prev = self._btn_prev.get(idx, False)
        self._btn_prev[idx] = cur
        return cur and not prev

    # ========== 输入 ==========
    def _amplitude_to_vel(self, amplitude):
        if amplitude <= DEAD_ZONE:
            return 0
        norm = (amplitude - DEAD_ZONE) / (1.0 - DEAD_ZONE)
        vel = int((norm ** 0.5) * JOG_VEL_MAX)
        return max(5, vel)

    def _process_axes_cartesian(self):
        ref = self._coord_ref()
        n = self.joy.get_numaxes()
        if n > 1:
            val = -self.joy.get_axis(1)
            if abs(val) > DEAD_ZONE:
                self._start_jog(ref, 1, 1 if val > 0 else 0, "X", self._amplitude_to_vel(abs(val)))
            else:
                self._stop_jog_axis(ref, 1)
        if n > 0:
            val = self.joy.get_axis(0)
            if abs(val) > DEAD_ZONE:
                self._start_jog(ref, 2, 1 if val > 0 else 0, "Y", self._amplitude_to_vel(abs(val)))
            else:
                self._stop_jog_axis(ref, 2)
        if n > 3:
            val = -self.joy.get_axis(3)
            if abs(val) > DEAD_ZONE:
                self._start_jog(ref, 3, 1 if val > 0 else 0, "Z", self._amplitude_to_vel(abs(val)))
            else:
                self._stop_jog_axis(ref, 3)
        if n > 2:
            val = self.joy.get_axis(2)
            if abs(val) > DEAD_ZONE:
                self._start_jog(ref, 4, 1 if val > 0 else 0, "Rx", self._amplitude_to_vel(abs(val)))
            else:
                self._stop_jog_axis(ref, 4)
        if n > 4:
            lt = (self.joy.get_axis(4) + 1.0) / 2.0
            if lt > DEAD_ZONE:
                self._start_jog(ref, 5, 0, "Ry-", self._amplitude_to_vel(lt))
            else:
                self._stop_jog_axis(ref, 5)
        if n > 5:
            rt = (self.joy.get_axis(5) + 1.0) / 2.0
            if rt > DEAD_ZONE:
                self._start_jog(ref, 5, 1, "Ry+", self._amplitude_to_vel(rt))
            elif n <= 4 or (self.joy.get_axis(4) + 1.0) / 2.0 <= DEAD_ZONE:
                self._stop_jog_axis(ref, 5)

    def _process_axes_joint(self):
        n = self.joy.get_numaxes()
        if n > 1:
            val = -self.joy.get_axis(1)
            if abs(val) > DEAD_ZONE:
                self._start_jog(0, 4, 1 if val > 0 else 0, "J4", self._amplitude_to_vel(abs(val)))
            else:
                self._stop_jog_axis(0, 4)
        if n > 0:
            val = self.joy.get_axis(0)
            if abs(val) > DEAD_ZONE:
                self._start_jog(0, 5, 1 if val > 0 else 0, "J5", self._amplitude_to_vel(abs(val)))
            else:
                self._stop_jog_axis(0, 5)
        if n > 3:
            val = -self.joy.get_axis(3)
            if abs(val) > DEAD_ZONE:
                self._start_jog(0, 3, 1 if val > 0 else 0, "J3", self._amplitude_to_vel(abs(val)))
            else:
                self._stop_jog_axis(0, 3)
        if n > 2:
            val = self.joy.get_axis(2)
            if abs(val) > DEAD_ZONE:
                self._start_jog(0, 6, 1 if val > 0 else 0, "J6", self._amplitude_to_vel(abs(val)))
            else:
                self._stop_jog_axis(0, 6)
        if n > 4:
            lt = (self.joy.get_axis(4) + 1.0) / 2.0
            if lt > DEAD_ZONE:
                self._start_jog(0, 4, 0, "J4-", self._amplitude_to_vel(lt))
        if n > 5:
            rt = (self.joy.get_axis(5) + 1.0) / 2.0
            if rt > DEAD_ZONE:
                self._start_jog(0, 4, 1, "J4+", self._amplitude_to_vel(rt))

    def _process_axes(self):
        n = self.joy.get_numaxes()
        for i in range(min(n, 6)):
            self._axis_raw[i] = self.joy.get_axis(i)
        if self.control_mode == 1:
            self._process_axes_cartesian()
        else:
            self._process_axes_joint()

    def _process_hat(self):
        if self.joy.get_numhats() == 0:
            return
        hat = self.joy.get_hat(0)
        self._hat_raw = hat
        if self.control_mode == 1:
            if hat[1] == 1:
                self._start_jog(self._coord_ref(), 6, 1, "Rz+", self.vel)
            elif hat[1] == -1:
                self._start_jog(self._coord_ref(), 6, 0, "Rz-", self.vel)
            else:
                self._stop_jog_axis(self._coord_ref(), 6)
            if hat[0] == 1:
                self._start_jog(self._coord_ref(), 6, 1, "Rz+", self.vel)
            elif hat[0] == -1:
                self._start_jog(self._coord_ref(), 6, 0, "Rz-", self.vel)
            else:
                self._stop_jog_axis(self._coord_ref(), 6)
        else:
            if hat[1] == 1:
                self._start_jog(0, 1, 1, "J1+")
            elif hat[1] == -1:
                self._start_jog(0, 1, 0, "J1-")
            else:
                self._stop_jog_axis(0, 1)
            if hat[0] == 1:
                self._start_jog(0, 2, 1, "J2+")
            elif hat[0] == -1:
                self._start_jog(0, 2, 0, "J2-")
            else:
                self._stop_jog_axis(0, 2)

    def _process_buttons(self):
        nb = self.joy.get_numbuttons()
        for i in range(min(nb, 16)):
            self._btn_raw[i] = self.joy.get_button(i)

        # Select(6) -> 切模式
        if self._btn_pressed(6):
            self._stop_all_jog()
            time.sleep(0.1)
            self.control_mode = 2 if self.control_mode == 1 else 1
            self._log_cmd("SELECT", f"-> {self._mode_name()}")

        # A(0) -> 笛卡尔切坐标系 / 关节切模式
        if self._btn_pressed(0):
            self._stop_all_jog()
            time.sleep(0.1)
            if self.control_mode == 1:
                self.coord_idx = (self.coord_idx + 1) % len(COORD_REFS)
                self._log_cmd("A", f"COORD -> {self._coord_name()}")
            else:
                self.control_mode = 1
                self._log_cmd("A", f"MODE -> {self._mode_name()}")

        # B(1) -> 急停
        if nb > 1 and self.joy.get_button(1):
            if self._jog_active:
                self._imm_stop()
                self._log_cmd("B_STOP", "ImmStopJOG")
                self._set_msg("[ EMERGENCY STOP ]")

        # X(2) -> 速度+
        if self._btn_pressed(2):
            self.vel = min(100, self.vel + 10)
            self._log_cmd("X_VEL", f"+10% -> {self.vel}%")

        # Y(3) -> 故障复位
        if self._btn_pressed(3):
            self._imm_stop()
            time.sleep(0.2)
            ret = self.robot.ResetAllError()
            self._log_cmd("Y_RESET", f"ret={ret}")
            time.sleep(0.5)

        # LB(4)/RB(5) -> J3
        if nb > 4 and self.joy.get_button(4):
            self._start_jog(0, 3, 0, "J3-", self.vel)
        else:
            self._stop_jog_axis(0, 3)
        if nb > 5 and self.joy.get_button(5):
            self._start_jog(0, 3, 1, "J3+", self.vel)

        # Start(7) -> 归位（优先多轴联动，失败则从 J6 逐轴回退）
        if self._btn_pressed(7):
            self._stop_all_jog()
            time.sleep(0.2)
            self._go_home()

    # ========== 归位逻辑 ==========
    def _clear_homing_state(self):
        """清除当前归位调整状态：停止所有点动 + 复位错误"""
        try:
            self.robot.ImmStopJOG()
        except Exception:
            pass
        self._jog_active.clear()
        self._jog_vel.clear()
        try:
            ret = self.robot.ResetAllError()
            self._log_cmd("HOME_CLR", f"ImmStop+ResetAllError ret={ret}")
        except Exception as e:
            self._log_cmd("HOME_CLR", f"ERR {e}")
        time.sleep(0.3)

    def _wait_joint_reached(self, joint_idx, target, timeout=15.0, tol=0.5):
        """
        等待指定关节到位，期间实时监测异常。
        到位返回 True；异常（卡死/超时/读不到关节）返回 False。
        """
        start = time.time()
        last_pos = None
        stuck_count = 0
        pos = None
        while time.time() - start < timeout:
            cur = self._get_joints()
            if not cur or len(cur) <= joint_idx:
                time.sleep(0.2)
                continue
            pos = cur[joint_idx]
            # 到位判定
            if abs(pos - target) <= tol:
                return True
            # 异常检测：关节长时间不动（卡死 / 到达限位）
            if last_pos is not None and abs(pos - last_pos) < 0.01:
                stuck_count += 1
                if stuck_count >= 10:  # 约 2 秒未动视为异常
                    self._log_cmd("HOME", f"J{joint_idx+1} STUCK at {pos:.3f} (target {target:.3f})")
                    return False
            else:
                stuck_count = 0
            last_pos = pos
            time.sleep(0.2)
        pos_str = f"{pos:.3f}" if pos is not None else "N/A"
        self._log_cmd("HOME", f"J{joint_idx+1} TIMEOUT at {pos_str} (target {target:.3f})")
        return False

    def _go_home(self):
        """
        归位流程：
        1) 先清错；
        2) 优先多轴联动 MoveJ 一次性归位；
        3) 若多轴失败，则从 J6 开始逐一调整到目标位；
        4) 调整过程中实时监测异常，异常则立即清除当前调整状态并继续下一轴；
        5) 全程 LOG 记录归位方式及过程。
        """
        target = list(self._home_joints)
        self._log_cmd("HOME", f"START target={target}")

        # -- 1. 清除错误 --
        try:
            ret_rst = self.robot.ResetAllError()
            self._log_cmd("HOME", f"ResetAllError ret={ret_rst}")
        except Exception as e:
            self._log_cmd("HOME", f"ResetAllError ERR {e}")
        time.sleep(0.5)

        # -- 2. 优先多轴联动 MoveJ --
        self._log_cmd("HOME", "METHOD=multi-axis MoveJ")
        try:
            ret = self.robot.MoveJ(target, tool=0, user=0, vel=50)
        except Exception as e:
            ret = -1
            self._log_cmd("HOME", f"MoveJ EXC {e}")

        if ret == 0:
            # 等待多轴到位
            ok = self._wait_joint_reached(5, target[5], timeout=20.0, tol=1.0)
            if ok:
                self._log_cmd("HOME", "DONE multi-axis MoveJ OK")
                self._set_msg("HOME OK (multi-axis)")
                return
            else:
                self._log_cmd("HOME", "multi-axis not reached, fallback single-axis")
        else:
            self._log_cmd("HOME", f"multi-axis MoveJ FAIL ret={ret}, fallback single-axis")
            self._set_msg("!! MoveJ FAIL -> single-axis")
            self._rumble(0.7, 0.5, 250)

        # -- 3. 回退方案：从 J6 到 J1 逐轴调整 --
        self._log_cmd("HOME", "METHOD=single-axis from J6 to J1")
        for i in range(5, -1, -1):  # J6 -> J1
            cur = self._get_joints()
            if not cur or len(cur) < 6:
                self._log_cmd("HOME", f"J{i+1} ABORT: cannot read joints")
                continue

            # 当前已接近目标则跳过
            if abs(cur[i] - target[i]) <= 0.5:
                self._log_cmd("HOME", f"J{i+1} SKIP already at {cur[i]:.3f}")
                continue

            # 构造单轴目标（其余轴保持当前位置）
            single_target = list(cur[:6])
            single_target[i] = target[i]
            self._log_cmd("HOME", f"J{i+1} MoveJ {cur[i]:.3f} -> {target[i]:.3f}")

            try:
                ret = self.robot.MoveJ(single_target, tool=0, user=0, vel=30)
            except Exception as e:
                ret = -1
                self._log_cmd("HOME", f"J{i+1} MoveJ EXC {e}")

            if ret != 0:
                self._log_cmd("HOME", f"J{i+1} MoveJ FAIL ret={ret}, clear & continue")
                self._clear_homing_state()
                continue

            # 实时监测到位 / 异常
            ok = self._wait_joint_reached(i, target[i])
            if not ok:
                self._log_cmd("HOME", f"J{i+1} ANOMALY detected, clear & continue")
                self._clear_homing_state()
                continue

            self._log_cmd("HOME", f"J{i+1} OK -> {target[i]:.3f}")

        self._log_cmd("HOME", "DONE single-axis sequence finished")
        self._set_msg("HOME done (single-axis)")

    # ========== 渲染基础 ==========
    def _draw_text(self, text, x, y, font=None, color=FG_GREEN):
        if font is None:
            font = self.font
        surf = font.render(text, True, color)
        self.screen.blit(surf, (x, y))
        return surf.get_height()

    def _hline(self, x1, x2, y, color=FG_MUTED):
        pygame.draw.line(self.screen, color, (x1, y), (x2, y), 1)

    def _box(self, x, y, w, h, border_color=FG_DIM, fill_color=None):
        if fill_color is not None:
            pygame.draw.rect(self.screen, fill_color, (x, y, w, h))
        pygame.draw.rect(self.screen, border_color, (x, y, w, h), 1)

    def _draw_bar(self, x, y, w, h, ratio):
        self._box(x, y, w, h, FG_DIM, BG)
        cx = x + w // 2
        pygame.draw.line(self.screen, FG_MUTED, (cx, y), (cx, y + h), 1)
        if abs(ratio) > DEAD_ZONE:
            bar_w = int((abs(ratio) - DEAD_ZONE) / (1.0 - DEAD_ZONE) * (w // 2))
            bar_w = max(0, min(w // 2 - 1, bar_w))
            bar_color = FG_GREEN if ratio > 0 else FG_RED
            if ratio > 0:
                pygame.draw.rect(self.screen, bar_color, (cx + 1, y + 1, bar_w, h - 2))
            else:
                pygame.draw.rect(self.screen, bar_color, (cx - bar_w - 1, y + 1, bar_w, h - 2))

    def _draw_trigger_bar(self, x, y, w, h, ratio, color=FG_CYAN):
        self._box(x, y, w, h, FG_DIM, BG)
        if ratio > DEAD_ZONE:
            bar_w = int((ratio - DEAD_ZONE) / (1.0 - DEAD_ZONE) * (w - 2))
            bar_w = max(0, min(w - 2, bar_w))
            pygame.draw.rect(self.screen, color, (x + 1, y + 1, bar_w, h - 2))

    def _draw_collapsible_title(self, title, y, w, key):
        if key == "log":
            collapsed = self._log_collapsed
        else:
            collapsed = self._help_collapsed
        mark = "[+]" if collapsed else "[-]"
        full = f"{mark} {title}"
        y += self._draw_text(full, 10, y, self.font_big, FG_CYAN)
        self._hline(10, w - 10, y, FG_DIM)
        y += 2
        self._click_regions[key] = pygame.Rect(10, y - 22, w - 20, 26)
        return y + 2

    # ---------- 手柄列 ----------
    def _draw_gamepad_col(self, x, y, col_w):
        start_y = y
        y += self._draw_text(self.L("title_gamepad"), x, y, self.font_big, FG_CYAN)
        y += 2
        self._hline(x, x + col_w - 8, y)
        y += 6

        BAR_W = 150
        LBL_X = x + 12   # 右移约 1.5 个字符宽度
        BAR_X = x + 172
        VAL_X = BAR_X + BAR_W + 8

        if self.control_mode == 1:
            labels = [
                ("L-Y  X_AXIS ", 1),
                ("L-X  Y_AXIS ", 0),
                ("R-Y  Z_AXIS ", 3),
                ("R-X  RX     ", 2),
                ("LT   RX-     ", 4, True, FG_RED),
                ("RT   RX+     ", 5, True, FG_CYAN),
            ]
        else:
            labels = [
                ("L-Y  J4      ", 1),
                ("L-X  J5      ", 0),
                ("R-Y  J3      ", 3),
                ("R-X  J6      ", 2),
                ("LT   J4-     ", 4, True, FG_RED),
                ("RT   J4+     ", 5, True, FG_CYAN),
            ]

        for item in labels:
            lbl, ai = item[0], item[1]
            is_trigger = len(item) > 2 and item[2]
            trig_color = item[3] if len(item) > 3 else FG_CYAN
            val = self._axis_raw[ai] if ai < len(self._axis_raw) else 0
            if is_trigger:
                val = (val + 1.0) / 2.0
            elif ai in (1, 3):
                val = -val

            self._draw_text(lbl, LBL_X, y, self.font, FG_DIM)
            if is_trigger:
                self._draw_trigger_bar(BAR_X, y + 2, BAR_W, 10, val, trig_color)
            else:
                self._draw_bar(BAR_X, y + 2, BAR_W, 10, val)
            vel = self._amplitude_to_vel(abs(val))
            vs = f"{val:+.2f} {vel:3d}%" if abs(val) > DEAD_ZONE else f"{val:+.2f}    "
            self._draw_text(vs, VAL_X, y + 1, self.font, FG_GREEN)
            y += self.line_h

        # 方向键
        hat_u = {1: "^", -1: "v", 0: "."}
        hat_r = {1: ">", -1: "<", 0: "."}
        if self.control_mode == 1:
            hlabel = f"HAT: Rz [{hat_u.get(self._hat_raw[1])}{hat_r.get(self._hat_raw[0])}]"
        else:
            hlabel = f"HAT: J1[{hat_u.get(self._hat_raw[1])}] J2[{hat_r.get(self._hat_raw[0])}]"
        y += self._draw_text(hlabel, LBL_X, y, self.font, FG_YELLOW)
        y += 2

        # 按键 2×4 —— 按钮描述随语言切换
        if self.control_mode == 1:
            btn_funcs = [self.L("btn_coord"), self.L("btn_stop"), self.L("btn_vel"), self.L("btn_reset"),
                         self.L("btn_j3_neg"), self.L("btn_j3_pos"), self.L("btn_mode"), self.L("btn_home")]
            # 笛卡尔模式下 LB(4)/RB(5) 无效 —— 标记为灰显
            disabled_idx = {4, 5}
        else:
            btn_funcs = [self.L("btn_mode"), self.L("btn_stop"), self.L("btn_vel"), self.L("btn_reset"),
                         self.L("btn_j3_neg"), self.L("btn_j3_pos"), self.L("btn_mode"), self.L("btn_home")]
            disabled_idx = set()
        btn_names = ["A", "B", "X", "Y", "LB", "RB", "SEL", "STA"]

        bw = 90
        bh = 38
        gap_x = 6
        gap_y = 6
        rows, cols = 2, 4
        for r in range(rows):
            for c in range(cols):
                i = r * cols + c
                if i >= len(btn_names):
                    continue
                pressed = self._btn_raw[i] if i < len(self._btn_raw) else False
                bx = x + c * (bw + gap_x)
                by = y + r * (bh + gap_y)
                is_disabled = i in disabled_idx

                if is_disabled:
                    # 无效按钮：纯灰，无高亮
                    bg = BG
                    border = (40, 40, 45)
                    nc = (60, 60, 65)
                    fc = (50, 50, 55)
                elif pressed:
                    bg = (0, 40, 15)
                    border = FG_GREEN
                    nc = FG_GREEN
                    fc = FG_GREEN
                else:
                    bg = BG
                    border = FG_DIM
                    nc = FG_DIM
                    fc = FG_MUTED

                pygame.draw.rect(self.screen, bg, (bx, by, bw, bh))
                pygame.draw.rect(self.screen, border, (bx, by, bw, bh), 1)
                self._draw_text(btn_names[i], bx + 6, by + 3, self.font, nc)
                # 笛卡尔模式下 LB/RB 显示 "N/A"
                label_txt = "N/A" if is_disabled else btn_funcs[i]
                self._draw_text(label_txt, bx + 6, by + 18, self.font_small, fc)
        y += rows * (bh + gap_y) + 4

        return y - start_y

    # ---------- 机械臂列 ----------
    def _draw_robot_col(self, x, y, col_w):
        start_y = y
        y += self._draw_text(self.L("title_robot"), x, y, self.font_big, FG_CYAN)
        y += 2
        self._hline(x, x + col_w - 8, y)
        y += 6

        pose = self._cached_pose
        joints = self._cached_joints
        cur_vels = list(self._jog_vel.values())
        cur_vel = max(cur_vels) if cur_vels else 0
        jog_desc = ",".join(self._jog_active.values()) if self._jog_active else "IDLE"
        mode_tag = self._mode_name()
        if self.control_mode == 1:
            mode_tag += f"@{self._coord_name()}"

        # 固定状态行
        y += self._draw_text(
            f"MODE={mode_tag}  VEL={self.vel}%  STICK={cur_vel}%  JOG=[{jog_desc}]",
            x, y, self.font, FG_GREEN)
        y += 2

        # --- TCP位姿区（固定3行）---
        y += self._draw_text(self.L("tcp_title"), x, y, self.font_small, FG_DIM)
        if pose and len(pose) >= 6:
            y += self._draw_text(
                f"  X {pose[0]:9.2f}  Y {pose[1]:9.2f}  Z {pose[2]:9.2f}",
                x, y, self.font, FG_GREEN)
            y += self._draw_text(
                f"  Rx {pose[3]:8.2f}  Ry {pose[4]:8.2f}  Rz {pose[5]:8.2f}",
                x, y, self.font, FG_GREEN)
        else:
            y += self._draw_text("  -- TCP UNKNOWN --", x, y, self.font, FG_RED)
            y += self._draw_text("  --              --", x, y, self.font, FG_DIM)
        y += 2

        # --- 关节区（固定6行）---
        bar_w = 130
        for i in range(6):
            lo = SOFT_LIMIT[i * 2] + SOFT_MARGIN
            hi = SOFT_LIMIT[i * 2 + 1] - SOFT_MARGIN
            if joints and i < len(joints):
                val = joints[i]
                is_limit = val < lo or val > hi
                color = FG_RED if is_limit else FG_GREEN
                bar_ratio = (val - SOFT_LIMIT[i*2]) / (SOFT_LIMIT[i*2+1] - SOFT_LIMIT[i*2])
                bar_ratio = max(0, min(1, bar_ratio))
                label = f"J{i+1}: {val:7.2f}d"
            else:
                label = f"J{i+1}:  ------"
                color = FG_DIM
                bar_ratio = 0.5

            by = y
            self._draw_text(label, x, by, self.font, color)
            bx = x + 100
            self._box(bx, by + 2, bar_w, 10, FG_DIM, BG)
            fill_w = int(bar_ratio * (bar_w - 2))
            fc2 = FG_RED if (joints and i < len(joints) and (joints[i] < lo or joints[i] > hi)) else FG_GREEN
            pygame.draw.rect(self.screen, fc2, (bx + 1, by + 3, fill_w, 8))
            y += self.line_h

        y += 2
        # --- 消息行（固定1行）---
        if self._last_msg and (time.time() - self._msg_time) < 4.0:
            y += self._draw_text(f">> {self._last_msg}", x, y, self.font, FG_YELLOW)
        else:
            y += self._draw_text("", x, y, self.font, FG_GREEN)

        return y - start_y

    # ---------- LOG区 ----------
    def _draw_log_section(self, y, w, h):
        top = self._draw_collapsible_title(self.L("log_title"), y, w, "log")
        content_bot = y + h
        content_h = content_bot - top
        if content_h < 10:
            return y + h

        if self._log_collapsed:
            items = list(self._cmd_log)[-1:] if self._cmd_log else []
            bar_y = top
            bar_h = self.line_h + 4
            self._box(10, bar_y, w - 20, bar_h, FG_DIM, (15, 20, 15))
            if items:
                ts, cmd, ret = items[0]
                line = f"[{ts}] {cmd} -> {ret}"
                self._draw_text(line, 14, bar_y + 3, self.font_small, FG_DIM)
            return content_bot

        self._box(10, top, w - 20, content_h, FG_DIM, (8, 12, 8))

        items = list(self._cmd_log)
        line_h = self.font_small.get_height() + 1
        max_lines = (content_h - 4) // line_h
        visible = items[-max_lines:] if items else []

        by = top + 2
        for ts, cmd, ret in visible:
            ts_str = f"[{ts}] "
            cmd_str = f"{cmd}"
            ret_str = f" -> {ret}"
            self._draw_text(ts_str, 14, by, self.font_small, FG_DIM)
            tw = self.font_small.size(ts_str)[0]
            self._draw_text(cmd_str, 14 + tw, by, self.font_small, FG_GREEN)
            cw = self.font_small.size(cmd_str)[0]
            self._draw_text(ret_str, 14 + tw + cw, by, self.font_small, FG_CYAN)
            by += line_h

        return content_bot

    # ---------- 帮助区 ----------
    def _draw_help_section(self, y, w, h):
        top = self._draw_collapsible_title(self.L("help_title"), y, w, "help")
        content_bot = y + h
        content_h = content_bot - top
        if content_h < 10:
            return y + h

        if self._help_collapsed:
            return content_bot

        self._box(10, top, w - 20, content_h, FG_DIM, (8, 12, 8))

        if self.control_mode == 1:
            helps = [
                "[ MODE 1  CARTESIAN ]",
                "L-Y  X FWD/REV   L-X  X L/R",
                "R-Y  Z UP/DN     R-X  RX",
                "LT   RX-  RT RX+  HAT  RZ",
                "A    NEXT COORD  BASE>TOOL>WOBJ",
                "SEL  -> MODE 2   JOINTS",
            ]
        else:
            helps = [
                "[ MODE 2  JOINT ]",
                "L-Y  J4     L-X  J5",
                "R-Y  J3     R-X  J6",
                "LT   J4-    RT   J4+",
                "LB   J3-    RB   J3+",
                "HAT  J1(J2) SEL -> MODE 1",
            ]
        common = [
            "B=STOP  X=VEL+10  Y=RESET  STA=RESET+HOME",
            "Stick amplitude -> velocity 5-100%  gamma curve",
            "Dead zone 0.15  Auto stop on center",
        ]
        all_lines = helps + [""] + common

        line_h = self.font_small.get_height() + 1
        by = top + 3
        for line in all_lines:
            if by + line_h > content_bot - 2:
                break
            if line.startswith("[") and line.endswith("]"):
                color = FG_CYAN
            elif line == "":
                by += line_h
                continue
            else:
                color = FG_DIM
            self._draw_text(line, 14, by, self.font_small, color)
            by += line_h

        return content_bot

    # ---------- 顶层布局 ----------
    def _draw_window(self):
        self.screen.fill(BG)
        self._click_regions = {}

        margin = 10
        bottom_bar_h = 22
        row1_h = 280  # row1 固定高度
        top_h = 36    # 模式行高度（无标题）

        # ---- 顶部：仅模式行 ----
        y = margin
        # ---- 语言切换按钮（最右上角）----
        lang_btn_w = 66
        lang_btn_h = 26
        lang_btn_x = WIN_W - margin - lang_btn_w
        lang_btn_y = margin + 2
        self._lang_btn_rect = pygame.Rect(lang_btn_x, lang_btn_y, lang_btn_w, lang_btn_h)
        self._box(lang_btn_x, lang_btn_y, lang_btn_w, lang_btn_h, FG_GREEN, BG)
        toggle_txt = "EN" if self._lang == "cn" else "中文"
        self._draw_text(toggle_txt, lang_btn_x + 18, lang_btn_y + 5, self.font, FG_GREEN)

        # ---- 顶部模式行 ----
        mode_txt = f"> MODE: {self._mode_name()}"
        mode_color = FG_GREEN if self.control_mode == 1 else FG_CYAN
        y += self._draw_text(mode_txt, 10, y, self.font_big, mode_color)
        if self.control_mode == 1:
            rest = f"  COORD: {self._coord_name()}"
        else:
            rest = "  [JOINT MODE]"
        self._draw_text(rest, 10 + self.font_big.size(mode_txt)[0] + 8,
                       y - 20, self.font_big, FG_YELLOW)
        y += 4
        self._hline(margin, WIN_W - margin, y, FG_MUTED)
        y += 8

        # ---- row1 ----
        row1_top = y
        col_split = int(WIN_W * 0.46)   # GAMEPAD列更窄，ROBOT列更宽
        col_gap = 10

        self._draw_gamepad_col(margin, row1_top, col_split - margin)
        self._draw_robot_col(col_split + col_gap, row1_top, WIN_W - col_split - col_gap - margin)
        pygame.draw.line(self.screen, FG_MUTED,
                         (col_split, row1_top + 2),
                         (col_split, row1_top + row1_h - 2), 1)
        self._box(margin, row1_top, WIN_W - margin * 2, row1_h, FG_DIM)

        y = row1_top + row1_h + 8

        # ---- LOG区 ----
        bottom_bar_top = WIN_H - bottom_bar_h
        available = bottom_bar_top - y

        if self._log_collapsed:
            log_h = 36
        else:
            if self._help_collapsed:
                log_h = max(120, available - 4)
            else:
                log_h = 160

        log_h = min(log_h, available - 4)
        log_h = max(log_h, 36)

        y = self._draw_log_section(y, WIN_W, log_h)
        y += 4

        # ---- 帮助区 ----
        help_available = bottom_bar_top - y
        if self._help_collapsed:
            help_h = 32
        else:
            help_h = max(60, help_available - 2)

        help_h = min(help_h, help_available - 2)
        help_h = max(help_h, 32)
        self._draw_help_section(y, WIN_W, help_h)

        # ---- 底部 ----
        self._hline(margin, WIN_W - margin, WIN_H - bottom_bar_h - 2, FG_MUTED)
        if self._lang == "cn":
            bar_txt = "SEL=切模式  A=切坐标系  B=急停  X=速度+10%  Y=复位  STA=回原点  ESC=退出"
        else:
            bar_txt = "SEL=MODE  A=COORD  B=STOP  X=VEL+10  Y=RESET  STA=HOME  ESC=QUIT"
        self._draw_text(bar_txt, 10, WIN_H - bottom_bar_h + 4, self.font_small, FG_MUTED)

        pygame.display.flip()

    # ========== 主循环 ==========
    def run(self):
        print(">>> ready. press any button on gamepad...")
        control_interval = 1.0 / CONTROL_HZ   # 30Hz
        render_interval = 1.0 / RENDER_FPS    # 30Hz
        cache_interval = 0.15                 # 10Hz 缓存刷新
        last_control = 0
        last_render = 0
        last_cache = 0

        # 独立采集摇杆原始值的频率 —— 远高于 control，确保 UI 立即响应
        raw_interval = 1.0 / 120               # 120Hz 摇杆轮询
        last_raw = 0

        try:
            while self.running:
                now = time.time()

                # ---- [最高优先级] 摇杆原始值采集 ----
                # 在任何 RPC / sleep 之前执行，确保 UI 能立即反映摇杆状态
                if now - last_raw >= raw_interval:
                    last_raw = now
                    n = self.joy.get_numaxes()
                    for i in range(min(n, 6)):
                        self._axis_raw[i] = self.joy.get_axis(i)
                    if self.joy.get_numhats() > 0:
                        self._hat_raw = self.joy.get_hat(0)
                    nb = self.joy.get_numbuttons()
                    for i in range(min(nb, 16)):
                        self._btn_raw[i] = self.joy.get_button(i)

                pygame.event.pump()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        # 语言切换按钮
                        if self._lang_btn_rect and self._lang_btn_rect.collidepoint(event.pos):
                            self._lang = "en" if self._lang == "cn" else "cn"
                            continue
                        for key, rect in list(self._click_regions.items()):
                            if rect.collidepoint(event.pos):
                                if key == "log":
                                    self._log_collapsed = not self._log_collapsed
                                elif key == "help":
                                    self._help_collapsed = not self._help_collapsed
                                break

                # ---- [独立 tick] 缓存刷新（RPC） ----
                if now - last_cache >= cache_interval:
                    last_cache = now
                    try:
                        self._refresh_cache()
                    except Exception:
                        pass

                # ---- [control tick] JOG / 按键处理 ----
                if now - last_control >= control_interval:
                    last_control = now
                    try:
                        self._process_axes()
                        self._process_hat()
                        self._process_buttons()
                        self._check_limits()
                    except Exception as e:
                        print(f"control tick warn: {e}")

                # ---- [render tick] 绘制（只读缓存，不做 RPC）----
                if now - last_render >= render_interval:
                    last_render = now
                    try:
                        self._draw_window()
                    except Exception as e:
                        print(f"render tick warn: {e}")

                time.sleep(0.003)

        except KeyboardInterrupt:
            print("\n>>> interrupt")
        finally:
            self._rumble_stop()
            self._imm_stop()
            print(">>> all jog stopped")
            pygame.quit()
            print(">>> exit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fairino 6-axis robot gamepad controller (StartJOG)."
    )
    parser.add_argument(
        "--robot-ip", required=True,
        help="机械臂控制器 IP（必填，无默认值），例如 192.168.1.222"
    )
    parser.add_argument(
        "--joystick-id", type=int, default=0,
        help="手柄设备 ID（可选，默认 0）"
    )
    args = parser.parse_args()

    ctrl = GamepadRobotController(args.robot_ip, joystick_id=args.joystick_id)
    ctrl.run()
