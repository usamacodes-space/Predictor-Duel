# I acknowledge the use of ChatGPT (OpenAI, GPT-5) to co-create this file.

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from game_logic import GameEngine

# Clear, user-facing copy (no jargon like "n")
HELP_TEXT = (
    "Predictor Duel — How to play\n\n"
    "Goal: Outsmart the AI. Each round it tries to predict your next choice (0 or 1).\n\n"
    "Why 0/1? The game is a simple pattern duel. Humans fall into habits; the AI learns\n"
    "those habits and predicts your next move. You score by being less predictable.\n\n"
    "Controls:\n"
    "• Rounds = total turns.\n"
    "• AI memory = how many of your last moves the AI studies (1–4). Higher memory learns\n"
    "  faster and predicts better.\n\n"
    "Scoring:\n"
    "• AI +1 if it predicts correctly. You +1 if you surprise it.\n"
    "• Export CSV saves the full session log (round, prediction, scores).\n"
)

class Toast(tk.Toplevel):
    """Tiny, transient toast window (auto-destroys)."""
    def __init__(self, master, text, duration_ms=1500):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text=text).pack()
        # Position bottom-right of parent
        self.update_idletasks()
        x = master.winfo_rootx() + master.winfo_width() - self.winfo_width() - 24
        y = master.winfo_rooty() + master.winfo_height() - self.winfo_height() - 24
        self.geometry(f"+{x}+{y}")
        self.after(duration_ms, self.destroy)

class PredictorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Predictor Duel")
        self.geometry("760x560")
        self.minsize(720, 520)
        self.resizable(True, True)
        self.engine: GameEngine | None = None

        # Root grid (header, controls, board, log, footer)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # log grows

        # Header — purpose statement
        header = ttk.Frame(self, padding=(12, 10))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Predictor Duel", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            header,
            text=(
                "Purpose: the AI learns your patterns and tries to predict your next move (0 or 1). "
                "Be less predictable to win."
            ),
            foreground="#444",
        ).pack(anchor="w", pady=(2, 0))

        # Controls
        controls = ttk.Frame(self, padding=(12, 6))
        controls.grid(row=1, column=0, sticky="ew")
        controls.grid_columnconfigure(8, weight=1)

        ttk.Label(controls, text="Rounds:").grid(row=0, column=0, padx=(0, 6))
        self.rounds = tk.IntVar(value=50)
        ttk.Entry(controls, textvariable=self.rounds, width=7).grid(row=0, column=1, padx=(0, 16))

        ttk.Label(controls, text="AI memory (last moves studied):").grid(row=0, column=2, padx=(0, 6))
        self.ai_memory = tk.IntVar(value=2)  # replaces "n"
        ttk.Spinbox(controls, from_=1, to=4, textvariable=self.ai_memory, width=5).grid(row=0, column=3, padx=(0, 16))

        ttk.Button(controls, text="Start", command=self.start_game).grid(row=0, column=4, padx=(0, 8))
        ttk.Button(controls, text="Help", command=lambda: messagebox.showinfo("Help", HELP_TEXT)).grid(row=0, column=5)

        # Board: prediction banner + scoreboard + action buttons
        board = ttk.Frame(self, padding=(12, 6))
        board.grid(row=2, column=0, sticky="ew")
        board.grid_columnconfigure(0, weight=1)

        self.pred_banner = ttk.Label(board, text="Press Start to begin", font=("Segoe UI", 12, "bold"))
        self.pred_banner.grid(row=0, column=0, sticky="w")

        scorebar = ttk.Frame(board)
        scorebar.grid(row=1, column=0, sticky="w", pady=(6, 2))
        self.score_player = ttk.Label(scorebar, text="You: 0", font=("Segoe UI", 11))
        self.score_ai = ttk.Label(scorebar, text="AI: 0", font=("Segoe UI", 11))
        self.score_rem = ttk.Label(scorebar, text="Remaining: 0", font=("Segoe UI", 11))
        self.score_player.pack(side="left"); ttk.Label(scorebar, text="   ").pack(side="left")
        self.score_ai.pack(side="left");    ttk.Label(scorebar, text="   ").pack(side="left")
        self.score_rem.pack(side="left")

        actions = ttk.Frame(board)
        actions.grid(row=2, column=0, pady=(8, 0))
        self.btn0 = ttk.Button(actions, text="Choose 0", command=lambda: self.play(0), width=12)
        self.btn1 = ttk.Button(actions, text="Choose 1", command=lambda: self.play(1), width=12)
        self.btn0.grid(row=0, column=0, padx=12)
        self.btn1.grid(row=0, column=1, padx=12)

        self.flash = ttk.Label(board, text="", font=("Segoe UI", 10))
        self.flash.grid(row=3, column=0, sticky="w", pady=(6, 0))

        # Log (scrollable)
        logwrap = ttk.Frame(self, padding=(12, 6))
        logwrap.grid(row=3, column=0, sticky="nsew")
        logwrap.grid_columnconfigure(0, weight=1)
        logwrap.grid_rowconfigure(0, weight=1)
        self.log = tk.Text(logwrap, wrap="none")
        yscroll = ttk.Scrollbar(logwrap, orient="vertical", command=self.log.yview)
        xscroll = ttk.Scrollbar(logwrap, orient="horizontal", command=self.log.xview)
        self.log.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.log.grid(row=0, column=0, sticky="nsew"); yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew"); self.log.config(state="disabled", height=12)

        # Footer
        footer = ttk.Frame(self, padding=(12, 10))
        footer.grid(row=4, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        btns = ttk.Frame(footer); btns.pack(anchor="e")
        ttk.Button(btns, text="Export CSV", command=self.export_csv).grid(row=0, column=0, padx=6)
        ttk.Button(btns, text="Reset", command=self.reset).grid(row=0, column=1, padx=6)
        ttk.Button(btns, text="Exit", command=self.destroy).grid(row=0, column=2, padx=6)

        self.disable_play()

    # ---------- Helpers ----------
    def _update_prediction_banner(self):
        if not self.engine:
            self.pred_banner.config(text="Press Start to begin", foreground="#333")
            return
        try:
            nxt = self.engine.predictor.predict(self.engine.history)
            self.pred_banner.config(text=f"AI predicts your next move: {nxt}", foreground="#006699")
        except Exception:
            self.pred_banner.config(text="AI is thinking…", foreground="#006699")

    def _update_scores(self):
        s = self.engine.summary()
        self.score_player.config(text=f"You: {s['player_score']}")
        self.score_ai.config(text=f"AI: {s['ai_score']}")
        self.score_rem.config(text=f"Remaining: {self.engine.remaining()}")

    def _append_log(self, text):
        self.log.config(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _flash_msg(self, text, you_scored: bool | None):
        color = "#2e7d32" if you_scored is True else "#c62828" if you_scored is False else "#333333"
        self.flash.config(text=text, foreground=color)

    def _toast(self, text, ms=1500):
        Toast(self, text, ms)

    def enable_play(self):
        self.btn0.state(["!disabled"]); self.btn1.state(["!disabled"])

    def disable_play(self):
        self.btn0.state(["disabled"]); self.btn1.state(["disabled"])

    def clear_log(self):
        self.log.config(state="normal"); self.log.delete("1.0", "end"); self.log.config(state="disabled")

    # ---------- Actions ----------
    def start_game(self):
        try:
            mem = int(self.ai_memory.get())   # renamed from n
            rounds = int(self.rounds.get())
            self.engine = GameEngine(rounds=rounds, n=mem)
            self.clear_log()
            self._flash_msg("Game started. Outsmart the predictor.", None)
            self._toast("New game launched ✅")
            self.enable_play()
            self._update_scores()
            self._update_prediction_banner()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def play(self, bit: int):
        if not self.engine or self.engine.is_finished():
            return
        r = self.engine.turn(bit)
        who = "AI" if r.correct else "You"
        self._append_log(
            f"Round {r.round_no:02d} | AI predicted {r.ai_prediction} | "
            f"You played {r.player_bit} → {who} scored"
        )
        self._flash_msg(f"{who} scored this round.", you_scored=(who == "You"))
        self._update_scores()

        if self.engine.is_finished():
            self.disable_play()
            s = self.engine.summary()
            if s['player_score'] > s['ai_score']:
                crown = "🎉 You win! Less predictable, more brilliant."
            elif s['player_score'] < s['ai_score']:
                crown = "🤖 AI wins. Try randomizing your patterns!"
            else:
                crown = "🤝 Draw. Perfectly balanced, as all things should be."
            self._toast(crown, ms=2500)
            messagebox.showinfo("Final Result", f"{crown}\n\nFinal — You {s['player_score']} : AI {s['ai_score']}")
            self.pred_banner.config(text="Game finished.", foreground="#333")
        else:
            self._update_prediction_banner()

    def export_csv(self):
        if not self.engine or self.engine.round_no == 0:
            messagebox.showwarning("Export", "No session to export yet.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        self.engine.export_csv(path)
        self._toast("CSV saved 💾")
        messagebox.showinfo("Export", f"Saved session log to:\n{path}")

    def reset(self):
        if self.engine:
            self.engine.reset()
        self.disable_play()
        self._update_scores()
        self._update_prediction_banner()
        self.clear_log()
        self._flash_msg("Game reset. Press Start to begin a new session.", None)
        self._toast("Session reset ↺")

def main():
    app = PredictorGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
