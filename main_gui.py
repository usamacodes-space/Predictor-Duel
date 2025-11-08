# I acknowledge the use of ChatGPT (OpenAI, GPT-5) to co-create this file.

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from game_logic import GameEngine


class PredictorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Predictor Duel")
        self.geometry("540x420")
        self.resizable(False, False)

        self.engine = None

        ttk.Label(self, text="Predictor Duel", font=("Segoe UI", 16, "bold")).pack(pady=8)

        ctrl = ttk.Frame(self)
        ctrl.pack(pady=4)
        ttk.Label(ctrl, text="Rounds:").grid(row=0, column=0, padx=3)
        self.rounds = tk.IntVar(value=50)
        ttk.Entry(ctrl, textvariable=self.rounds, width=6).grid(row=0, column=1, padx=3)
        ttk.Label(ctrl, text="Difficulty (n):").grid(row=0, column=2, padx=3)
        self.ngram = tk.IntVar(value=2)
        ttk.Spinbox(ctrl, from_=1, to=4, textvariable=self.ngram, width=4).grid(row=0, column=3, padx=3)
        ttk.Button(ctrl, text="Start", command=self.start_game).grid(row=0, column=4, padx=6)

        self.info = ttk.Label(self, text="", font=("Consolas", 10))
        self.info.pack(pady=6)

        self.buttons = ttk.Frame(self)
        self.btn0 = ttk.Button(self.buttons, text="0", command=lambda: self.play(0), width=8)
        self.btn1 = ttk.Button(self.buttons, text="1", command=lambda: self.play(1), width=8)
        self.btn0.grid(row=0, column=0, padx=10, pady=10)
        self.btn1.grid(row=0, column=1, padx=10, pady=10)
        self.buttons.pack()

        self.log = tk.Text(self, height=10, width=58, state="disabled", wrap="none")
        self.log.pack(pady=8)

        exp_frame = ttk.Frame(self)
        exp_frame.pack()
        ttk.Button(exp_frame, text="Export CSV", command=self.export_csv).grid(row=0, column=0, padx=5)
        ttk.Button(exp_frame, text="Reset", command=self.reset).grid(row=0, column=1, padx=5)
        ttk.Button(exp_frame, text="Exit", command=self.destroy).grid(row=0, column=2, padx=5)

        self.disable_play()

    def start_game(self):
        try:
            n = self.ngram.get()
            rounds = self.rounds.get()
            self.engine = GameEngine(rounds=rounds, n=n)
            self.enable_play()
            self.log_clear()
            self.info.config(text=f"Game started — rounds: {rounds}, difficulty n={n}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def play(self, bit):
        if not self.engine or self.engine.is_finished():
            return
        result = self.engine.turn(bit)
        self.append_log(result)
        if self.engine.is_finished():
            self.disable_play()
            summary = self.engine.summary()
            msg = (f"Game finished!\nPlayer: {summary['player_score']}  "
                   f"AI: {summary['ai_score']}")
            messagebox.showinfo("Summary", msg)

    def append_log(self, result):
        self.log.config(state="normal")
        self.log.insert("end",
            f"Round {result.round_no:02d}: AI predicted {result.ai_prediction}, "
            f"You {result.player_bit} → {'AI' if result.correct else 'You'} scored\n")
        self.log.see("end")
        self.log.config(state="disabled")

        s = self.engine.summary()
        self.info.config(
            text=f"Player {s['player_score']}  |  AI {s['ai_score']}  |  "
                 f"Remaining {self.engine.remaining()}"
        )

    def export_csv(self):
        if not self.engine:
            messagebox.showwarning("Export", "No session yet.")
            return
        file = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files","*.csv")])
        if not file:
            return
        self.engine.export_csv(file)
        messagebox.showinfo("Export", f"Saved to {file}")

    def reset(self):
        if self.engine:
            self.engine.reset()
        self.log_clear()
        self.disable_play()
        self.info.config(text="Game reset")

    def enable_play(self):
        self.btn0.state(["!disabled"])
        self.btn1.state(["!disabled"])

    def disable_play(self):
        self.btn0.state(["disabled"])
        self.btn1.state(["disabled"])

    def log_clear(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")


def main():
    app = PredictorGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
