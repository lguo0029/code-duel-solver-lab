"""Bilingual Tk interface. Worker threads never call Tk APIs."""

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from .constraints import Contradiction, SearchLimit
from .engine import Game
from .i18n import text
from .rules import validate

MANUAL = True
LEVELS = ("easy", "medium", "hard")


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.geometry("1120x860")
        self.minsize(960, 780)
        self.configure(bg="#101827")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background="#101827", foreground="#e5edf9", font=("Arial", 12))
        style.configure("TButton", padding=9, background="#2563eb")
        style.configure("TEntry", fieldbackground="#20324a", foreground="white", padding=8)
        style.configure("TCombobox", fieldbackground="#20324a", foreground="#101827", padding=5)
        style.configure(
            "Treeview",
            background="#18253b",
            fieldbackground="#18253b",
            foreground="#e5edf9",
            rowheight=27,
        )
        style.configure("Treeview.Heading", background="#233752", foreground="white")
        self.language = tk.StringVar(value="English")
        self.game = None
        self.busy = False
        self.events = queue.Queue()
        self.bind("<Return>", self.enter)
        self.after(40, self.poll)
        self.menu()

    def t(self, key: str, **kwargs) -> str:
        return text(key, "zh" if self.language.get() == "简体中文" else "en", **kwargs)

    def clear(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

    def menu(self, event=None) -> None:
        self.clear()
        self.game = None
        self.title(self.t("lab_title" if MANUAL else "title"))
        frame = ttk.Frame(self, padding=35)
        frame.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text="CODE DUEL" + (" / SOLVER LAB" if MANUAL else ""),
            font=("Arial", 28, "bold"),
        ).pack(pady=(20, 12))
        selector = ttk.Combobox(
            frame,
            textvariable=self.language,
            values=["English", "简体中文"],
            state="readonly",
            width=25,
        )
        selector.pack(pady=8)
        selector.bind("<<ComboboxSelected>>", self.menu)
        ttk.Label(
            frame, text=self.t("manual_rules" if MANUAL else "auto_rules"), justify="center"
        ).pack(pady=22)
        ttk.Label(frame, text=self.t("level")).pack(pady=6)
        self.level = tk.StringVar(value=self.t("medium"))
        ttk.Combobox(
            frame,
            textvariable=self.level,
            values=[self.t(k) for k in LEVELS],
            state="readonly",
            width=34,
        ).pack(pady=8)
        if MANUAL:
            ttk.Label(frame, text=self.t("length")).pack(pady=8)
            self.length_choice = tk.StringVar(value="4")
            ttk.Combobox(
                frame,
                textvariable=self.length_choice,
                values=list(map(str, range(1, 11))),
                state="readonly",
                width=20,
            ).pack(pady=8)
            ttk.Label(frame, text=self.t("limitations")).pack(pady=12)
        else:
            ttk.Label(frame, text=self.t("secret")).pack(pady=8)
            self.secret = tk.StringVar()
            self.secret_entry = ttk.Entry(
                frame, textvariable=self.secret, show="•", justify="center", width=20
            )
            self.secret_entry.pack(pady=8)
            self.visible = tk.BooleanVar()
            ttk.Checkbutton(
                frame,
                text=self.t("show"),
                variable=self.visible,
                command=lambda: self.secret_entry.configure(show="" if self.visible.get() else "•"),
            ).pack(pady=6)
            self.secret_entry.focus_set()
        ttk.Button(frame, text=self.t("start"), command=self.start).pack(pady=15)

    def start(self) -> None:
        difficulty = LEVELS[[self.t(k) for k in LEVELS].index(self.level.get())]
        try:
            if MANUAL:
                self.game = Game(int(self.length_choice.get()), difficulty)
            else:
                self.game = Game(self.secret.get(), difficulty)
                self.secret.set("")
        except ValueError:
            messagebox.showerror(self.t("error"), self.t("invalid", length=4), parent=self)
            return
        self.clear()
        root = ttk.Frame(self, padding=20)
        root.pack(fill="both", expand=True)
        self.status = ttk.Label(
            root,
            text=self.t("round_prompt", length=self.game.length, round=1),
            font=("Arial", 17, "bold"),
        )
        self.status.pack(pady=10)
        body = ttk.Frame(root)
        body.pack(fill="both", expand=True)
        self.tables = []
        for i, title in enumerate(("player", "ai")):
            pane = ttk.Frame(body, padding=12)
            pane.pack(side="left", fill="both", expand=True)
            ttk.Label(pane, text=self.t(title), font=("Arial", 18, "bold")).pack(pady=8)
            if i == 0:
                self.guess = tk.StringVar()
                self.guess_entry = ttk.Entry(
                    pane, textvariable=self.guess, font=("Courier", 22), justify="center", width=16
                )
                self.guess_entry.pack(pady=8)
                self.submit_button = ttk.Button(pane, text=self.t("submit"), command=self.submit)
                self.submit_button.pack(pady=6)
                self.guess_entry.focus_set()
            else:
                self.ai_cards = ttk.Label(
                    pane, text=" ".join("—" * self.game.length), font=("Courier", 21, "bold")
                )
                self.ai_cards.pack(pady=8)
                if MANUAL:
                    ttk.Label(pane, text=self.t("feedback")).pack(pady=4)
                    self.feedback = tk.StringVar()
                    self.feedback_box = ttk.Combobox(
                        pane,
                        textvariable=self.feedback,
                        values=list(map(str, range(self.game.length + 1))),
                        state="disabled",
                        width=8,
                    )
                    self.feedback_box.pack(pady=4)
                    self.feedback_button = ttk.Button(
                        pane,
                        text=self.t("confirm"),
                        command=self.confirm_feedback,
                        state="disabled",
                    )
                    self.feedback_button.pack(pady=4)
            holder = ttk.Frame(pane)
            holder.pack(fill="both", expand=True, pady=12)
            tree = ttk.Treeview(
                holder, columns=("round", "guess", "matches"), show="headings", height=9
            )
            for key in ("round", "guess", "matches"):
                tree.heading(key, text=self.t(key))
                tree.column(key, width=115, anchor="center")
            bar = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=bar.set)
            tree.pack(side="left", fill="both", expand=True)
            bar.pack(side="right", fill="y")
            self.tables.append(tree)
        self.count_label = ttk.Label(root)
        self.count_label.pack(pady=3)
        self.metrics = ttk.Label(root, text=self.t("initial"), justify="center")
        self.metrics.pack(pady=4)
        self.validation_label = ttk.Label(root, text="")
        self.validation_label.pack(pady=3)
        self.result = ttk.Label(root, text="", justify="center")
        self.result.pack(pady=4)
        self.reset_button = ttk.Button(root, text=self.t("reset"), command=self.reset_game)
        self.reset_button.pack(pady=4)
        self.show_count()

    def show_count(self) -> None:
        self.count_label.configure(
            text=self.t(
                "candidate_exact" if self.game.length <= 4 else "candidate_sample",
                count=self.game.candidate_count,
            )
        )

    def show_metrics(self) -> None:
        info = self.game.decision
        if info is None:
            return
        if info.answer_sample == 0:
            label = self.t("metrics_random", strategy=self.t(info.strategy), ms=info.seconds * 1000)
        else:
            label = self.t(
                "metrics_search",
                strategy=self.t(info.strategy),
                ms=info.seconds * 1000,
                answers=info.answer_sample,
                worst=info.worst_bucket,
                entropy=self.t("entropy", bits=info.entropy_bits)
                if info.entropy_bits is not None
                else self.t("no_entropy"),
                scope=self.t("exact" if info.exact_distribution else "sampled"),
            )
        self.metrics.configure(text=label)

    def enter(self, event=None) -> None:
        if self.busy:
            return
        if self.game is None:
            self.start()
        elif MANUAL and self.game.pending is not None:
            self.confirm_feedback()
        else:
            self.submit()

    def reset_game(self) -> None:
        if not self.busy and messagebox.askyesno(
            self.t("reset_title"), self.t("reset_body"), parent=self
        ):
            self.menu()

    def launch(self, operation, kind: str) -> None:
        self.busy = True
        self.submit_button.configure(state="disabled")
        self.guess_entry.configure(state="disabled")
        self.reset_button.configure(state="disabled")
        if MANUAL:
            self.feedback_button.configure(state="disabled")
            self.feedback_box.configure(state="disabled")

        def worker():
            try:
                self.events.put((kind, operation()))
            except Exception as exc:
                self.events.put(("error", exc))

        threading.Thread(target=worker, daemon=True).start()

    def submit(self) -> None:
        if self.busy or self.game is None or self.game.outcome is not None:
            return
        if MANUAL and self.game.pending is not None:
            return
        try:
            guess = validate(self.guess.get(), self.game.length)
        except ValueError:
            messagebox.showerror(
                self.t("error"), self.t("invalid", length=self.game.length), parent=self
            )
            return
        self.status.configure(text=self.t("working"))
        self.launch(
            lambda: self.game.begin_round(guess) if MANUAL else self.game.play_round(guess),
            "guess" if MANUAL else "round",
        )

    def confirm_feedback(self) -> None:
        if not MANUAL or self.busy or self.game is None or self.game.pending is None:
            return
        if self.feedback.get() == "":
            messagebox.showerror(self.t("error"), self.t("choose_feedback"), parent=self)
            return
        value = int(self.feedback.get())
        self.status.configure(text=self.t("validating"))
        self.launch(lambda: self.game.finish_round(value), "round")

    def show_validation(self) -> None:
        result = self.game.validation if MANUAL else None
        if result is not None:
            status_key = (
                "unknown_status" if result.status.value == "unknown" else result.status.value
            )
            self.validation_label.configure(
                text=self.t("validation", status=self.t(status_key), ms=result.seconds * 1000)
            )

    def poll(self) -> None:
        try:
            kind, value = self.events.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            self.reset_button.configure(state="normal")
            if kind == "error":
                key = (
                    "unknown"
                    if isinstance(value, SearchLimit)
                    else "contradiction"
                    if isinstance(value, Contradiction)
                    else "failure"
                )
                self.status.configure(text=self.t(key))
                self.show_validation()
                messagebox.showerror(self.t("error"), self.t(key), parent=self)
                if MANUAL and self.game.pending is not None:
                    self.feedback_button.configure(state="normal")
                    self.feedback_box.configure(state="readonly")
                elif key != "failure":
                    self.submit_button.configure(state="normal")
                    self.guess_entry.configure(state="normal")
            elif kind == "guess":
                self.ai_cards.configure(text=" ".join(value))
                self.feedback.set("")
                self.feedback_button.configure(state="normal")
                self.feedback_box.configure(state="readonly")
                self.status.configure(
                    text=self.t(
                        "awaiting", round=len(self.game.rounds) + 1, length=self.game.length
                    )
                )
                self.show_metrics()
            else:
                r = value
                for table, guess, matches in zip(
                    self.tables, (r.player_guess, r.ai_guess), (r.player_score, r.ai_score)
                ):
                    row = table.insert(
                        "", "end", values=(r.number, guess, f"{matches} / {self.game.length}")
                    )
                    table.see(row)
                self.ai_cards.configure(text=" ".join(r.ai_guess))
                self.guess.set("")
                self.show_count()
                self.show_metrics()
                self.show_validation()
                if self.game.outcome is not None:
                    self.status.configure(
                        text=self.t(
                            {"player": "player_win", "ai": "ai_win", "draw": "draw"}[
                                self.game.outcome
                            ]
                        )
                    )
                    if MANUAL:
                        self.result.configure(
                            text=self.t("manual_result", ai=self.game.reveal(), rounds=r.number)
                        )
                    else:
                        human, ai = self.game.reveal()
                        self.result.configure(
                            text=self.t(
                                "auto_result", human=human, ai=ai, rounds=r.number, length=4
                            )
                        )
                else:
                    self.status.configure(
                        text=self.t("round_prompt", round=r.number + 1, length=self.game.length)
                    )
                    self.submit_button.configure(state="normal")
                    self.guess_entry.configure(state="normal")
        self.after(40, self.poll)


def main() -> None:
    App().mainloop()
