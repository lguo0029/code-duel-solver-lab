"""Run a real, reproducible GUI scene for screenshots (no fabricated widgets)."""

import argparse

from code_duel.engine import Game
from code_duel.gui import MANUAL, App
from code_duel.rules import score

parser = argparse.ArgumentParser()
parser.add_argument("--stage", choices=["menu", "game", "explain", "result"], default="menu")
parser.add_argument("--language", choices=["en", "zh"], default="en")
args = parser.parse_args()
app = App()
app.language.set("English" if args.language == "en" else "简体中文")
app.menu()
if args.stage != "menu":
    if not MANUAL:
        app.secret.set("0037")
    app.level.set(app.t("hard"))
    app.start()
    app.game = Game(4 if MANUAL else "0037", "hard", seed=42, ai_secret="9999")
    guesses = iter(["1111", "2222"] + (["9999"] if args.stage == "result" else []))

    def advance():
        if app.busy:
            app.after(50, advance)
            return
        if app.game.outcome is not None:
            return
        if MANUAL and app.game.pending is not None:
            app.feedback.set(str(score("0037", app.game.pending[1])))
            app.confirm_feedback()
            app.after(50, advance)
            return
        guess = next(guesses, None)
        if guess is None:
            return
        app.guess.set(guess)
        app.submit()
        app.after(50, advance)

    app.after(100, advance)
app.mainloop()
