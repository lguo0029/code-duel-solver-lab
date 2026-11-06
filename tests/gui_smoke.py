"""Real-window integration test; run under Xvfb on headless Linux."""

import time
from unittest.mock import patch

from code_duel.engine import Game
from code_duel.gui import MANUAL, App


def settle(app):
    deadline = time.monotonic() + 20
    while app.busy and time.monotonic() < deadline:
        app.update()
        time.sleep(0.01)
    app.update()
    assert not app.busy


def main():
    app = App()
    try:
        app.update()
        assert app.t("start") == "Start duel"
        app.language.set("简体中文")
        app.menu()
        assert app.t("start") == "开始对决"
        if MANUAL:
            assert not hasattr(app, "secret_entry")
            app.length_choice.set("2")
            app.start()
            app.game = Game(2, "easy", ai_secret="99")
            with patch("code_duel.engine.choose", side_effect=["00", "01", "10"]):
                for feedback in [1, 0]:
                    app.guess.set("22")
                    app.submit()
                    settle(app)
                    app.feedback.set(str(feedback))
                    app.confirm_feedback()
                    settle(app)
                app.guess.set("99")
                app.submit()
                settle(app)
                app.feedback.set("0")
                with patch("code_duel.gui.messagebox.showerror") as warning:
                    app.confirm_feedback()
                    settle(app)
                    assert warning.called
                assert len(app.game.rounds) == 2 and app.game.pending is not None
                app.feedback.set("2")
                app.confirm_feedback()
                settle(app)
            assert app.game.outcome == "draw"
            assert all(len(t.get_children()) == 3 for t in app.tables)
        else:
            assert app.secret_entry.cget("show") == "•"
            app.secret.set("0037")
            app.start()
            app.game = Game("0037", "easy", ai_secret="9999")
            with patch("code_duel.engine.choose", side_effect=["1234", "0037"]):
                for guess in ["1111", "9999"]:
                    app.guess.set(guess)
                    app.submit()
                    settle(app)
            assert app.game.outcome == "draw"
            assert all(len(t.get_children()) == 2 for t in app.tables)
        with patch("code_duel.gui.messagebox.askyesno", return_value=True):
            app.reset_game()
        app.language.set("English")
        app.menu()
        if MANUAL:
            app.length_choice.set("10")
            app.start()
            app.guess.set("0" * 10)
            app.submit()
            settle(app)
            app.feedback.set("10")
            app.confirm_feedback()
            settle(app)
            assert app.game.outcome in ("ai", "draw")
        else:
            app.secret.set("0037")
            app.start()
            app.guess.set("1111")
            app.submit()
            settle(app)
            assert len(app.game.rounds) == 1
        print(
            "PASS: English/Chinese setup and gameplay, real worker rounds, history, draw, reset, close"
            + (
                "; manual contradiction/correction and length 10"
                if MANUAL
                else "; hidden secret and automatic scoring"
            )
        )
    finally:
        app.destroy()


if __name__ == "__main__":
    main()
