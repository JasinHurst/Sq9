import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import csv

# -------------------- THEME CONSTANTS --------------------
DARK_BG = "#1e1e1e"
CELL_BG = "#2d2d2d"
CENTER_SHADE = "#555555"
TEXT_LIGHT = "#ffffff"
TEXT_DARK = "#000000"
FONT_MAIN = ("Arial", 9, "bold")
FONT_CELL = ("Arial", 11, "bold")

# -------------------- PLANET SETTINGS --------------------
PLANET_COLORS = {
    "SUN": "#FFD700", "MOON": "#FFFFFF", "MER": "#9370DB",
    "VEN": "#87CEFA", "MARS": "#FF0000", "JUP": "#D8BFD8",
    "SAT": "#000000", "URA": "#00FF7F", "NEP": "#00008B",
    "PLU": "#8B4513", "NN": "#FF4500"
}
PLANET_FULL = {
    "SUN": "Sun", "MOON": "Moon", "MER": "Mercury", "VEN": "Venus",
    "MARS": "Mars", "JUP": "Jupiter", "SAT": "Saturn",
    "URA": "Uranus", "NEP": "Neptune", "PLU": "Pluto", "NN": "North Node"
}
WHITE_TEXT = {"MER", "MARS", "NEP", "PLU", "NN", "SAT"}

# -------------------- STEP SIZE OPTIONS --------------------
STEP_SIZES = {
    "Day": 1,
    "Week": 7,
    "Month": 30,
    "Year": 365
}

# -------------------- SQ9 GRID BUILDER --------------------
def build_sq9(size=19):
    grid = [[0]*size for _ in range(size)]
    cx = cy = size // 2
    x, y = cx, cy
    n = 1
    grid[y][x] = n
    step = 1
    while n < size*size:
        for _ in range(step):  # Right
            if n >= size*size: break
            x += 1; n += 1; grid[y][x] = n
        for _ in range(step):  # Up
            if n >= size*size: break
            y -= 1; n += 1; grid[y][x] = n
        step += 1
        for _ in range(step):  # Left
            if n >= size*size: break
            x -= 1; n += 1; grid[y][x] = n
        for _ in range(step):  # Down
            if n >= size*size: break
            y += 1; n += 1; grid[y][x] = n
        step += 1
    return grid

def degree_to_cell(deg):
    d = int(deg % 360)
    return d if d != 0 else 360

