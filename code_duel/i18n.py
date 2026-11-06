"""User-visible strings: English and Simplified Chinese."""

STRINGS = {
    "title": ("CodeDuel — Human vs AI", "CodeDuel — 数字对决"),
    "lab_title": ("CodeDuel Solver Lab", "CodeDuel 求解实验室"),
    "auto_rules": (
        "Choose a four-digit secret. The engine scores both sides automatically.\nOnly matching digits in matching positions count. A same-round win is a draw.",
        "设置四位秘密数字，系统为双方自动评分。\n只计算数字与位置同时正确的位数；同轮猜中为平局。",
    ),
    "manual_rules": (
        "Keep your secret on paper or in mind — never enter it here.\nAfter each AI guess, select how many positions match.\nFeedback is checked against every previous clue.",
        "把秘密组合记在心里或纸上，不要输入游戏。\n每次 AI 猜测后，选择它猜对的位置数。\n系统会校验反馈与所有历史线索是否一致。",
    ),
    "level": ("AI difficulty", "AI 难度"),
    "easy": ("Easy · random", "慢 · 随机候选"),
    "medium": ("Medium · heuristic", "中 · 采样启发式"),
    "hard": ("Hard · entropy / minimax", "快 · 信息熵 / Minimax"),
    "length": ("Code length (1–10 digits)", "比赛数字长度（1–10 位）"),
    "secret": ("Your four-digit secret", "你的四位秘密数字"),
    "show": ("Show secret", "显示秘密"),
    "start": ("Start duel", "开始对决"),
    "player": ("YOU → AI", "玩家 → AI"),
    "ai": ("AI → YOU", "AI → 玩家"),
    "submit": ("Submit guess ↵", "提交猜测 ↵"),
    "feedback": ("How many AI positions match your secret?", "AI 有几位数字和位置同时正确？"),
    "confirm": ("Confirm feedback ↵", "确认正确位数 ↵"),
    "round": ("Round", "轮次"),
    "guess": ("Guess", "猜测"),
    "matches": ("Matches", "正确位数"),
    "reset": ("New game / main menu", "重新开始 / 主菜单"),
    "reset_title": ("Restart?", "重新开始？"),
    "reset_body": (
        "Discard this game and return to the setup screen?",
        "结束本局并返回设置页面吗？",
    ),
    "round_prompt": (
        "{length}-digit duel · Round {round} · Enter your guess",
        "{length} 位数字对决 · 第 {round} 回合 · 输入你的猜测",
    ),
    "working": ("AI is reasoning…", "AI 正在推理…"),
    "validating": ("Checking all feedback constraints…", "正在校验全部历史约束…"),
    "awaiting": (
        "Round {round} · Select AI matches (0–{length})",
        "第 {round} 回合 · 请选择 AI 正确位数（0–{length}）",
    ),
    "error": ("Please check", "请检查"),
    "invalid": (
        "Enter exactly {length} ASCII digits (0–9). Repeats and leading zeros are allowed.",
        "请输入恰好 {length} 位 ASCII 数字（0–9），允许重复及前导零。",
    ),
    "choose_feedback": ("Select a feedback value before continuing.", "请先选择 AI 猜对的位数。"),
    "contradiction": (
        "This feedback contradicts this or earlier clues. The round was not saved. Check your feedback and try again.",
        "反馈与本轮或更早的线索矛盾，无法同时成立。本轮尚未提交，请检查并修改反馈。",
    ),
    "unknown": (
        "UNKNOWN: the validation budget was reached without a witness or a contradiction proof. This round was not saved.",
        "无法判定：计算达到上限，既未找到合法答案，也未证明矛盾。本轮尚未提交。",
    ),
    "failure": (
        "The operation stopped because of an internal consistency error. Restart this game.",
        "内部一致性校验异常，操作已停止，请重新开始。",
    ),
    "candidate_exact": ("Valid candidates: {count} (exact)", "合法候选：{count}（精确）"),
    "candidate_sample": (
        "Valid samples: {count} · total not counted",
        "合法样本：{count} · 总候选数未计算",
    ),
    "metrics_random": (
        "{strategy} · {ms:.2f} ms · no distribution scoring",
        "{strategy} · {ms:.2f} 毫秒 · 未计算反馈分布",
    ),
    "metrics_search": (
        "{strategy} · {ms:.2f} ms\nAnswer sample: {answers} · largest bucket: {worst}\n{entropy} · {scope}",
        "{strategy} · {ms:.2f} 毫秒\n答案样本：{answers} · 最大反馈桶：{worst}\n{entropy} · {scope}",
    ),
    "entropy": ("Entropy: {bits:.3f} bits", "信息熵：{bits:.3f} 比特"),
    "no_entropy": ("Expected remaining-size heuristic", "预期剩余量启发式"),
    "exact": ("exact distribution", "精确分布"),
    "sampled": ("sampled distribution", "采样分布"),
    "player_win": ("You win!", "你获胜了！"),
    "ai_win": ("AI wins", "AI 获胜"),
    "draw": ("Same-round success · Draw", "同轮猜中 · 平局"),
    "auto_result": (
        "Your secret: {human}   AI secret: {ai}\n{rounds} rounds per side · {length} digits",
        "你的秘密：{human}    AI 秘密：{ai}\n双方各猜 {rounds} 轮 · {length} 位",
    ),
    "manual_result": (
        "AI secret: {ai}\nYour secret was never collected. {rounds} rounds per side.",
        "AI 秘密：{ai}\n游戏从未收集你的秘密数字。双方各猜 {rounds} 轮。",
    ),
    "validation": ("Validation: {status} · {ms:.2f} ms", "反馈校验：{status} · {ms:.2f} 毫秒"),
    "consistent": ("Consistent", "一致"),
    "contradictory": ("Contradictory", "矛盾"),
    "unknown_status": ("Unknown", "无法判定"),
    "limitations": (
        "Consistency checks cannot detect an incorrect but logically consistent report.",
        "逻辑校验无法识别仍然自洽的误报。",
    ),
    "initial": (
        "Strategy diagnostics will appear after the AI decides.",
        "AI 决策后显示真实策略指标。",
    ),
}


def text(key: str, language: str = "en", **kwargs) -> str:
    return STRINGS[key][1 if language == "zh" else 0].format(**kwargs)
