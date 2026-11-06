# CodeDuel 求解实验室

[English documentation](README.md)

需要 Python 3.11+ 和 Tkinter。在本目录运行 `python main.py`。
首页语言菜单可选 English 或简体中文；开始后保持所选语言。

选择 1–10 位，自己记住秘密数字，勿输入系统。提交猜测后，在右侧选择 AI 猜对的位数；矛盾或无法判定不会写入历史，可修正本轮反馈。5–10 位使用有界约束搜索，样本数不等于候选总数。仍然自洽的误报无法被识别。

三档 AI 都遵守全部历史，只计算同位置同数字。允许重复与前导零。

安装及测试：

```sh
python -m pip install -e ".[dev]"
python -m pytest -q
python -m tests.gui_smoke
```

详细算法、真实测试规模、局限及求职说明见英文 README。两个项目必须使用不同虚拟环境。
