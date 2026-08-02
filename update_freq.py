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
RECENT_N = 10          # 「直近◯回」作戦で見る抽選回数


def main():
    req = urllib.request.Request(CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as res:
        raw = res.read()
    text = raw.decode("shift_jis", errors="replace")

    freq = {str(n): 0 for n in range(1, 44)}
    draws = 0
    records = []          # (開催回, 日付, 本数字6個) を回順に貯める

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
        records.append((int(row[0]), row[1].strip(), nums))

    # データ源の異常（取得失敗・大幅減少）で壊れた集計を書き込まないための下限チェック
    if draws < 2000:
        print(f"ERROR: draws={draws} is suspiciously low; aborting without writing.")
        sys.exit(1)

    records.sort(key=lambda r: r[0])
    last_draw, last_date, _ = records[-1]

    # 直近10回だけの集計（アプリの「直近10回」作戦で使う）
    recent = records[-RECENT_N:]
    recent_freq = {str(n): 0 for n in range(1, 44)}
    for _, _, nums in recent:
        for n in nums:
            recent_freq[str(n)] += 1

    out = {
        "draws": draws,
        "lastDraw": last_draw,
        "lastDate": last_date,
        "freq": freq,
        "recentN": len(recent),
        "recentFreq": recent_freq,
        "recentFirstDraw": recent[0][0],
        "recentFirstDate": recent[0][1],
    }
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"OK: {draws} draws, last #{last_draw} ({last_date}) -> {OUT_PATH}")
    print(f"    recent {len(recent)}: #{recent[0][0]}({recent[0][1]}) - #{last_draw}({last_date})")


if __name__ == "__main__":
    main()
