import os, json, time, math, random, threading, platform
import tkinter as tk
from collections import deque
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import sys
from pathlib import Path


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR   = get_base_dir()
CONFIG_DIR = BASE_DIR / "config"
API_FILE   = CONFIG_DIR / "api_keys.json"

SYSTEM_NAME = "J.A.R.V.I.S"
MODEL_BADGE = "MARK XXXVII"

# ── Holographic Energy Orb palette ─────────────────────────────────────────
C_BG      = "#000508"
C_DARK    = "#000c12"
C_PANEL   = "#020e14"
C_GOLD    = "#ffaa00"
C_GOLD2   = "#ffcc44"
C_GOLD3   = "#ff8800"
C_AMBER   = "#ff6600"
C_EMBER   = "#ff4400"
C_GLOW    = "#ffd060"
C_DIM     = "#3a2800"
C_DIMMER  = "#0f0800"
C_TEXT    = "#ffe8a0"
C_GREEN   = "#aaff44"
C_RED     = "#ff3333"
C_MUTED   = "#ff3366"
C_BLUE    = "#80c8ff"
C_CYAN    = "#00e8ff"
C_ENERGY  = "#ff9900"


class JarvisUI:
    def __init__(self, face_path, size=None):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S — MARK XXXVII")
        self.root.resizable(False, False)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        W  = min(sw, 984)
        H  = min(sh, 816)
        self.root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.root.configure(bg=C_BG)

        self.W = W
        self.H = H

        # Orb is larger and centered more vertically
        self.ORB_R   = min(int(H * 0.30), 230)
        self.FCX     = W // 2
        self.FCY     = int(H * 0.42)

        self.speaking     = False
        self.muted        = False
        self.scale        = 1.0
        self.target_scale = 1.0
        self.halo_a       = 80.0
        self.target_halo  = 80.0
        self.last_t       = time.time()
        self.tick         = 0

        # Multiple latitude/longitude orbit rings for holographic sphere look
        self.orbit_angles = [random.uniform(0, 360) for _ in range(8)]
        self.orbit_tilts  = [i * 22.5 for i in range(8)]   # 0°,22.5°,...157.5°
        self.orbit_speeds = [random.uniform(0.4, 1.2) * random.choice([-1,1]) for _ in range(8)]

        self.scan_angle   = 0.0
        self.scan2_angle  = 120.0
        self.scan3_angle  = 240.0
        self.pulse_r      = []
        self.energy_nodes = self._init_energy_nodes()

        # Music spectrum bars (64 bars arranged in a ring around the orb)
        self.spectrum_bars = [random.uniform(0.02, 0.08) for _ in range(64)]
        self.spectrum_targets = [random.uniform(0.02, 0.08) for _ in range(64)]

        # Floating circuit debris
        self.debris = [self._new_debris() for _ in range(80)]

        # City-grid surface texture coordinates on the sphere
        self.city_nodes = self._init_city_nodes()

        self.status_blink = True
        self._jarvis_state = "INITIALISING"
        self.status_text   = "INITIALISING"

        self.typing_queue = deque()
        self.is_typing    = False
        self.on_text_command = None

        self._face_pil         = None
        self._has_face         = False
        self._face_scale_cache = None
        self._load_face(face_path)

        self.bg = tk.Canvas(self.root, width=W, height=H,
                            bg=C_BG, highlightthickness=0)
        self.bg.place(x=0, y=0)

        # Log panel – slimmer, placed at bottom
        LW  = int(W * 0.68)
        LH  = 90
        LOG_Y = H - LH - 78
        self.log_frame = tk.Frame(self.root, bg="#010a10",
                                  highlightbackground=C_DIM,
                                  highlightthickness=1)
        self.log_frame.place(x=(W - LW) // 2, y=LOG_Y, width=LW, height=LH)
        self.log_text = tk.Text(self.log_frame, fg=C_TEXT, bg="#010a10",
                                insertbackground=C_TEXT, borderwidth=0,
                                wrap="word", font=("Courier", 9), padx=10, pady=6)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")
        self.log_text.tag_config("you", foreground="#e8e8e8")
        self.log_text.tag_config("ai",  foreground=C_GOLD2)
        self.log_text.tag_config("sys", foreground=C_AMBER)
        self.log_text.tag_config("err", foreground=C_RED)

        INPUT_Y = LOG_Y + LH + 6
        self._build_input_bar(LW, INPUT_Y)
        self._build_mute_button()

        self.root.bind("<F4>", lambda e: self._toggle_mute())

        self._api_key_ready = self._api_keys_exist()
        if not self._api_key_ready:
            self._show_setup_ui()

        self._animate()
        self.root.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))

    # ── energy node helpers ─────────────────────────────────────────────────
    def _init_energy_nodes(self):
        """Golden glowing nodes on the sphere surface."""
        nodes = []
        for _ in range(120):
            lat = random.uniform(-80, 80)
            lon = random.uniform(0, 360)
            nodes.append({
                "lat": lat, "lon": lon,
                "lon_speed": random.uniform(0.2, 0.8),
                "brightness": random.uniform(0.3, 1.0),
                "size": random.randint(1, 3),
            })
        return nodes

    def _init_city_nodes(self):
        """Dense city-grid dots forming the sphere surface pattern."""
        nodes = []
        # Latitude rings
        for lat_step in range(-80, 81, 8):
            lon_count = max(4, int(36 * math.cos(math.radians(lat_step))))
            for lon_step in range(0, 360, 360 // lon_count):
                nodes.append({
                    "lat": lat_step + random.uniform(-3, 3),
                    "lon": lon_step + random.uniform(-3, 3),
                    "lon_speed": random.uniform(0.1, 0.4),
                    "type": random.choice(["dot", "dot", "dot", "cross", "square"]),
                    "brightness": random.uniform(0.2, 0.9),
                })
        return nodes

    # ── sphere projection ───────────────────────────────────────────────────
    def _sphere_project(self, lat_deg, lon_deg, r, cx, cy, lon_offset=0):
        """Project sphere lat/lon to 2D canvas x,y. Returns (x,y,depth)."""
        lat = math.radians(lat_deg)
        lon = math.radians(lon_deg + lon_offset)
        x3d = r * math.cos(lat) * math.sin(lon)
        y3d = -r * math.sin(lat)
        z3d = r * math.cos(lat) * math.cos(lon)
        # Perspective tilt (~20°)
        tilt = math.radians(20)
        y2d = y3d * math.cos(tilt) - z3d * math.sin(tilt)
        z2d = y3d * math.sin(tilt) + z3d * math.cos(tilt)
        return cx + x3d, cy + y2d, z2d / r   # depth: -1=back, +1=front

    # ── debris helpers ──────────────────────────────────────────────────────
    def _new_debris(self, angle_deg=None):
        R   = self.ORB_R
        ang = random.uniform(0, 360) if angle_deg is None else angle_deg
        r   = random.uniform(R * 0.9, R * 1.6)
        vr  = random.uniform(-0.3, 0.3)
        va  = random.uniform(0.2, 1.4) * random.choice([-1, 1])
        sz  = random.randint(1, 4)
        b   = random.uniform(0.3, 1.0)
        return {"ang": ang, "r": r, "vr": vr, "va": va, "sz": sz, "b": b}

    # ── mute button ─────────────────────────────────────────────────────────
    def _build_mute_button(self):
        BTN_W, BTN_H = 110, 32
        self._mute_canvas = tk.Canvas(
            self.root, width=BTN_W, height=BTN_H,
            bg=C_BG, highlightthickness=0, cursor="hand2"
        )
        self._mute_canvas.place(x=18, y=self.H - 70)
        self._mute_canvas.bind("<Button-1>", lambda e: self._toggle_mute())
        self._draw_mute_button()

    def _draw_mute_button(self):
        c = self._mute_canvas
        c.delete("all")
        if self.muted:
            border, fill, icon, label, fg = C_MUTED, "#1a0008", "🔇", " MUTED", C_MUTED
        else:
            border, fill, icon, label, fg = C_DIM, C_PANEL, "🎙", " LIVE", C_GREEN
        c.create_rectangle(0, 0, 110, 32, outline=border, fill=fill, width=1)
        c.create_text(55, 16, text=f"{icon}{label}", fill=fg, font=("Courier", 10, "bold"))

    def _toggle_mute(self):
        self.muted = not self.muted
        self._draw_mute_button()
        if self.muted:
            self.set_state("MUTED")
            self.write_log("SYS: Microphone muted.")
        else:
            self.set_state("LISTENING")
            self.write_log("SYS: Microphone active.")

    # ── input bar ───────────────────────────────────────────────────────────
    def _build_input_bar(self, lw: int, y: int):
        x0    = (self.W - lw) // 2
        BTN_W = 70
        INP_W = lw - BTN_W - 4

        self._input_var = tk.StringVar()
        self._input_entry = tk.Entry(
            self.root, textvariable=self._input_var,
            fg=C_TEXT, bg="#010a10",
            insertbackground=C_GOLD,
            borderwidth=0, font=("Courier", 10),
            highlightthickness=1,
            highlightbackground=C_DIM,
            highlightcolor=C_GOLD,
        )
        self._input_entry.place(x=x0, y=y, width=INP_W, height=28)
        self._input_entry.bind("<Return>", self._on_input_submit)
        self._input_entry.bind("<KP_Enter>", self._on_input_submit)

        self._send_btn = tk.Button(
            self.root, text="SEND ▸", command=self._on_input_submit,
            fg=C_GOLD, bg=C_PANEL,
            activeforeground=C_BG, activebackground=C_GOLD,
            font=("Courier", 9, "bold"), borderwidth=0, cursor="hand2",
            highlightthickness=1, highlightbackground=C_DIM,
        )
        self._send_btn.place(x=x0 + INP_W + 4, y=y, width=BTN_W, height=28)

    def _on_input_submit(self, event=None):
        text = self._input_var.get().strip()
        if not text:
            return
        self._input_var.set("")
        self.write_log(f"You: {text}")
        if self.on_text_command:
            threading.Thread(target=self.on_text_command, args=(text,), daemon=True).start()

    # ── state ───────────────────────────────────────────────────────────────
    def set_state(self, state: str):
        self._jarvis_state = state
        state_map = {
            "MUTED":      (False, "MUTED"),
            "SPEAKING":   (True,  "SPEAKING"),
            "THINKING":   (False, "THINKING"),
            "LISTENING":  (False, "LISTENING"),
            "PROCESSING": (False, "PROCESSING"),
        }
        self.speaking, self.status_text = state_map.get(state, (False, "ONLINE"))

    # ── face loading ─────────────────────────────────────────────────────────
    def _load_face(self, path):
        FW = self.ORB_R * 2
        try:
            img  = Image.open(path).convert("RGBA").resize((FW, FW), Image.LANCZOS)
            mask = Image.new("L", (FW, FW), 0)
            ImageDraw.Draw(mask).ellipse((2, 2, FW - 2, FW - 2), fill=255)
            img.putalpha(mask)
            self._face_pil = img
            self._has_face = True
        except Exception:
            self._has_face = False

    # ── colour helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _ac(r, g, b, a):
        f = max(0.0, min(1.0, a / 255.0))
        return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"

    @staticmethod
    def _gold(alpha):
        f = max(0.0, min(1.0, alpha / 255.0))
        return f"#{int(255*f):02x}{int(170*f):02x}{int(0*f):02x}"

    @staticmethod
    def _amber(alpha):
        f = max(0.0, min(1.0, alpha / 255.0))
        return f"#{int(255*f):02x}{int(100*f):02x}{int(0*f):02x}"

    @staticmethod
    def _energy_col(alpha, intensity=1.0):
        """Orange-gold energy color."""
        f = max(0.0, min(1.0, alpha / 255.0))
        r = int(255 * f)
        g = int((120 + 80 * intensity) * f)
        b = int(0)
        return f"#{r:02x}{g:02x}{b:02x}"

    # ── animation loop ────────────────────────────────────────────────────────
    def _animate(self):
        self.tick += 1
        t   = self.tick
        now = time.time()

        spk = self.speaking
        mut = self.muted

        if now - self.last_t > (0.08 if spk else 0.45):
            if spk:
                self.target_scale = random.uniform(1.04, 1.11)
                self.target_halo  = random.uniform(170, 220)
            elif mut:
                self.target_scale = random.uniform(0.998, 1.002)
                self.target_halo  = random.uniform(18, 30)
            else:
                self.target_scale = random.uniform(1.001, 1.006)
                self.target_halo  = random.uniform(60, 90)
            self.last_t = now

        sp = 0.30 if spk else 0.14
        self.scale  += (self.target_scale - self.scale) * sp
        self.halo_a += (self.target_halo  - self.halo_a) * sp

        # Spin orbit rings
        for i in range(8):
            speed_mult = 2.2 if spk else 1.0
            self.orbit_angles[i] = (self.orbit_angles[i] + self.orbit_speeds[i] * speed_mult) % 360

        # Rotate city nodes and energy nodes
        lon_speed_mult = 2.5 if spk else 1.0
        for n in self.city_nodes:
            n["lon"] = (n["lon"] + n["lon_speed"] * lon_speed_mult) % 360
        for n in self.energy_nodes:
            n["lon"] = (n["lon"] + n["lon_speed"] * lon_speed_mult * 0.6) % 360

        # Scan arcs
        scan_spd = 3.5 if spk else 1.6
        self.scan_angle  = (self.scan_angle  + scan_spd) % 360
        self.scan2_angle = (self.scan2_angle - scan_spd * 0.7) % 360
        self.scan3_angle = (self.scan3_angle + scan_spd * 1.3) % 360

        # Pulse rings
        pspd  = 5.0 if spk else 2.5
        limit = self.ORB_R * 1.8
        new_p = [r + pspd for r in self.pulse_r if r + pspd < limit]
        spawn_chance = 0.12 if spk else 0.03
        if len(new_p) < 5 and random.random() < spawn_chance:
            new_p.append(0.0)
        self.pulse_r = new_p

        # Spectrum bars (music visualizer)
        for i in range(64):
            if spk:
                # Lively random heights when speaking
                if random.random() < 0.35:
                    self.spectrum_targets[i] = random.uniform(0.08, 0.85)
            elif not mut:
                # Gentle breathing when listening
                phase = t * 0.04 + i * 0.3
                self.spectrum_targets[i] = 0.05 + 0.08 * abs(math.sin(phase))
            else:
                self.spectrum_targets[i] = 0.02

            # Smooth lerp toward target
            lerp = 0.4 if spk else 0.12
            self.spectrum_bars[i] += (self.spectrum_targets[i] - self.spectrum_bars[i]) * lerp

        # Debris
        for p in self.debris:
            p["ang"] = (p["ang"] + p["va"]) % 360
            p["r"]   = max(self.ORB_R * 0.85, min(self.ORB_R * 1.7,
                           p["r"] + p["vr"] * (2.0 if spk else 0.6)))
            if random.random() < 0.004:
                p["va"] *= -1
        if random.random() < (0.05 if spk else 0.01):
            self.debris.append(self._new_debris())
        if len(self.debris) > 100:
            self.debris.pop(0)

        if t % 35 == 0:
            self.status_blink = not self.status_blink

        self._draw()
        self.root.after(16, self._animate)

    # ── draw ─────────────────────────────────────────────────────────────────
    def _draw(self):
        c    = self.bg
        W, H = self.W, self.H
        t    = self.tick
        FCX  = self.FCX
        FCY  = self.FCY
        R    = self.ORB_R
        c.delete("all")

        # ── deep space background ─────────────────────────────────────────────
        # Subtle star field
        if not hasattr(self, '_stars'):
            self._stars = [(random.randint(0, W), random.randint(0, H),
                            random.choice(["#111111", "#151515", "#0d0d0d"])) for _ in range(200)]
        for sx, sy, sc in self._stars:
            c.create_rectangle(sx, sy, sx+1, sy+1, fill=sc, outline="")

        # ── large radial atmospheric glow ────────────────────────────────────
        glow_max = int(R * 2.4)
        for gr in range(glow_max, int(R * 0.8), -22):
            frac = 1.0 - (gr - R * 0.8) / (R * 1.6)
            frac = max(0, frac)
            if self.muted:
                ga = max(0, min(255, int(self.halo_a * 0.04 * frac)))
                c.create_oval(FCX-gr, FCY-gr, FCX+gr, FCY+gr,
                              outline=self._ac(150, 20, 40, ga), width=3)
            else:
                ga = max(0, min(255, int(self.halo_a * 0.07 * frac)))
                c.create_oval(FCX-gr, FCY-gr, FCX+gr, FCY+gr,
                              outline=self._gold(ga), width=3)

        # ── pulse rings ───────────────────────────────────────────────────────
        for pr in self.pulse_r:
            frac = 1.0 - pr / (R * 1.8)
            pa   = max(0, int(200 * frac))
            ri   = int(pr + R * 0.95)
            if self.muted:
                col = self._ac(200, 30, 60, pa // 4)
            else:
                col = self._amber(pa)
            c.create_oval(FCX-ri, FCY-ri, FCX+ri, FCY+ri, outline=col, width=2)

        # ── music spectrum ring around orb ───────────────────────────────────
        N_BARS    = 64
        SPEC_INNER = R * 1.08
        SPEC_OUTER = R * 1.45
        for i in range(N_BARS):
            angle_deg = (i / N_BARS) * 360 - 90
            angle_rad = math.radians(angle_deg)
            bar_h     = self.spectrum_bars[i]
            inner_r   = SPEC_INNER
            outer_r   = SPEC_INNER + (SPEC_OUTER - SPEC_INNER) * bar_h

            x1 = FCX + inner_r * math.cos(angle_rad)
            y1 = FCY + inner_r * math.sin(angle_rad)
            x2 = FCX + outer_r * math.cos(angle_rad)
            y2 = FCY + outer_r * math.sin(angle_rad)

            intensity = bar_h
            if self.muted:
                alpha = int(40 + 20 * bar_h * 255)
                col = self._ac(200, 30, 60, min(255, alpha))
                w = 2
            elif self.speaking:
                alpha = int((0.4 + 0.6 * intensity) * 255)
                if intensity > 0.6:
                    col = self._ac(255, 200, 50, min(255, alpha))
                elif intensity > 0.35:
                    col = self._ac(255, 130, 0, min(255, alpha))
                else:
                    col = self._ac(200, 80, 0, min(255, alpha))
                w = 3 if intensity > 0.5 else 2
            else:
                alpha = int((0.2 + 0.4 * intensity) * 255)
                col = self._ac(180, 90, 0, min(255, alpha))
                w = 2

            c.create_line(x1, y1, x2, y2, fill=col, width=w, capstyle="round")

        # ── city nodes on sphere surface (back layer first) ──────────────────
        lon_offset = t * 0.15 if not self.speaking else t * 0.35
        # Sort by depth (back to front)
        node_data = []
        for n in self.city_nodes:
            x, y, depth = self._sphere_project(n["lat"], n["lon"], R * 0.96,
                                               FCX, FCY, lon_offset)
            node_data.append((depth, x, y, n))

        node_data.sort(key=lambda d: d[0])

        for depth, nx, ny, n in node_data:
            # Depth-based alpha (back = dim, front = bright)
            depth_frac = (depth + 1) / 2.0  # 0=back, 1=front
            base_alpha = int(self.halo_a * n["brightness"] * (0.15 + 0.85 * depth_frac))
            base_alpha = max(0, min(255, base_alpha))

            if self.muted:
                col = self._ac(180, 40, 60, base_alpha)
            else:
                # Orange-gold city glow, brighter on front face
                r_c = 255
                g_c = int(100 + 80 * depth_frac)
                b_c = 0
                col = self._ac(r_c, g_c, b_c, base_alpha)

            typ = n["type"]
            if typ == "dot":
                sz = 1
                c.create_oval(nx-sz, ny-sz, nx+sz, ny+sz, fill=col, outline="")
            elif typ == "cross":
                c.create_line(nx-2, ny, nx+2, ny, fill=col, width=1)
                c.create_line(nx, ny-2, nx, ny+2, fill=col, width=1)
            elif typ == "square":
                c.create_rectangle(nx-1, ny-1, nx+1, ny+1, fill=col, outline="")

        # ── energy nodes (brighter glowing hot spots) ────────────────────────
        for n in self.energy_nodes:
            x, y, depth = self._sphere_project(n["lat"], n["lon"], R * 0.96,
                                               FCX, FCY, lon_offset)
            if depth < -0.1:
                continue  # skip back hemisphere
            depth_frac = (depth + 1) / 2.0
            alpha = int(self.halo_a * n["brightness"] * 1.8 * depth_frac)
            alpha = max(0, min(255, alpha))
            sz = n["size"]
            if self.muted:
                col = self._ac(220, 40, 80, alpha)
            else:
                col = self._ac(255, 180 + int(70 * depth_frac), 20, alpha)
            c.create_oval(x-sz, y-sz, x+sz, y+sz, fill=col, outline="")

        # ── orbit rings (tilted great circles) ───────────────────────────────
        ring_specs = [
            (1.00, 3, 100, 45),
            (0.95, 2, 80,  35),
            (0.92, 2, 60,  30),
            (0.98, 2, 90,  50),
            (0.88, 1, 70,  40),
            (0.93, 1, 50,  25),
            (1.02, 3, 110, 60),
            (0.97, 2, 75,  38),
        ]
        for idx, (r_frac, w_ring, arc_l, gap) in enumerate(ring_specs):
            ring_r = int(R * r_frac)
            base_a = self.orbit_angles[idx]
            tilt   = self.orbit_tilts[idx]

            a_val  = max(0, min(255, int(self.halo_a * (1.0 - idx * 0.06))))
            tilt_rad  = math.radians(tilt)
            y_squeeze = max(0.1, abs(math.cos(tilt_rad)))
            ry = max(int(ring_r * y_squeeze), 6)
            rx = ring_r

            if self.muted:
                col = self._ac(180, 30, 60, a_val)
            elif idx % 3 == 0:
                col = self._gold(a_val)
            elif idx % 3 == 1:
                col = self._amber(a_val)
            else:
                col = self._ac(255, 200, 60, a_val)

            step = arc_l + gap
            count = 360 // step + 1
            for s in range(count):
                start = (base_a + s * step) % 360
                c.create_arc(FCX - rx, FCY - ry, FCX + rx, FCY + ry,
                             start=start, extent=arc_l,
                             outline=col, width=w_ring, style="arc")

        # ── scan energy sweepers ─────────────────────────────────────────────
        sr = int(R * 1.01)
        scan_a = min(255, int(self.halo_a * 1.8))
        arc_ext = 100 if self.speaking else 60

        scan_col = (self._ac(180, 30, 60, scan_a) if self.muted
                    else self._ac(255, 160, 0, scan_a))
        c.create_arc(FCX-sr, FCY-sr, FCX+sr, FCY+sr,
                     start=self.scan_angle, extent=arc_ext,
                     outline=scan_col, width=4, style="arc")

        # Second scanner
        c.create_arc(FCX-sr, FCY-sr, FCX+sr, FCY+sr,
                     start=self.scan2_angle, extent=arc_ext // 2,
                     outline=self._ac(255, 100, 0, scan_a // 2),
                     width=2, style="arc")

        # Third thin scanner (inner orbit)
        ir = int(R * 0.82)
        c.create_arc(FCX-ir, FCY-ir, FCX+ir, FCY+ir,
                     start=self.scan3_angle, extent=40,
                     outline=self._ac(255, 200, 80, scan_a // 3),
                     width=2, style="arc")

        # ── tick marks on outer boundary ─────────────────────────────────────
        t_out = int(R * 1.04)
        t_in  = int(R * 0.995)
        a_mk  = self._gold(100)
        for deg in range(0, 360, 5):
            rad = math.radians(deg)
            inn = t_in if deg % 30 == 0 else (t_in + 3 if deg % 10 == 0 else t_in + 6)
            c.create_line(FCX + t_out * math.cos(rad), FCY - t_out * math.sin(rad),
                          FCX + inn  * math.cos(rad), FCY - inn  * math.sin(rad),
                          fill=a_mk, width=1)

        # ── debris particles around orb ───────────────────────────────────────
        for p in self.debris:
            ang_r = math.radians(p["ang"])
            px    = FCX + p["r"] * math.cos(ang_r)
            py    = FCY + p["r"] * math.sin(ang_r)
            sz    = p["sz"]
            ba    = max(0, min(255, int(self.halo_a * p["b"] * 1.2)))
            if self.muted:
                col = self._ac(180, 40, 60, ba)
            else:
                if p["b"] > 0.75:
                    col = self._ac(255, 190, 30, ba)
                elif p["b"] > 0.5:
                    col = self._ac(255, 120, 0, ba)
                else:
                    col = self._ac(180, 70, 0, ba)
            c.create_rectangle(px, py, px+sz, py+sz//2+1, fill=col, outline="")

        # ── crosshair targeting lines ─────────────────────────────────────────
        ch_r = int(R * 1.06)
        gap  = int(R * 0.22)
        ch_a = self._gold(int(self.halo_a * 0.5))
        for x1, y1, x2, y2 in [
                (FCX - ch_r, FCY, FCX - gap, FCY), (FCX + gap, FCY, FCX + ch_r, FCY),
                (FCX, FCY - ch_r, FCX, FCY - gap), (FCX, FCY + gap, FCX, FCY + ch_r)]:
            c.create_line(x1, y1, x2, y2, fill=ch_a, width=1)

        # Corner tick brackets
        for deg in [45, 135, 225, 315]:
            rad = math.radians(deg)
            bx  = FCX + ch_r * math.cos(rad)
            by  = FCY - ch_r * math.sin(rad)
            arc_start = deg - 15
            c.create_arc(FCX - ch_r, FCY - ch_r, FCX + ch_r, FCY + ch_r,
                         start=arc_start, extent=30,
                         outline=ch_a, width=2, style="arc")

        # ── central orb glow / face ───────────────────────────────────────────
        if self._has_face:
            fw = int(R * 2 * self.scale)
            if (self._face_scale_cache is None or
                    abs(self._face_scale_cache[0] - self.scale) > 0.004):
                scaled = self._face_pil.resize((fw, fw), Image.BILINEAR)
                tk_img = ImageTk.PhotoImage(scaled)
                self._face_scale_cache = (self.scale, tk_img)
            c.create_image(FCX, FCY, image=self._face_scale_cache[1])
        else:
            # Layered glowing energy orb
            orb_r = int(R * 0.56 * self.scale)
            # Outer soft glow layers
            for i in range(12, 0, -1):
                r2   = int(orb_r * i / 12)
                frac = i / 12.0
                if self.muted:
                    ga  = max(0, min(255, int(self.halo_a * 0.7 * frac)))
                    col = self._ac(160, 20, 50, ga)
                else:
                    ga  = max(0, min(255, int(self.halo_a * 1.1 * frac)))
                    # Core: white-gold → outer: deep amber
                    r_c = 255
                    g_c = int(220 * frac + 60 * (1 - frac))
                    b_c = int(80 * frac)
                    col = self._ac(r_c, g_c, b_c, ga)
                c.create_oval(FCX-r2, FCY-r2, FCX+r2, FCY+r2, fill=col, outline="")

            # Inner bright core
            core_r = max(4, int(orb_r * 0.25))
            c.create_oval(FCX-core_r, FCY-core_r, FCX+core_r, FCY+core_r,
                          fill=self._ac(255, 240, 200, min(255, int(self.halo_a * 2.2))),
                          outline="")

            # System name
            name_a = min(255, int(self.halo_a * 2.8))
            c.create_text(FCX, FCY,
                          text=SYSTEM_NAME,
                          fill=self._ac(255, 240, 160, name_a),
                          font=("Courier", 13, "bold"))

        # ── HUD data overlays ─────────────────────────────────────────────────
        # Left side data readout
        lx = FCX - int(R * 1.45)
        data_lines = [
            ("LAT", f"{28.6 + math.sin(t*0.02)*0.3:.4f}°"),
            ("LON", f"{77.2 + math.cos(t*0.015)*0.3:.4f}°"),
            ("ALT", f"{0.847 + math.sin(t*0.03)*0.01:.3f} km"),
            ("PWR", f"{87 + int(math.sin(t*0.05)*8)}%"),
        ]
        ly = FCY - 40
        for label, val in data_lines:
            c.create_text(lx, ly, text=label, fill=C_DIM, font=("Courier", 8), anchor="e")
            c.create_text(lx + 8, ly, text=val, fill=C_GOLD2, font=("Courier", 8), anchor="w")
            ly += 18

        # Right side data readout
        rx = FCX + int(R * 1.45)
        data_lines2 = [
            ("SYS", "NOMINAL"),
            ("NET", "SECURE"),
            ("CPU", f"{42 + int(math.sin(t*0.07)*20)}%"),
            ("MEM", f"{61 + int(math.cos(t*0.04)*10)}%"),
        ]
        ly2 = FCY - 40
        for label, val in data_lines2:
            c.create_text(rx - 8, ly2, text=val, fill=C_GOLD2, font=("Courier", 8), anchor="e")
            c.create_text(rx, ly2, text=label, fill=C_DIM, font=("Courier", 8), anchor="w")
            ly2 += 18

        # ── status label with energy indicator ───────────────────────────────
        sy = FCY + int(R * 1.25)
        if self.muted:
            stat, sc = "⊘  MUTED", C_MUTED
        elif self.speaking:
            stat, sc = "●  SPEAKING", C_GOLD
        elif self._jarvis_state == "THINKING":
            sym  = "◈" if self.status_blink else "◇"
            stat, sc = f"{sym}  THINKING", C_GLOW
        elif self._jarvis_state == "PROCESSING":
            sym  = "▷" if self.status_blink else "▶"
            stat, sc = f"{sym}  PROCESSING", C_AMBER
        elif self._jarvis_state == "LISTENING":
            sym  = "●" if self.status_blink else "○"
            stat, sc = f"{sym}  LISTENING", C_GREEN
        else:
            sym  = "●" if self.status_blink else "○"
            stat, sc = f"{sym}  {self.status_text}", C_GOLD2
        c.create_text(W // 2, sy, text=stat, fill=sc, font=("Courier", 11, "bold"))

        # ── header bar ───────────────────────────────────────────────────────
        HDR = 52
        c.create_rectangle(0, 0, W, HDR, fill="#010608", outline="")
        c.create_line(0, HDR, W, HDR, fill=C_DIM, width=1)
        c.create_line(W // 4, HDR, 3 * W // 4, HDR, fill=C_GOLD3, width=2)

        c.create_text(W // 2, 16, text=SYSTEM_NAME,
                      fill=C_GOLD, font=("Courier", 16, "bold"))
        c.create_text(W // 2, 36, text="Just A Rather Very Intelligent System",
                      fill=C_DIM, font=("Courier", 8))
        c.create_text(16, 26, text=MODEL_BADGE,
                      fill=C_DIM, font=("Courier", 8), anchor="w")
        c.create_text(W - 16, 26, text=time.strftime("%H:%M:%S"),
                      fill=C_GOLD2, font=("Courier", 13, "bold"), anchor="e")

        # ── footer bar ───────────────────────────────────────────────────────
        c.create_rectangle(0, H - 26, W, H, fill="#010608", outline="")
        c.create_line(0, H - 26, W, H - 26, fill=C_DIM, width=1)
        c.create_text(W - 16, H - 13, fill=C_DIM, font=("Courier", 7),
                      text="[F4] MUTE", anchor="e")
        c.create_text(W // 2, H - 13, fill=C_DIM, font=("Courier", 7),
                      text="FatihMakes Industries  ·  CLASSIFIED  ·  MARK XXXVII")

    # ── log writing ──────────────────────────────────────────────────────────
    def write_log(self, text: str):
        self.typing_queue.append(text)
        tl = text.lower()
        if tl.startswith("you:"):
            self.set_state("PROCESSING")
        elif tl.startswith("jarvis:") or tl.startswith("ai:"):
            self.set_state("SPEAKING")
        if not self.is_typing:
            self._start_typing()

    def _start_typing(self):
        if not self.typing_queue:
            self.is_typing = False
            if not self.speaking and not self.muted:
                self.set_state("LISTENING")
            return
        self.is_typing = True
        text = self.typing_queue.popleft()
        tl   = text.lower()
        tag  = ("you"  if tl.startswith("you:")
                else "ai"  if (tl.startswith("jarvis:") or tl.startswith("ai:"))
                else "err" if ("error" in tl or "failed" in tl)
                else "sys")
        self.log_text.configure(state="normal")
        self._type_char(text, 0, tag)

    def _type_char(self, text, i, tag):
        if i < len(text):
            self.log_text.insert(tk.END, text[i], tag)
            self.log_text.see(tk.END)
            self.root.after(8, self._type_char, text, i + 1, tag)
        else:
            self.log_text.insert(tk.END, "\n")
            self.log_text.configure(state="disabled")
            self.root.after(25, self._start_typing)

    def start_speaking(self):
        self.set_state("SPEAKING")

    def stop_speaking(self):
        if not self.muted:
            self.set_state("LISTENING")

    # ── API key helpers ───────────────────────────────────────────────────────
    def _api_keys_exist(self) -> bool:
        if not API_FILE.exists():
            return False
        try:
            data = json.loads(API_FILE.read_text(encoding="utf-8"))
            return bool(data.get("gemini_api_key")) and bool(data.get("os_system"))
        except Exception:
            return False

    def wait_for_api_key(self):
        while not self._api_key_ready:
            time.sleep(0.1)

    @staticmethod
    def _detect_os() -> str:
        s = platform.system().lower()
        if s == "darwin":   return "mac"
        if s == "windows":  return "windows"
        return "linux"

    def _show_setup_ui(self):
        detected = self._detect_os()
        self._selected_os = tk.StringVar(value=detected)

        self.setup_frame = tk.Frame(
            self.root, bg="#010a10",
            highlightbackground=C_GOLD, highlightthickness=1
        )
        self.setup_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self.setup_frame, text="◈  INITIALISATION REQUIRED",
                 fg=C_GOLD, bg="#010a10", font=("Courier", 13, "bold")).pack(pady=(18, 2))
        tk.Label(self.setup_frame, text="Configure J.A.R.V.I.S. before first boot.",
                 fg=C_DIM, bg="#010a10", font=("Courier", 9)).pack(pady=(0, 14))
        tk.Label(self.setup_frame, text="GEMINI API KEY",
                 fg=C_DIM, bg="#010a10", font=("Courier", 9)).pack(pady=(0, 2))

        self.gemini_entry = tk.Entry(
            self.setup_frame, width=52, fg=C_TEXT, bg="#010a10",
            insertbackground=C_GOLD, borderwidth=0, font=("Courier", 10), show="*"
        )
        self.gemini_entry.pack(pady=(0, 18))

        tk.Frame(self.setup_frame, bg=C_DIM, height=1).pack(fill="x", padx=24, pady=(0, 12))
        tk.Label(self.setup_frame, text="SELECT OPERATING SYSTEM",
                 fg=C_DIM, bg="#010a10", font=("Courier", 9)).pack(pady=(0, 4))

        detect_label = {"windows": "Windows", "mac": "macOS", "linux": "Linux"}.get(
            detected, detected.capitalize())
        tk.Label(self.setup_frame, text=f"AUTO-DETECTED: {detect_label}",
                 fg=C_AMBER, bg="#010a10", font=("Courier", 8)).pack(pady=(0, 8))

        os_btn_frame = tk.Frame(self.setup_frame, bg="#010a10")
        os_btn_frame.pack(pady=(0, 18))
        os_options = [("windows", "⊞  WINDOWS"), ("mac", "  macOS"), ("linux", "🐧  LINUX")]

        self._os_buttons = {}
        for os_key, os_label in os_options:
            btn = tk.Button(os_btn_frame, text=os_label, width=13,
                            font=("Courier", 10, "bold"), borderwidth=0,
                            cursor="hand2", pady=7,
                            command=lambda k=os_key: self._select_os(k))
            btn.pack(side="left", padx=6)
            self._os_buttons[os_key] = btn

        self._select_os(detected)
        tk.Frame(self.setup_frame, bg=C_DIM, height=1).pack(fill="x", padx=24, pady=(0, 14))
        tk.Button(self.setup_frame, text="▸  INITIALISE SYSTEMS",
                  command=self._save_api_keys, bg=C_BG, fg=C_GOLD,
                  activebackground="#0a1a10", font=("Courier", 10),
                  borderwidth=0, pady=8).pack(pady=(0, 18))

    def _select_os(self, os_key: str):
        self._selected_os.set(os_key)
        styles = {"windows": (C_GOLD, "#1a0e00"), "mac": (C_AMBER, "#1a0800"), "linux": (C_GREEN, "#001a0d")}
        for key, btn in self._os_buttons.items():
            if key == os_key:
                fg, bg = styles[key]
                btn.configure(fg=bg, bg=fg, activeforeground=bg, activebackground=fg, relief="flat")
            else:
                btn.configure(fg=C_DIM, bg="#010a10", activeforeground=C_TEXT,
                              activebackground="#1a0e00", relief="flat")

    def _save_api_keys(self):
        gemini = self.gemini_entry.get().strip()
        if not gemini:
            self.gemini_entry.configure(highlightthickness=1,
                                        highlightbackground=C_RED, highlightcolor=C_RED)
            return
        os_system = self._selected_os.get()
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(API_FILE, "w", encoding="utf-8") as f:
            json.dump({"gemini_api_key": gemini, "os_system": os_system}, f, indent=4)
        self.setup_frame.destroy()
        self._api_key_ready = True
        self.set_state("LISTENING")
        self.write_log(f"SYS: Systems initialised. OS → {os_system.upper()}. JARVIS online.")