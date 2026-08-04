#!/usr/bin/env python3
"""行业横切分析 —— 给单个公司的数字提供参照系。

    python bin/sector.py AAPL MSFT GOOGL META      # 直接给一组 ticker
    python bin/sector.py --group semis_fabless     # 用 sectors/groups.yml 里定义的组
    python bin/sector.py --group semis_fabless --stdout

默认写入 `data/sector_<组名>.md`（机器产物，可随时重跑覆盖）。
**认知档案请写在 `sectors/<组名>.md`** —— 那是不可再生的资产，两者刻意分开。

输出一张对标表：每个指标给出**公司值 / 同业中位数 / 分位数**。
判读规则见 FRAMEWORK.md §3 —— 不看绝对值，看分位数与它的移动方向。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rightcol import peers as P  # noqa: E402

GROUPS_PATH = Path(__file__).resolve().parent.parent / "sectors" / "groups.yml"

PCT_FMT = {"gross_margin", "operating_margin", "roic", "incremental_roic", "fcf_margin",
           "accrual", "capex_intensity", "rev_cagr_5y", "sbc_of_gross_profit"}


def _fmt(key: str, v: float | None) -> str:
    if v is None:
        return "—"
    if key in PCT_FMT:
        return f"{v * 100:.1f}%"
    if key == "ccc":
        return f"{v:.0f}"
    return f"{v:.2f}×"


def load_group(name: str) -> list[str]:
    if not GROUPS_PATH.exists():
        raise SystemExit(f"没有 {GROUPS_PATH}；请直接传 ticker 列表，或先创建该文件。")
    import yaml

    groups = yaml.safe_load(GROUPS_PATH.read_text()) or {}
    if name not in groups:
        raise SystemExit(f"组 {name!r} 未定义。已有：{sorted(groups)}")
    g = groups[name]
    return g["tickers"] if isinstance(g, dict) else list(g)


def main() -> int:
    ap = argparse.ArgumentParser(description="rightcol — 行业横切分析")
    ap.add_argument("tickers", nargs="*", help="美股代码列表")
    ap.add_argument("--group", help="使用 sectors/groups.yml 中定义的组")
    ap.add_argument("--years", type=int, default=8)
    ap.add_argument("-o", "--out", default=None,
                    help="输出目录（默认 data/）。机器产物写成 sector_<组名>.md，"
                         "刻意与 sectors/<组名>.md 分开——后者是你手写的行业认知，不可再生")
    ap.add_argument("--stdout", action="store_true", help="打印到 stdout 而不写文件")
    ap.add_argument("--basis", choices=["ttm", "annual"], default="ttm",
                    help="口径：ttm=最近四季合计（默认，跨公司可比）；annual=最新完整财年")
    args = ap.parse_args()

    tickers = [t.upper() for t in args.tickers] or (load_group(args.group) if args.group else [])
    if len(tickers) < 3:
        raise SystemExit("至少需要 3 家公司才有参照系意义（中位数与分位数都需要样本）。")

    rows, stats = P.cross_section(tickers, years=args.years, basis=args.basis)
    ok = [r for r in rows if not r.error]

    L: list[str] = []
    title = args.group or "+".join(t.ticker for t in ok[:4])
    L.append(f"# 行业横切 — {title}")
    L.append("")
    if args.basis == "ttm":
        L.append(f"样本 {len(ok)}/{len(tickers)} 家 · **口径：TTM（最近四个季度合计）**")
        L.append("")
        L.append("> 为什么用 TTM 而不是最新财年：各公司财年不同，「最新财年」根本不是同一段时间。")
        L.append("> 实测 15 家样本**年报期末跨度 368 天**，而最新季末跨度只有 **94 天**。")
        L.append("> 差别有多大：SanDisk 年报口径 ROIC −10.4%，TTM 口径 **+42.0%**。")
        L.append("> （增量 ROIC 与营收 CAGR 需要多年序列，仍用年报口径。）")
    else:
        L.append(f"样本 {len(ok)}/{len(tickers)} 家 · 口径：最新完整财年（⚠️ **财年止日期不同，见下表**）")
    L.append("")
    L.append("> 判读规则（FRAMEWORK.md §3）：**不看绝对值，看分位数是否 ≥70th，")
    L.append("> 以及它在上行还是下行。** 中位数而非均值——均值会被龙头污染。")
    L.append("")

    L.append(f"| 公司 | {'TTM止' if args.basis=='ttm' else '财年止'} |" + "".join(f" {lab} |" for _k, lab in P.CROSS_METRICS))
    L.append("|" + "---|" * (2 + len(P.CROSS_METRICS)))
    for r in ok:
        cells = []
        for k, _lab in P.CROSS_METRICS:
            v = _fmt(k, r.values.get(k))
            pct = stats[k]["pct"].get(r.ticker)
            cells.append(f"{v}" + (f" _({pct:.0f})_" if pct is not None else ""))
        L.append(f"| **{r.ticker}** | {r.end} |" + "".join(f" {c} |" for c in cells))

    med = []
    for k, _lab in P.CROSS_METRICS:
        med.append(_fmt(k, stats[k]["median"]))
    L.append("| _中位数_ | — |" + "".join(f" _{m}_ |" for m in med))
    L.append("")
    L.append("_括号内为该公司在样本中的分位数（0~100，已按指标方向校正：越高越好）。_")
    L.append("")

    bad = [r for r in rows if r.error]
    if bad:
        L.append("## 取数失败")
        L.append("")
        for r in bad:
            L.append(f"- **{r.ticker}** — {r.error}")
        L.append("")
        L.append("金融机构在通用科目上会结构性缺失（无毛利/存货/资本开支），")
        L.append("这不是数据问题，是生意结构不同——见 FRAMEWORK.md §10。")
        L.append("")

    L.append("## ⚠️ 可比性检查（读表前必看）")
    L.append("")
    if args.basis == "ttm":
        L.append("- **TTM 仍有残余错位**：各家季末日期最多相差约 3 个月（上表已列出）。")
        L.append("  这比年报口径的近一年好得多，但在急剧变化期仍需注意。")
        L.append("- **存量项取最新季末**：资产负债表类指标（净负债、存货）用的是时点值，")
        L.append("  与四季合计的流量项在时间上并不完全对齐——这是 TTM 口径固有的取舍。")
    else:
        L.append("- 🔴 **财年不对齐**：各家财年止日期最多相差 **368 天**（实测）。")
        L.append("  跨公司比同一「最新财年」实际可能相差近一年——**建议改用 --basis ttm**。")
    L.append("- **业务混合**：多元化公司的合并数字会掩盖各块生意的差异；")
    L.append("  companyfacts 拿不到分部数据，需回 10-K 原文。")
    L.append("- **会计口径**：租赁资本化、研发资本化、并购摊销在同业间可能不同。")
    L.append("- **样本选择**：这组同行是你选的。**选错同行，整张表都是错的参照系。**")
    L.append("")

    text = "\n".join(L)
    if args.stdout:
        print(text)
        return 0

    # ⚠️ 文件名带 sector_ 前缀且默认落在 data/。
    # 认知档案在 sectors/<组名>.md —— 那是你手写的、不可再生的资产；
    # 这里是可随时重跑的机器产物。两者混在同一路径会互相覆盖。
    # 用 __file__ 解析，与 CACHE_DIR / GROUPS_PATH 保持一致 ——
    # 否则从仓库外运行会静默在别处建 data/，仓库里的报告永远不更新。
    d = Path(args.out) if args.out else Path(__file__).resolve().parent.parent / "data"
    d.mkdir(parents=True, exist_ok=True)
    # 位置参数（无 --group）时用 ticker 拼名，避免不同的 ad-hoc 同业组互相静默覆盖
    stem = args.group or "-".join(r.ticker for r in ok)
    p = d / f"sector_{stem}.md"
    p.write_text(text)
    print(f"✅ {p}  （{len(ok)}/{len(tickers)} 家）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
