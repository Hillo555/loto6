# -*- coding: utf-8 -*-
"""ロト6の全当選データを取得して、番号ごとの出現回数を freq.json に書き出す。

GitHub Actions から毎週月・木の抽選後に自動実行される。
手動で実行してもよい:  python update_freq.py
"""
import csv
import io
import json
import sys
import urllib.request

CSV_URL = "https://loto6.thekyo.jp/data/loto6.csv"
OUT_PATH = "freq.json"


def main():
    req = urllib.request.Request(CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as res:
        raw = res.read()
    text = raw.decode("shift_jis", errors="replace")

    freq = {str(n): 0 for n in range(1, 44)}
    draws = 0
    last_draw = 0
    last_date = ""

    reader = csv.reader(io.StringIO(text))
    next(reader)  # ヘッダー行
    for row in reader:
        if len(row) < 9 or not row[0].strip().isdigit():
            continue
        nums = []
        try:
            nums = [int(row[i]) for i in range(2, 8)]
        except ValueError:
            continue
        if any(n < 1 or n > 43 for n in nums):
            continue
        draws += 1
        for n in nums:
            freq[str(n)] += 1
        if int(row[0]) > last_draw:
            last_draw = int(row[0])
            last_date = row[1].strip()

    # データ源の異常（取得失敗・大幅減少）で壊れた集計を書き込まないための下限チェック
    if draws < 2000:
        print(f"ERROR: draws={draws} is suspiciously low; aborting without writing.")
        sys.exit(1)

    out = {
        "draws": draws,
        "lastDraw": last_draw,
        "lastDate": last_date,
        "freq": freq,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"OK: {draws} draws, last #{last_draw} ({last_date}) -> {OUT_PATH}")


if __name__ == "__main__":
    main()
