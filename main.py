import tkinter as tk
from PIL import Image, ImageTk
import random
import os

# ==================== CONFIG ==================== #
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
PLAYER_SIZE = 40
MOVE_SPEED = 20
DNA_PAIRS = {"A": "T", "T": "A", "G": "C", "C": "G"}
ASSETS_PATH = "assets"
LEVEL_UP_TIME_LIMIT = 90  # extended timer
MAX_WIN_LEVEL = 3
BASE_COLOR = "blue"
TEXT_COLOR = "black"

# ==================== ML MODEL ==================== #
class DifficultyModel:
    def __init__(self):
        self.streak = 0
    def record(self, correct):
        self.streak = self.streak + 1 if correct else max(0, self.streak - 1)
    def extra(self):
        return self.streak

# ==================== GAME ==================== #
class DNAIslandGame:
    def __init__(self, root):
        self.root = root
        self.root.title("DNA Island Adventure")
        self.canvas = tk.Canvas(root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        self.canvas.pack()

        self.scene = "hub"
        self.level = 1
        self.model = DifficultyModel()
        self.time_left = LEVEL_UP_TIME_LIMIT
        self.dropped = []  # track dropped labels

        self.load_images()
        self.show_hub()
        self.bind_keys()

    def load_images(self):
        def load(name): return ImageTk.PhotoImage(
            Image.open(os.path.join(ASSETS_PATH, name)).resize((WINDOW_WIDTH, WINDOW_HEIGHT)))
        self.hub_bg = load("hub_map.png")
        self.forest_bg = load("dna_forest.png")
        self.lab_bg = load("dna_lab_bg.png")
        self.player_img = ImageTk.PhotoImage(
            Image.open(os.path.join(ASSETS_PATH, "player.png")).resize((PLAYER_SIZE, PLAYER_SIZE)))

    def bind_keys(self):
        self.root.bind("<KeyPress>", self.on_key)

    def clear_ui(self):
        for w in list(self.root.winfo_children()):
            if w is not self.canvas:
                w.destroy()
        self.canvas.delete("all")

    # ------ HUB ------
    def show_hub(self):
        self.clear_ui()
        self.scene = "hub"
        self.canvas.create_image(0,0,anchor="nw",image=self.hub_bg)
        self.player = self.canvas.create_image(100,500,anchor="nw",image=self.player_img)
        self.hub_entrance = self.canvas.create_rectangle(130,100,220,200,outline="",fill="")

    # ------ FOREST ------
    def show_forest(self):
        self.clear_ui()
        self.scene = "dna_forest"
        self.canvas.create_image(0,0,anchor="nw",image=self.forest_bg)
        self.player = self.canvas.create_image(100,500,anchor="nw",image=self.player_img)
        self.lab_door = self.canvas.create_rectangle(700,100,780,200,outline="",fill="")
        tk.Button(self.root, text="Exit to Hub", bg=BASE_COLOR, fg=TEXT_COLOR,
                  width=4, height=2, relief="raised", command=self.show_hub).place(x=700, y=500)

    # ------ LAB ------
    def show_lab(self):
        if self.level > MAX_WIN_LEVEL:
            return self.show_win()
        self.clear_ui()
        self.scene = "dna_lab"
        self.canvas.create_image(0,0,anchor="nw",image=self.lab_bg)
        tk.Button(self.root, text="Exit to Hub", bg=BASE_COLOR, fg=TEXT_COLOR,
                  width=4, height=2, relief="raised", command=self.show_hub).place(x=700, y=500)
        self.level_label = tk.Label(self.root, text=f"Level: {self.level}",
                                    bg=BASE_COLOR, fg=TEXT_COLOR, width=8, height=2, relief="ridge")
        self.level_label.place(x=600, y=30)
        self.timer_label = tk.Label(self.root, text="Time: 0s",
                                    bg=BASE_COLOR, fg=TEXT_COLOR, width=8, height=2, relief="ridge")
        self.timer_label.place(x=600, y=80)
        self.setup_lab()

    def setup_lab(self):
        base_count = 4 + (self.level - 1) * 2 + self.model.extra()
        x0, y0 = 150, 150
        spacing = min(80, (WINDOW_WIDTH - 300) // base_count)

        self.empty_spots = []
        for i, base in enumerate(random.choices(list(DNA_PAIRS.keys()), k=base_count)):
            tk.Label(self.root, text=base, bg="lightblue", width=4, height=2, relief="ridge").place(x=x0 + i * spacing, y=y0)
            slot = tk.Label(self.root, text="", bg="white", width=4, height=2, relief="ridge")
            slot.place(x=x0 + i * spacing, y=y0 + 100)
            self.empty_spots.append((slot, base))

        self.counts = {b: 5 for b in DNA_PAIRS}
        pal_y = y0 + 200
        self.pal_btns = {}
        for j, b in enumerate(DNA_PAIRS):
            btn = tk.Button(self.root, text=f"{b} ({self.counts[b]})",
                            bg=BASE_COLOR, fg=TEXT_COLOR,
                            width=4, height=2, relief="raised",
                            command=lambda bb=b: self.spawn_base(bb))
            btn.place(x=150 + j * 100, y=pal_y)
            self.pal_btns[b] = btn

        tk.Button(self.root, text="Submit", bg=BASE_COLOR, fg=TEXT_COLOR,
                  width=4, height=2, relief="raised", command=self.on_submit).place(x=650, y=pal_y)

        self.start_timer()

    def spawn_base(self, base):
        if self.counts[base] <= 0:
            return
        self.counts[base] -= 1
        self.pal_btns[base].config(text=f"{base} ({self.counts[base]})")
        lbl = tk.Label(self.root, text=base,
                       bg=BASE_COLOR, fg=TEXT_COLOR,
                       width=4, height=2, relief="raised")
        lbl.place(x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT - 100)
        lbl.bind("<Button-1>", self.start_drag)
        lbl.bind("<B1-Motion>", self.do_drag)
        lbl.bind("<ButtonRelease-1>", self.stop_drag)
        self.dropped.append(lbl)

    def start_timer(self):
        self.time_left = LEVEL_UP_TIME_LIMIT
        self.timer_running = True
        self.update_timer()

    def update_timer(self):
        if not self.timer_running:
            return
        self.timer_label.config(text=f"Time: {self.time_left}s")
        if self.time_left > 0:
            self.time_left -= 1
            self.root.after(1000, self.update_timer)
        else:
            self.timer_running = False
            self.model.record(False)
            self.level = max(1, self.level - 1)
            self.show_lab()

    def start_drag(self, e):
        w = e.widget
        w.sx, w.sy = e.x, e.y

    def do_drag(self, e):
        w = e.widget
        w.place(x=w.winfo_x() - w.sx + e.x,
                y=w.winfo_y() - w.sy + e.y)

    def stop_drag(self, e):
        w = e.widget
        for slot, base in self.empty_spots:
            sx, sy = slot.winfo_rootx(), slot.winfo_rooty()
            wx, wy = w.winfo_rootx(), w.winfo_rooty()
            if abs(sx - wx) < 40 and abs(sy - wy) < 40:
                slot.config(text=w["text"], bg="lightgreen")
                w.destroy()
                break

    def on_submit(self):
        # Ensure all slots are filled and correct
        correct = True
        for slot, base in self.empty_spots:
            if slot["text"] != DNA_PAIRS[base]:
                slot.config(bg="red")
                correct = False
            else:
                slot.config(bg="lightgreen")

        if correct:
            self.model.record(True)
            self.level += 1
        else:
            self.model.record(False)
            # reset dropped bases if incorrect
            for widget in self.dropped:
                widget.destroy()
            self.dropped.clear()
            for slot, _ in self.empty_spots:
                slot.config(text="", bg="white")
            self.counts = {b:5 for b in DNA_PAIRS}
            for b, btn in self.pal_btns.items():
                btn.config(text=f"{b} (5)")

        self.show_lab()

    def show_win(self):
        self.clear_ui()
        tk.Label(self.root, text="YOU WIN!", font=("Arial", 32), fg="green").place(x=WINDOW_WIDTH//2, y=WINDOW_HEIGHT//2, anchor="c")
        tk.Button(self.root, text="Restart", bg=BASE_COLOR, fg=TEXT_COLOR,
                  width=4, height=2, relief="raised",
                  command=lambda: setattr(self, 'level', 1) or self.show_hub()).place(x=WINDOW_WIDTH//2, y=WINDOW_HEIGHT//2+50, anchor="c")

    def on_key(self, e):
        if self.scene not in ["hub", "dna_forest"]:
            return
        dx = dy = 0
        if e.keysym == "Up":    dy = -MOVE_SPEED
        if e.keysym == "Down":  dy = MOVE_SPEED
        if e.keysym == "Left":  dx = -MOVE_SPEED
        if e.keysym == "Right": dx = MOVE_SPEED
        self.canvas.move(self.player, dx, dy)
        self.check_collision()

    def check_collision(self):
        pc = self.canvas.bbox(self.player)
        if self.scene == "hub":
            dc = self.canvas.coords(self.hub_entrance)
            if not(pc[2]<dc[0] or pc[0]>dc[2] or pc[3]<dc[1] or pc[1]>dc[3]):
                self.show_forest()
        elif self.scene == "dna_forest":
            dc = self.canvas.coords(self.lab_door)
            if not(pc[2]<dc[0] or pc[0]>dc[2] or pc[3]<dc[1] or pc[1]>dc[3]):
                self.show_lab()

if __name__ == "__main__":
    root = tk.Tk()
    app = DNAIslandGame(root)
    root.mainloop()
