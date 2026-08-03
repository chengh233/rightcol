#!/usr/bin/env python3
"""闸门 2 —— 逆向 DCF：当前价格在假设什么？

    python bin/value.py AAPL --price 255
    python bin/value.py AAPL --market-cap 3800e9 --rate 0.10
    python bin/value.py COST --price 900 --years 10 --terminal 0.025

**为什么要手动输入价格**：本项目坚持零密钥、零付费依赖，而 SEC EDGAR
不含股价。手动输入还有一个好处 —— 它强迫你意识到「价格是你选的输入」，
而不是一个从系统里自动流出来、看起来客观的东西。

输出不是「它值多少」，而是一个**可证伪的命题**：
「这个价格要求它未来 N 年自由现金流年化增长 X%」。
X 合不合理，你拿它的历史增速、行业天花板、竞争格局去检验 —— 那才是认知。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rightcol import edgar as E  # noqa: E402
from rightcol import metrics as M  # noqa: E402
from rightcol import valuation as V  # noqa: E402


def _b(x: float | None) -> str:
    return "—" if x is None else f"{x / 1e9:,.1f}B"


def main() -> int:
    ap = argparse.ArgumentParser(description="rightcol — 逆向 DCF：价格在假设什么")
    ap.add_argument("ticker")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--price", type=float, help="每股价格（配合最新申报股本换算市值）")
    g.add_argument("--market-cap", type=float, help="直接给市值（美元）")
    ap.add_argument("--rate", type=float, default=0.09, help="折现率，默认 0.09")
    ap.add_argument("--terminal", type=float, default=0.025, help="永续增长率，默认 0.025")
    ap.add_argument("--years", type=int, default=10, help="显式预测期，默认 10")
    ap.add_argument("--fcf-years", type=int, default=3, help="起点 FCF 取近几年平均，默认 3")
    args = ap.parse_args()
    if args.fcf_years < 1:
        ap.error("--fcf-years 必须 ≥ 1（0 会退化成取整个序列平均）")

    ticker = args.ticker.upper()
    try:
        facts = E.company_facts(ticker)
    except Exception as e:
        print(f"❌ {ticker}: {e}", file=sys.stderr)
        return 1
    ps = M.build_periods(facts, years=12)
    if not ps:
        print(f"❌ {ticker}: 无年度数据", file=sys.stderr)
        return 1

    last = ps[-1]
    info = E.entity_info(ticker)

    # 市值
    if args.market_cap:
        mcap = args.market_cap
        shares_note = "（直接给定市值）"
    else:
        shares = last.shares_outstanding
        proxy = False
        if not shares:
            shares, proxy = last.shares_diluted, True
        if not shares:
            print(f"❌ {ticker}: 取不到股本，请改用 --market-cap", file=sys.stderr)
            return 1
        mcap = args.price * shares
        shares_note = f"（{shares / 1e9:.3f}B 股 × ${args.price:,.2f}，股本取自最新申报，未做拆股追溯调整）"
        if proxy:
            # ⚠️ 退而求其次用了**加权平均摊薄股数**，它不是时点股本。
            # 对当年 IPO、增发频繁、或多重股权结构（A/B/C 类分别申报）的公司，
            # 这个数会显著低估当前股本，从而低估市值与企业价值。
            shares_note += "\n  ⚠️ **股本用的是「加权平均摊薄股数」代理，不是时点值** ——"
            shares_note += "\n     该公司未申报 CommonStockSharesOutstanding（常见于当年 IPO 或多重股权结构）。"
            shares_note += "\n     若公司年内 IPO/增发，此值会**显著低估**真实股本与市值，请改用 --market-cap。"

    # 企业价值：先扣净现金 —— 这是段永平算苹果时做的第一件事
    net_cash = M._sub(M.excess_cash(last), M.total_debt(last))
    ev = mcap - (net_cash or 0)

    # 起点 FCF：近 N 年平均，避免周期高点/低点失真
    tail = ps[-args.fcf_years :]
    fcfs = [M.fcf(p) for p in tail if M.fcf(p) is not None]
    fcfs_ex = [M.fcf_ex_sbc(p) for p in tail if M.fcf_ex_sbc(p) is not None]
    fcf0 = sum(fcfs) / len(fcfs) if fcfs else None
    fcf0_ex = sum(fcfs_ex) / len(fcfs_ex) if fcfs_ex else None

    # TTM 口径：年报可能已过期一年，对周期股这是致命的
    qs = M.build_quarters(facts, n=12)
    ttm_fcf = M.ttm_fcf(qs)
    stale = M.staleness_days(last.end, qs[-1].end if qs else None)

    a = V.DCFAssumptions(discount_rate=args.rate, terminal_growth=args.terminal, years=args.years)
    warns = a.check()
    if warns:
        for w in warns:
            print(f"❌ 假设不合法：{w}", file=sys.stderr)
        return 1

    print(f"# {info['name']} ({ticker}) — 逆向 DCF")
    print(f"\nCIK {info['cik']} · 最新财年止 {last.end} · 数据源 SEC EDGAR XBRL\n")
    print("## 输入（每一项都是**你的选择**，不是客观事实）\n")
    print(f"- 市值　　　　　{_b(mcap)}  {shares_note}")
    print(f"- 净现金　　　　{_b(net_cash)}  （超额现金 {_b(M.excess_cash(last))} − 有息负债 {_b(M.total_debt(last))}）")
    print(f"- **企业价值**　{_b(ev)}  ← 逆向 DCF 的目标值")
    print(f"- 起点 FCF　　　{_b(fcf0)}  （近 {len(fcfs)} 年平均）")
    print(f"- 起点 FCF(扣SBC){_b(fcf0_ex)}  （近 {len(fcfs_ex)} 年平均）")
    if ttm_fcf is not None:
        print(f"- **TTM FCF**　　{_b(ttm_fcf)}  （最近四季，截至 {qs[-1].end}）")
    if stale and stale >= 180:
        print(f"\n  🔴 **年报视图已过期 {stale} 天**（财年止 {last.end}，最新季末 {qs[-1].end}）。")
        print(f"     近 {args.fcf_years} 年平均是**跨周期口径**，TTM 是**当下口径**——")
        print(f"     两者差距越大，说明这家公司正处在周期的陡峭段，任何单一起点都会误导。")
    print(f"- 折现率 r　　　{args.rate:.1%}　永续增长 g_t {args.terminal:.1%}　显式期 {args.years} 年\n")

    print("## 结论 —— 一个可证伪的命题\n")
    bases = [("FCF（近%d年均）" % args.fcf_years, fcf0), ("FCF(扣SBC)", fcf0_ex)]
    if ttm_fcf is not None:
        bases.append(("FCF（TTM 当下口径）", ttm_fcf))
    for label, base in bases:
        if base is None or base <= 0:
            print(f"- **{label}**：起点为负或缺失 → DCF 不适用。")
            print("  （自由现金流为负时应改用单位经济模型 / 路径到盈利，见 FRAMEWORK.md §10）")
            continue
        g = V.implied_growth(ev, base, a)
        if g is None:
            print(f"- **{label}**：在 −50%~+100% 的增长区间内无解 —— 价格已脱离该模型能表达的范围。")
            continue
        tv = V.terminal_value_share(base, g, a)
        print(f"- **{label}**：当前价格要求它未来 {args.years} 年自由现金流年化增长 "
              f"**{g:.1%}**，之后永续 {args.terminal:.1%}。")
        print(f"  终值占总现值 **{tv:.0%}** —— 结论主要由「{args.years} 年以后」决定，这是最不可知的部分。")

    # 历史增速，用来检验隐含增长率合不合理
    hist_fcf = [M.fcf(p) for p in ps]
    for n in (5, 10):
        if len(ps) > n:
            win = ps[-(n + 1) :]
            ends = [p.end for p in win]
            # 窗口内若有业务重组/分拆，跨越它的 CAGR 毫无意义
            broken = any(p.structural_break for p in win[1:])
            c = None if broken else M.cagr(hist_fcf[-(n + 1) :], ends)
            rc = None if broken else M.cagr([p.revenue for p in win], ends)
            tail = "（窗口内存在业务重组/分拆，跨期增速无意义）" if broken else ""
            print(f"\n- 参照：过去 {n} 年 FCF CAGR {f'{c:.1%}' if c else '—'}　"
                  f"营收 CAGR {f'{rc:.1%}' if rc else '—'}{tail}")

    print("\n## 敏感性 —— 为什么不该相信任何一个精确目标价\n")
    if fcf0 and fcf0 > 0:
        # 只保留合法折现率：r 必须严格大于永续增长率，否则 Gordon 模型发散。
        # 不过滤的话，--rate 0.055 --terminal 0.045 会在打印到一半时抛异常。
        rates = [r for r in (args.rate - 0.01, args.rate, args.rate + 0.01) if r > args.terminal + 1e-9]
        print("| 给定增长率 \\ 折现率 |" + "".join(f" {r:.1%} |" for r in rates))
        print("|" + "---|" * (1 + len(rates)))
        drops: list[float] = []
        for gg in (0.03, 0.06, 0.09, 0.12):
            vals = []
            for r in rates:
                aa = V.DCFAssumptions(discount_rate=r, terminal_growth=args.terminal, years=args.years)
                vals.append(V.pv_of_growing_fcf(fcf0, gg, aa))
            print(f"| g={gg:.0%} 时的企业价值 |" + "".join(f" {_b(v)} |" for v in vals))
            if len(vals) >= 2:
                drops.append((vals[-2] - vals[-1]) / vals[-2])
        if drops:
            # 动态算，不写死。曾经硬编码「动 20~30%」，而实测只有 13~16% ——
            # 一句被自己表格证伪的断言，比没有这句话更糟。
            print(f"\n折现率上行 1 个百分点，上表估值下移 **{min(drops):.0%}~{max(drops):.0%}**"
                  f"（现金流越靠后跌得越多）。**这就是不该相信任何精确目标价的原因。**")

    print("\n---\n")
    print("**接下来该问的不是「它值多少」，而是：上面那个隐含增长率，我信不信？**")
    print("拿它的历史增速（上面已给）、行业天花板、竞争格局去检验。")
    print(f"另外别忘了看当前 10 年期美债收益率 —— 折现率的地基由宏观决定（见 macroscope）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
