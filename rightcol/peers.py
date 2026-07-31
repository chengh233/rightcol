"""行业横切层 —— 给单个公司的数字提供**参照系**。

存在的理由只有一条：**单个公司的财务数字，脱离行业参照系几乎不携带信息。**

毛利率 70%，在软件业是中位数偏下，在食品零售业是不可能存在的数字。
同一个数字在两个行业里说的是完全不同的事。所以本项目坚持每个指标报三个数：

    公司值  ·  同业中位数  ·  公司在同业中的分位数（及其移动方向）

用中位数而不是均值 —— 均值会被龙头污染（把英伟达放进半导体的均值里，
其余每一家看起来都像垃圾）。

判读规则：**不看绝对值，看分位数是否 ≥70th，以及它在上行还是下行。**
一个从 80th 掉到 55th 的高毛利公司，比一个从 30th 升到 60th 的低毛利公司
危险得多 —— 前者的护城河在漏水，后者在改善。
"""

from __future__ import annotations

from dataclasses import dataclass

from . import edgar as E
from . import metrics as M


@dataclass
class PeerRow:
    ticker: str
    name: str
    end: str
    values: dict[str, float | None]
    error: str | None = None


# 横切时比较的指标。刻意**不含增长率之外的绝对规模** ——
# 规模大不等于生意好，把营收放进对标表只会诱导你用大小代替质地。
CROSS_METRICS = [
    ("gross_margin", "毛利率"),
    ("operating_margin", "营业利润率"),
    ("roic", "ROIC"),
    ("incremental_roic", "增量ROIC"),
    ("fcf_margin", "FCF利润率"),
    ("accrual", "应计比率"),
    ("ccc", "现金周期(天)"),
    ("capex_intensity", "资本开支强度"),
    ("net_debt_to_fcf", "净负债/FCF"),
    ("rev_cagr_5y", "营收CAGR(5y)"),
    ("sbc_of_gross_profit", "SBC/毛利"),
]


def _extract_row(ticker: str, years: int = 8) -> PeerRow:
    try:
        facts = E.company_facts(ticker)
    except Exception as e:
        return PeerRow(ticker, ticker, "", {}, error=str(e)[:120])

    ps = M.build_periods(facts, years=years)
    if not ps:
        return PeerRow(ticker, E.company_name(ticker), "", {}, error="无年度数据")

    p = ps[-1]
    prev = M.prev_of(ps, len(ps) - 1)
    mg = M.margins(p)
    cc = M.cash_conversion(p, prev)
    net_debt = M._sub(M.total_debt(p), M.excess_cash(p))

    return PeerRow(
        ticker=ticker,
        name=E.company_name(ticker),
        end=p.end,
        values={
            "gross_margin": mg["gross"],
            "operating_margin": mg["operating"],
            "roic": M.roic(p, prev),
            "incremental_roic": M.incremental_roic(ps),
            "fcf_margin": mg["fcf"],
            "accrual": M.accrual_ratio(p, prev),
            "ccc": cc["ccc"],
            "capex_intensity": mg["capex_intensity"],
            "net_debt_to_fcf": M._div(net_debt, M.fcf(p)),
            "rev_cagr_5y": (M.cagr([x.revenue for x in ps[-6:]], [x.end for x in ps[-6:]])
                            if len(ps) >= 6 else None),
            "sbc_of_gross_profit": mg["sbc_of_gross_profit"],
        },
    )


def _percentile(value: float | None, pool: list[float], higher_is_better: bool = True) -> float | None:
    """value 在 pool 中的分位数（0~100），用**中位秩**（mid-rank）。

    为什么不用朴素的「小于它的个数 / 总数」：那个算法两个方向不对称。
    以 pool=[0.1,0.2,0.3,0.4] 为例，朴素算法给
        越高越好 → [0, 25, 50, 75]      （冠军只有 75）
        越低越好 → [100, 75, 50, 25]    （冠军拿满 100）
    于是「越低越好」那一族指标会系统性显得更强，跨列比较分位数完全无效；
    而且「越高越好」的冠军永远拿不到 (n−1)/n×100 以上，n=4 时最高 75，
    **连文档反复强调的「≥70th」规则都够不到**。

    中位秩 pct = (小于它的个数 + 0.5×并列个数) / n，两个方向严格对称：
        [12.5, 37.5, 62.5, 87.5]  ↔  [87.5, 62.5, 37.5, 12.5]

    ⚠️ 样本量的天花板：n 家公司时冠军最高只能拿到 (1 − 0.5/n)×100 ——
    n=4 时 87.5，n=5 时 90。所以「≥70th」这条规则在小样本下要相应放宽。
    """
    if value is None or len(pool) < 3:
        return None
    n = len(pool)
    below = sum(1 for x in pool if x < value)
    equal = sum(1 for x in pool if x == value)
    pct = 100.0 * (below + 0.5 * equal) / n
    return pct if higher_is_better else 100.0 - pct


# 方向：True = 越高越好。CCC、应计、资本开支强度、净负债、SBC 占比越低越好。
HIGHER_IS_BETTER = {
    "gross_margin": True,
    "operating_margin": True,
    "roic": True,
    "incremental_roic": True,
    "fcf_margin": True,
    "accrual": False,
    "ccc": False,
    "capex_intensity": False,
    "net_debt_to_fcf": False,
    "rev_cagr_5y": True,
    "sbc_of_gross_profit": False,
}


def cross_section(tickers: list[str], years: int = 8) -> tuple[list[PeerRow], dict]:
    """拉取一组公司的横切数据，并算出每个指标的中位数与各家分位数。"""
    rows = [_extract_row(t, years) for t in tickers]
    ok = [r for r in rows if not r.error]

    stats: dict[str, dict] = {}
    for key, _label in CROSS_METRICS:
        pool = sorted(r.values[key] for r in ok if r.values.get(key) is not None)
        if not pool:
            stats[key] = {"median": None, "n": 0, "pct": {}}
            continue
        n = len(pool)
        median = pool[n // 2] if n % 2 else (pool[n // 2 - 1] + pool[n // 2]) / 2
        stats[key] = {
            "median": median,
            "n": n,
            "pct": {
                r.ticker: _percentile(r.values[key], pool, HIGHER_IS_BETTER[key])
                for r in ok
                if r.values.get(key) is not None
            },
        }
    return rows, stats
