#!/usr/bin/env python3
"""生成一家公司的确定性数据包。

    python bin/dossier.py AAPL              # 打印到 stdout
    python bin/dossier.py AAPL -o data/     # 写入 data/AAPL.md
    python bin/dossier.py AAPL --years 15

这一步**只产出数字**。拿到数据包之后，在 Claude Code 里跑 `/dossier AAPL`
做精读（读 10-K 原文、对照三个闸门下判断）——那一层走你的订阅，不花 API 钱。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rightcol import edgar as E  # noqa: E402
from rightcol import metrics as M  # noqa: E402
from rightcol import report as R  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="rightcol — 公司确定性数据包生成器")
    ap.add_argument("ticker", help="美股代码，如 AAPL")
    ap.add_argument("--years", type=int, default=10, help="回溯财年数（默认 10）")
    ap.add_argument("-o", "--out", help="输出目录；不给则打印到 stdout")
    ap.add_argument("--filings", action="store_true", help="附上最近 10-K 原文链接（精读层的入口）")
    ap.add_argument("--no-quarters", action="store_true", help="跳过季度视图（默认包含）")
    args = ap.parse_args()

    ticker = args.ticker.upper()
    try:
        facts = E.company_facts(ticker)
    except Exception as e:
        print(f"❌ {ticker}: {e}", file=sys.stderr)
        return 1

    periods = M.build_periods(facts, years=args.years)
    if not periods:
        print(f"❌ {ticker}: 取不到年度数据（可能从未提交过 10-K）", file=sys.stderr)
        return 1

    quarters = None if args.no_quarters else M.build_quarters(facts, n=12)
    # 检测「业绩发布已出、定期报告未到」的盲区窗口（财报季常见）
    pending = None
    if quarters:
        try:
            pending = E.stale_vs_earnings(ticker, quarters[-1].end)
        except Exception:
            pending = None
    text = R.data_pack(ticker, E.company_name(ticker), periods, quarters, pending)

    if args.filings:
        try:
            fl = E.filings(ticker, "10-K", limit=5)
            text += "\n## 八、10-K 原文（精读层入口）\n\n"
            for f in fl:
                text += f"- {f['filed']}（报告期 {f['period']}）— {f['url']}\n"
            text += (
                "\n数字之外，这些地方性价比最高：**风险因素的逐年 diff**（新增/删除了什么）、"
                "MD&A 里管理层对变化的解释、附注中的分部数据与客户集中度、"
                "以及会计政策变更。措辞的变化常常比财务指标更早反映问题。\n"
            )
        except Exception as e:  # 原文拿不到不该让整份数据包失败
            text += f"\n> ⚠️ 10-K 链接获取失败：{e}\n"

    if args.out:
        d = Path(args.out)
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{ticker}.md"
        p.write_text(text)
        print(f"✅ {p}  （{len(periods)} 个财年，最新止 {periods[-1].end}）")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