# -------------------- MAIN APPLICATION --------------------
class SQ9App:
    def __init__(self, root, ephemeris):
        self.root = root
        self.root.title("Square of 9 – Planet Calculator")
        self.root.configure(bg=DARK_BG)

        # Ephemeris data
        self.ephemeris = ephemeris
        self.all_dates = sorted(ephemeris.keys())
        self.min_date, self.max_date = self.all_dates[0], self.all_dates[-1]

        # Default date
        today = datetime.today().date()
        if today < self.min_date: today = self.min_date
        if today > self.max_date: today = self.max_date
        self.current_date = today

        # Track planet visibility (default NN = OFF)
        self.planet_visibility = {abbr: tk.IntVar(value=1) for abbr in PLANET_COLORS.keys()}
        self.planet_visibility["NN"].set(0)

        # Track All Off toggle state
        self.all_off_state = False

        # Button style
        style = ttk.Style()
        style.configure("TButton", font=FONT_MAIN, padding=3, relief="flat",
                        background="#444444", foreground="black")
        style.map("TButton", background=[("active", "#666666")],
                  foreground=[("active", "black")])

        # -------------------- SIDEBAR: LEGEND --------------------
        legend_frame = tk.Frame(root, bg=DARK_BG)
        legend_frame.pack(side="left", fill="y", padx=10, pady=10)
        tk.Label(legend_frame, text="Legend", font=("Arial", 11, "bold"),
                 fg=TEXT_LIGHT, bg=DARK_BG).pack(pady=(0,4))

        for abbr, color in PLANET_COLORS.items():
            fg = TEXT_LIGHT if abbr in WHITE_TEXT else TEXT_DARK
            item = tk.Frame(legend_frame, bg=DARK_BG)
            item.pack(anchor="w", pady=1)

            tk.Label(item, width=2, height=1, bg=color).pack(side="left", padx=4)
            tk.Label(item, text=f"{abbr} – {PLANET_FULL[abbr]}",
                     fg=TEXT_LIGHT, bg=DARK_BG, font=FONT_MAIN).pack(side="left")

            cb = tk.Checkbutton(item, variable=self.planet_visibility[abbr],
                                onvalue=1, offvalue=0, command=self.repaint,
                                fg=TEXT_LIGHT, bg=DARK_BG, selectcolor=DARK_BG,
                                activebackground=DARK_BG, activeforeground=TEXT_LIGHT)
            cb.pack(side="left", padx=5)

        # -------------------- PLANET GROUP BUTTONS --------------------
        group_frame = tk.Frame(legend_frame, bg=DARK_BG)
        group_frame.pack(anchor="w", pady=15)

        self.all_off_btn = ttk.Button(group_frame, text="All Off", command=self.toggle_all_off)
        self.all_off_btn.pack(anchor="w", pady=2, fill="x")

        ttk.Button(group_frame, text="Inner Planets", command=self.inner_planets).pack(anchor="w", pady=2, fill="x")
        ttk.Button(group_frame, text="Outer Planets", command=self.outer_planets).pack(anchor="w", pady=2, fill="x")

        # -------------------- SIDEBAR: MOTION --------------------
        self.motion_frame = tk.Frame(legend_frame, bg=DARK_BG)
        self.motion_frame.pack(side="top", pady=12, anchor="w")
        tk.Label(self.motion_frame, text="Planet Motion", font=("Arial", 11, "bold"),
                 fg=TEXT_LIGHT, bg=DARK_BG).pack(anchor="w", pady=(0,4))

        self.motion_labels = {}
        for abbr in PLANET_COLORS.keys():
            lbl = tk.Label(self.motion_frame, text=f"{abbr} – ?", fg=TEXT_LIGHT,
                           bg=DARK_BG, anchor="w", font=FONT_MAIN)
            lbl.pack(anchor="w", pady=1)
            self.motion_labels[abbr] = lbl

        # -------------------- MOTION LEGEND --------------------
        motion_legend = tk.Frame(legend_frame, bg=DARK_BG)
        motion_legend.pack(side="bottom", pady=15, anchor="w")

        tk.Label(motion_legend, text="Legend:", fg=TEXT_LIGHT, bg=DARK_BG,
                 font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Label(motion_legend, text="D = Direct", fg=TEXT_LIGHT, bg=DARK_BG,
                 font=FONT_MAIN).pack(anchor="w")
        tk.Label(motion_legend, text="R = Retrograde", fg="white", bg="red",
                 font=FONT_MAIN, padx=2, pady=1).pack(anchor="w", pady=1)
        tk.Label(motion_legend, text="S = Stationary", fg="black", bg="yellow",
                 font=FONT_MAIN, padx=2, pady=1).pack(anchor="w", pady=1)

        # -------------------- MAIN FRAME --------------------
        self.main_frame = tk.Frame(root, bg=DARK_BG)
        self.main_frame.pack(side="left", expand=True, fill="both")

        # Controls row
        self.calc_frame = tk.Frame(self.main_frame, bg=DARK_BG)
        self.calc_frame.pack(side="top", fill="x", pady=5)

        # Date entry + Today button
        date_frame = tk.Frame(self.calc_frame, bg=DARK_BG)
        date_frame.pack(side="top", pady=(0,3))
        tk.Label(date_frame, text="Date (MM/DD/YYYY):", bg=DARK_BG,
                 fg=TEXT_LIGHT, font=FONT_MAIN).pack(side="left", padx=4)
        self.date_entry = tk.Entry(date_frame, width=12, font=FONT_MAIN, justify="center")
        self.date_entry.insert(0, self.current_date.strftime("%m/%d/%Y"))
        self.date_entry.bind("<Return>", lambda e: self.on_calculate())
        self.date_entry.pack(side="left", padx=4)

        ttk.Button(date_frame, text="Today", command=self.jump_today, width=8).pack(side="left", padx=4)

        # Controls row 2
        control_row = tk.Frame(self.calc_frame, bg=DARK_BG)
        control_row.pack(side="top", pady=3)
        btn_width = 10
        ttk.Button(control_row, text="⟵ Back", command=lambda: self.step(-1), width=btn_width).pack(side="left", padx=3)
        ttk.Button(control_row, text="Forward ⟶", command=lambda: self.step(+1), width=btn_width).pack(side="left", padx=3)

        tk.Label(control_row, text="Select:", bg=DARK_BG, fg=TEXT_LIGHT,
                 font=FONT_MAIN).pack(side="left", padx=4)
        self.step_var = tk.StringVar(value="Day")
        option_menu = ttk.OptionMenu(control_row, self.step_var, "Day", "Day", "Week", "Month", "Year")
        option_menu.config(width=btn_width)
        option_menu.pack(side="left", padx=3)

        tk.Label(control_row, text="Custom:", bg=DARK_BG,
                 fg=TEXT_LIGHT, font=FONT_MAIN).pack(side="left", padx=4)
        self.custom_entry = tk.Entry(control_row, width=btn_width, font=FONT_MAIN, justify="center")
        self.custom_entry.insert(0, "0")
        self.custom_entry.pack(side="left", padx=3)

        ttk.Button(control_row, text="Increment", command=self.increment_custom, width=btn_width).pack(side="left", padx=3)
        ttk.Button(control_row, text="Reset", command=self.reset, width=btn_width).pack(side="left", padx=3)

        # -------------------- SQ9 GRID --------------------
        self.grid_frame = tk.Frame(self.main_frame, bg=DARK_BG)
        self.grid_frame.pack(expand=True, pady=(0,5))
        self.size = 19
        self.grid = build_sq9(self.size)
        self.center = self.size // 2
        self.labels = {}
        for i in range(self.size):
            for j in range(self.size):
                num = self.grid[i][j]
                bg, fg = self.base_shading(i, j)
                lbl = tk.Label(self.grid_frame, text=str(num), width=8, height=3,
                               borderwidth=1, relief="flat", bg=bg, fg=fg, font=("Arial", 9, "bold"))
                lbl.grid(row=i, column=j, padx=1, pady=1)
                self.labels[num] = lbl

        self.paint(self.current_date)

    # -------------------- HELPER METHODS --------------------
    def toggle_all_off(self):
        if not self.all_off_state:
            for abbr in self.planet_visibility:
                self.planet_visibility[abbr].set(0)
            self.all_off_btn.config(text="All On")
            self.all_off_state = True
        else:
            for abbr in self.planet_visibility:
                self.planet_visibility[abbr].set(1)
            self.all_off_btn.config(text="All Off")
            self.all_off_state = False
        self.repaint()

    def outer_planets(self):
        outer = {"PLU", "NEP", "URA", "JUP", "SAT"}
        for abbr in self.planet_visibility:
            self.planet_visibility[abbr].set(1 if abbr in outer else 0)
        self.repaint()

    def inner_planets(self):
        inner = {"SUN", "MOON", "MER", "VEN", "MARS"}
        for abbr in self.planet_visibility:
            self.planet_visibility[abbr].set(1 if abbr in inner else 0)
        self.repaint()

    def base_shading(self, i, j):
        if i == self.center or j == self.center or i == j or (i + j == self.size-1):
            return CENTER_SHADE, TEXT_LIGHT
        return CELL_BG, TEXT_LIGHT

    def on_calculate(self):
        try:
            d = datetime.strptime(self.date_entry.get(), "%m/%d/%Y").date()
        except:
            return
        if d < self.min_date or d > self.max_date: return
        self.current_date = d
        self.paint(d)

    def jump_today(self):
        d = datetime.today().date()
        if d < self.min_date: d = self.min_date
        if d > self.max_date: d = self.max_date
        self.current_date = d
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, d.strftime("%m/%d/%Y"))
        self.paint(d)

    def increment_custom(self):
        try:
            days = int(self.custom_entry.get())
        except:
            return
        if days <= 0:
            return
        new_date = self.current_date + timedelta(days=days)
        if new_date > self.max_date: new_date = self.max_date
        self.current_date = new_date
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, new_date.strftime("%m/%d/%Y"))
        self.paint(new_date)

    def reset(self):
        self.custom_entry.delete(0, tk.END)
        self.custom_entry.insert(0, "0")

    def step(self, direction):
        step_name = self.step_var.get()
        days = STEP_SIZES.get(step_name, 1)
        try:
            custom = int(self.custom_entry.get())
            if custom > 0: days = custom
        except: pass
        new_date = self.current_date + timedelta(days=days*direction)
        if new_date < self.min_date: new_date = self.min_date
        if new_date > self.max_date: new_date = self.max_date
        self.current_date = new_date
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, new_date.strftime("%m/%d/%Y"))
        self.paint(new_date)

    def repaint(self):
        self.paint(self.current_date)

    def paint(self, d):
        for i in range(self.size):
            for j in range(self.size):
                num = self.grid[i][j]
                bg, fg = self.base_shading(i, j)
                self.labels[num].config(text=str(num), bg=bg, fg=fg)

        row = self.ephemeris.get(d)
        if not row: return
        prev_row = self.ephemeris.get(d - timedelta(days=1))

        for abbr, deg in row.items():
            if self.planet_visibility[abbr].get() == 0:
                self.motion_labels[abbr].config(text=f"{abbr} – OFF", bg=DARK_BG, fg=TEXT_LIGHT)
                continue

            cell = degree_to_cell(deg)
            motion = "?"
            if prev_row and abbr in prev_row:
                delta = deg - prev_row[abbr]
                if delta > 180: delta -= 360
                if delta < -180: delta += 360
                if abs(delta) < 0.05:
                    motion = "S"
                elif delta > 0:
                    motion = "D"
                else:
                    motion = "R"

            # SQ9 grid: only show Cell + Planet (no degrees, no motion)
            if cell in self.labels:
                self.labels[cell].config(
                    text=f"{cell}\n{abbr}",
                    bg=PLANET_COLORS[abbr],
                    fg=TEXT_LIGHT if abbr in WHITE_TEXT else TEXT_DARK
                )

            # Sidebar still shows D/S/R
            if motion == "R":
                self.motion_labels[abbr].config(text=f"{abbr} – R", bg="red", fg="white")
            elif motion == "S":
                self.motion_labels[abbr].config(text=f"{abbr} – S", bg="yellow", fg="black")
            else:
                self.motion_labels[abbr].config(text=f"{abbr} – D", bg=DARK_BG, fg=TEXT_LIGHT)

# -------------------- CSV LOADER --------------------
def load_ephemeris(csv_file):
    data = {}
    with open(csv_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                d = datetime.strptime(row["Date"], "%Y-%m-%d").date()
            except:
                continue
            entry = {
                "SUN": float(row["Sun"]),
                "MOON": float(row["Moon"]),
                "MER": float(row["Mercury"]),
                "VEN": float(row["Venus"]),
                "MARS": float(row["Mars"]),
                "JUP": float(row["Jupiter"]),
                "SAT": float(row["Saturn"]),
                "URA": float(row["Uranus"]),
                "NEP": float(row["Neptune"]),
                "PLU": float(row["Pluto"]),
                "NN": float(row["True Node"])
            }
            data[d] = entry
    return data

# -------------------- MAIN ENTRY --------------------
if __name__ == "__main__":
    ephemeris = load_ephemeris("Ephemeris_1900_2079.csv")
    root = tk.Tk()
    app = SQ9App(root, ephemeris)
    root.mainloop()
