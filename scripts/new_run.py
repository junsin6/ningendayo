#!/usr/bin/env python3
"""new_run.py — _workspace/{YYYY-MM-DD-NNN}/ を作成し入力テキストを 01_input.txt に保存する。

使い方:
    python scripts/new_run.py            # 空の run ディレクトリを作成し run_id を出力
    python scripts/new_run.py input.txt  # input.txt の内容を 01_input.txt として保存
    cat draft.txt | python scripts/new_run.py -   # 標準入力から保存

オーケストレーターはこのスクリプトで run_id を採番してからパイプラインを開始する。
"""
import sys
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT / "_workspace"


def next_run_id(today: str) -> str:
    """同日連番 NNN を採番して run_id を返す。"""
    WORKSPACE.mkdir(exist_ok=True)
    existing = [p.name for p in WORKSPACE.iterdir()
                if p.is_dir() and p.name.startswith(today)]
    nums = []
    for name in existing:
        tail = name.rsplit("-", 1)[-1]
        if tail.isdigit():
            nums.append(int(tail))
    nxt = (max(nums) + 1) if nums else 1
    return f"{today}-{nxt:03d}"


def read_input(arg: str | None) -> str:
    if arg is None:
        return ""
    if arg == "-":
        return sys.stdin.read()
    return Path(arg).read_text(encoding="utf-8")


def main() -> None:
    today = datetime.date.today().isoformat()  # YYYY-MM-DD
    run_id = next_run_id(today)
    run_dir = WORKSPACE / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    arg = sys.argv[1] if len(sys.argv) > 1 else None
    text = read_input(arg)
    (run_dir / "01_input.txt").write_text(text, encoding="utf-8")

    print(run_id)
    print(str(run_dir))


if __name__ == "__main__":
    main()
