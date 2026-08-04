"""指标计算层 —— 把申报数字变成**可比较的**指标。

设计原则（三条，都是为了不自欺）：

1. **绝不用 0 填充缺失。** 拿不到就是 `None`，一路传到报告里显示"—"。
   把缺失当 0 会造出"零负债""零资本开支"这类致命的假象。

2. **口径必须留痕。** 每个指标都记录它用了哪个标签、哪个期间、平均还是期末。
   跨公司比较时，你必须知道自己在比什么。

3. **只算，不判断。** 这里没有"好/坏"。阈值和判断在 FRAMEWORK.md 里，
   由人来下 —— 因为同一个数字在不同生意里含义完全相反。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import concepts as C
from .edgar import Fact, annual_series


def _div(a: float | None, b: float | None) -> float | None:
    """安全除法。分母为 0 或任一方缺失都返回 None —— 不返回 0，不返回 inf。"""
    if a is None or b is None or b == 0:
        return None
    return a / b


def _sub(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else a - b


def _add(*xs: float | None) -> float | None:
    """相加。全缺失返回 None；部分缺失按 0 计但这是**有意**的 —— 用于
    「有息负债 = 长期 + 短期 + 租赁」这类分项，某一项没申报通常真的代表没有。"""
    vals = [x for x in xs if x is not None]
    return sum(vals) if vals else None


@dataclass
class Period:
    """一个财年的全部原始科目（已按概念名归一）。"""

    end: str
    fy: int | None
    raw: dict[str, float | None] = field(default_factory=dict)
    tags_used: dict[str, str] = field(default_factory=dict)

    gap_before: bool = False
    """与上一个 Period 之间存在**缺失年份**。为 True 时 YoY、期初期末平均
    这类跨期指标全部不可信，报告必须显示「—」并注明。

    这不是理论问题：实测美国运通的营收标签只覆盖 2008–2010 与 2016–2025，
    中间 2011–2015 完全缺失。若不检测，2010 与 2016 会被排成相邻两行，
    报告打印出「营收 YoY −12.9%」—— 那实际是相隔 2192 天的变化，
    而 ROIC / ROE / 应计比率用的是「2016 年与 2010 年的平均资产」。"""

    structural_break: bool = False
    """营收同比出现 **±80% 以上**的剧变 —— 需人工确认是不是业务重组/分拆。

    `gap_before` 只能发现**缺失年份**，发现不了**业务换了**。实测 Nebius
    （前身 Yandex N.V.）2022 年营收从 47.9 亿掉到 0.1 亿（−99.7%），
    那不是经营崩溃，是剥离了俄罗斯业务 —— 剥离前后的财务序列**毫无可比性**，
    任何跨越该年的 CAGR、趋势、平均值都是无意义的。

    ⚠️ 这只是**提示**不是判定：高增长公司也会有 +700% 的同比
    （实测 CoreWeave 2024 年 +736%，那是真实增长）。看到标记要回原文确认。"""

    balance_ok: bool | None = None
    """会计恒等式 资产 == 负债+权益 是否成立。False 说明这一年的资产负债表
    科目来自**不同申报期**（各标签独立取 filed 最新所致），拼出来的是一张
    现实中不存在的报表 —— 周转率、权益乘数、应计比率、ROIC 全部受影响。"""

    def __getattr__(self, k: str):
        if k.startswith("_"):
            raise AttributeError(k)
        return self.raw.get(k)


def build_periods(facts: dict, years: int = 12) -> list[Period]:
    """把 companyfacts 拍平成按财年排列的 Period 列表（最新在最后）。"""
    series: dict[str, dict[str, Fact]] = {}
    for name, (kind, tags) in C.CONCEPTS.items():
        series[name] = annual_series(
            facts, tags, kind=kind, strict_priority=name in C.STRICT_PRIORITY
        )

    # 以营收（或总资产，金融股无营收标签时）的期末日期作为财年主轴
    axis = sorted(series.get("revenue") or series.get("assets") or {})[-years:]

    out: list[Period] = []
    for end in axis:
        p = Period(end=end, fy=None)
        for name, s in series.items():
            f = s.get(end)
            if f is None and C.CONCEPTS[name][0] == C.STOCK:
                # 资产负债表时点日可能与利润表期末差几天（财年切换、并购），
                # 允许 ±7 天对齐，超出就认缺失而不是硬凑。
                from datetime import date

                target = date.fromisoformat(end)
                for k, cand in s.items():
                    if abs((date.fromisoformat(k) - target).days) <= 7:
                        f = cand
                        break
            if f is not None:
                p.raw[name] = f.val
                p.tags_used[name] = f.tag
                if p.fy is None:
                    p.fy = f.fy
        out.append(p)

    # 期间连续性：相邻财年间隔 > 400 天 = 中间有缺失年份，打断点标记
    from datetime import date as _date

    for i in range(1, len(out)):
        gap = (_date.fromisoformat(out[i].end) - _date.fromisoformat(out[i - 1].end)).days
        if gap > 400:
            out[i].gap_before = True

    # 业务结构性断裂：营收同比剧变，提示可能是重组/分拆而非经营变化
    for i in range(1, len(out)):
        a, b = out[i - 1].revenue, out[i].revenue
        if a and b and a > 0:
            if abs(b / a - 1) >= 0.80:
                out[i].structural_break = True

    # 会计恒等式护栏 —— 定义了就要真的用上
    for p in out:
        p.balance_ok = balance_check(p)

    return out


# --------------------------------------------------------------------------
# 派生量
# --------------------------------------------------------------------------


def build_quarters(facts: dict, n: int = 12) -> list[Period]:
    """拍平成按季度排列的 Period 列表（最新在最后），并倒推补上每个 Q4。

    **为什么周期股必须看季度**：年报最多有一年时滞。实测 Micron ——
    最新年报止 2025-08-28，而 2026-08 的价格反映的是随后四个季度的爆发
    （营收从 93 亿/季涨到 415 亿/季，毛利率从 37.7% 涨到 84.6%）。
    只看年报会把它读成一家平庸公司，而市场在给它定 9000 亿市值。

    存量项（资产负债表）用最近的季末时点值。
    """
    from .edgar import annual_series, derive_q4, quarterly_series

    series: dict[str, dict] = {}
    for name, (kind, tags) in C.CONCEPTS.items():
        strict = name in C.STRICT_PRIORITY
        is_avg = name in C.PERIOD_AVERAGE
        # 期间平均值（加权平均股数）**不能做任何还原** —— 相加相减都是数学错误。
        # 实测苹果被 YTD 差分出「−0.05B 股」，再四季相加得到 44.20B（实际约 14.7B）。
        q = quarterly_series(facts, tags, kind=kind, strict_priority=strict, derive=not is_avg)
        if kind == C.FLOW and not is_avg:
            a = annual_series(facts, tags, kind=kind, strict_priority=strict)
            q = derive_q4(q, a)
        series[name] = q

    # ⚠️ 季度轴**不能死盯 revenue**。银行没有可用的季度营收标签（实测摩根大通
    # 的季度轴会停在 2014 年，因为主标签 `Revenues` 只有旧数据），此时轴必须
    # 落到别的概念上。规则：在几个候选里取**最新一期最靠后**的那个。
    axis_src, axis_end = None, ""
    for cand in ("revenue", "net_income", "ocf"):
        s = series.get(cand) or {}
        if s and max(s) > axis_end:
            axis_src, axis_end = cand, max(s)
    axis = sorted(series.get(axis_src) or {})[-n:]

    out: list[Period] = []
    for end in axis:
        p = Period(end=end, fy=None)
        for name, s in series.items():
            f = s.get(end)
            if f is None and C.CONCEPTS[name][0] == C.STOCK:
                from datetime import date as _d

                target = _d.fromisoformat(end)
                cands = [(abs((_d.fromisoformat(k) - target).days), k) for k in s]
                cands = [c for c in cands if c[0] <= 7]
                if cands:
                    f = s[min(cands)[1]]
            if f is not None:
                p.raw[name] = f.val
                p.tags_used[name] = f.tag
                if p.fy is None:
                    p.fy = f.fy
        out.append(p)
    return out


def ttm_period(qs: list[Period], offset: int = 0) -> Period | None:
    """把最近四个季度合成一个「**TTM 期**」，让所有年度指标函数直接可用。

    - **流量项**（利润表、现金流量表）：最近四季**求和**
    - **存量项**（资产负债表）：取**最新季末**的时点值

    合成出来的对象和 `build_periods()` 产出的 Period 完全同构，
    所以 `margins()` / `roic()` / `total_debt()` / `cash_conversion()`
    这些函数不用改就能在 TTM 口径上跑。

    **为什么这件事很重要**：各公司财年不同，"最新财年"根本不是同一段时间。
    实测 15 家样本：**年报期末跨度 368 天**（SanDisk 止 2025-06 vs 微软止 2026-06），
    把它们放同一张表里比 ROIC 和毛利率，等于拿 2025 年中的公司和 2026 年中的公司比。
    改用 TTM 后，**最新季末的跨度只有 94 天** —— 可比性提升近 4 倍。

    `offset=4` 取"四个季度前的那个 TTM 期"，用于算平均投入资本与同比。

    返回 None 表示季度不足或存在缺口 —— **拼错的 TTM 比没有 TTM 更危险**。
    """
    from datetime import date

    from .edgar import QUARTER_MAX_DAYS, QUARTER_MIN_DAYS

    end_i = len(qs) - 1 - offset
    if end_i < 3:
        return None
    win = qs[end_i - 3 : end_i + 1]
    for a, b in zip(win, win[1:]):
        gap = (date.fromisoformat(b.end) - date.fromisoformat(a.end)).days
        if not (QUARTER_MIN_DAYS <= gap <= QUARTER_MAX_DAYS):
            return None

    last = win[-1]
    out = Period(end=last.end, fy=last.fy)
    for name, (kind, _tags) in C.CONCEPTS.items():
        if name in C.PERIOD_AVERAGE:
            # 加权平均股数这类**期间平均值**：既不能相加也不能相减。
            # 而且我们要的本来就是「当前股本」，所以取最近一个有值的季度。
            for q in reversed(win):
                if q.raw.get(name) is not None:
                    out.raw[name] = q.raw[name]
                    out.tags_used[name] = q.tags_used.get(name, "") + f"(取{q.end}单季)"
                    break
        elif kind == C.FLOW:
            vals = [q.raw.get(name) for q in win]
            if all(v is not None for v in vals):
                out.raw[name] = sum(vals)
                out.tags_used[name] = last.tags_used.get(name, "") + "(TTM四季合计)"
        else:  # 存量项用最新季末的时点值
            if last.raw.get(name) is not None:
                out.raw[name] = last.raw[name]
                out.tags_used[name] = last.tags_used.get(name, "")
    out.balance_ok = balance_check(out)
    return out


def ttm(qs: list[Period], concept: str) -> float | None:
    """最近四个季度的合计（Trailing Twelve Months）。

    不足四季、或四季之间存在缺口（相邻季末间隔超过 100 天）时返回 None ——
    **拼错的 TTM 比没有 TTM 更危险**，它看起来是个正常数字。
    """
    from datetime import date

    if len(qs) < 4:
        return None
    last4 = qs[-4:]
    for a, b in zip(last4, last4[1:]):
        from .edgar import QUARTER_MAX_DAYS, QUARTER_MIN_DAYS

        gap = (date.fromisoformat(b.end) - date.fromisoformat(a.end)).days
        if not (QUARTER_MIN_DAYS <= gap <= QUARTER_MAX_DAYS):
            return None
    vals = [q.raw.get(concept) for q in last4]
    return None if any(v is None for v in vals) else sum(vals)


def ttm_fcf(qs: list[Period]) -> float | None:
    o, c = ttm(qs, "ocf"), ttm(qs, "capex")
    return None if o is None or c is None else o - abs(c)


def staleness_days(annual_end: str, quarter_end: str | None) -> int | None:
    """最新季末比最新财年末新多少天 —— 用来判断年报视图有多陈旧。"""
    from datetime import date

    if not quarter_end:
        return None
    return (date.fromisoformat(quarter_end) - date.fromisoformat(annual_end)).days


def prev_of(ps: list[Period], i: int) -> Period | None:
    """取 ps[i] 的上一期，**跨缺失年份时返回 None**。

    所有需要「期初期末平均」或「同比」的地方都必须走这个函数。
    曾经只在报告第一节做了这个判断，结果同一份报告对美国运通 2016 年
    打印出两个不同的 ROE（第一节 26.2%、第二节 27.3%）—— 后者用的是
    2016 与 2010 的平均权益，跨了 6 年却没有任何提示。
    """
    return ps[i - 1] if (i and not ps[i].gap_before) else None


def total_debt(p: Period, include_leases: bool = True) -> float | None:
    """有息负债 = 非流动长期负债 + 流动有息负债（+ 经营租赁负债）。

    ⚠️ **不能用标签回退链取这个数**，两个陷阱都会静默算错：

    陷阱一 —— 重复计算。`LongTermDebt` 的定义已包含当期部分，把它与
      `DebtCurrent` 相加会把长期负债的当期部分算两遍。实测百事
      (PEP@2025-12-27)：LongTermDebt 46.351B、LongTermDebtNoncurrent 42.321B、
      DebtCurrent 6.861B —— 朴素相加得 53.21B，真实值 49.18B，虚增 8.2%。

    陷阱二 —— 漏项。短期有息负债有多个并列科目，回退链只会取到第一个。
      苹果同时申报 `LongTermDebtCurrent` 与 `CommercialPaper`，回退链会
      静默漏掉商业票据。

    所以这里显式分层组装，并对每一层留出降级路径。

    含租赁的理由：ASC 842 之后经营租赁上表，经济实质就是借钱占用资产。
    对零售 / 餐饮 / 航空这类"租来的重资产"生意，不算租赁会系统性低估杠杆。
    """
    # 最高优先：长短期合计的总额标签。它**已含**当期部分，所以一旦命中就
    # 独占使用，绝不再与 DebtCurrent 等分项相加（否则又是一次重复计算）。
    # 实测甲骨文只申报这一个标签，不覆盖它会漏掉约 1220 亿美元长期负债。
    if p.debt_combined_total is not None:
        total = p.debt_combined_total
        if include_leases:
            total = _add(total, p.lease_liab_long, p.lease_liab_short)
        return total

    # 非流动段：优先直接取；否则用 总长期负债 − 当期部分 倒推
    noncurrent = p.debt_lt_noncurrent
    if noncurrent is None and p.debt_lt_total is not None:
        noncurrent = p.debt_lt_total - (p.debt_lt_current or 0)

    # 流动段：DebtCurrent 已是"短期借款 + 长期负债当期部分"的合计，优先用它；
    # 缺失时才把分项相加（不是回退！）——但相加前必须去重。
    #
    # ⚠️ 同一行资产负债表科目可能被打上多个标签。实测 AMD FY2025：
    #    LongTermDebtCurrent = ShortTermBorrowings = 874,000,000（同一 accession、
    #    同一金额，就是同一条科目的重复打标）。盲目相加会把它算两遍，
    #    有息负债虚增 21.8%，并静默传导到 ROIC 与净负债。
    # 处理：数值完全相同的分项只计一次。
    current = p.debt_current_total
    if current is None:
        parts = [p.debt_lt_current, p.short_term_borrowings, p.commercial_paper]
        seen: list[float] = []
        for v in parts:
            if v is None or any(abs(v - s) < 1.0 for s in seen):
                continue
            seen.append(v)
        current = sum(seen) if seen else None

    total = _add(noncurrent, current)
    if include_leases:
        total = _add(total, p.lease_liab_long, p.lease_liab_short)
    return total


def excess_cash(p: Period) -> float | None:
    """超额现金 = 现金及等价物 + 短期有价证券 + **长期有价证券**。

    ⚠️ 第三项经常被漏掉，而它可能是最大的一块。实测苹果 FY2019：
    现金及等价物只有 488 亿，但 `MarketableSecuritiesNoncurrent` 高达 1053 亿。
    只算"现金 + 短期投资"会漏掉约千亿美元 —— 直接击穿"扣掉净现金后
    这家公司到底多贵"这条核心推理（段永平买苹果的算法正是先扣净现金）。

    长期有价证券本质是一个债券组合，不参与经营，理应从投入资本中剔除。

    ⚠️ **不能把「按流动性拆分的标签」和「整体合计标签」相加** —— 那会把流动
    那段算两遍。实测英伟达 FY2015 曾因此算出「超额现金 9.04B」，而它当年总资产
    只有 7.20B。所以这里的规则是：**只要任一条拆分链命中，就只用拆分口径；
    两条都落空时，才用合计标签，且只用一次。**

    最后还有一道硬护栏：超额现金不可能超过总资产。越界返回 None 而不是
    一个荒谬但不报错的数 —— 数据出问题必须长得像出问题。

    简化之处（诚实声明）：真正的「超额」还应扣掉经营所需的最低现金
    （通常按营收 1~2% 估），这里不做，因此对现金极多的公司 ROIC 略偏乐观。
    """
    split = _add(p.short_term_investments, p.long_term_investments)
    securities = split if split is not None else p.total_investments
    total = _add(p.cash, securities)
    if total is not None and p.assets is not None and total > p.assets:
        return None  # 不可能：现金类资产多于总资产 → 口径出错，拒绝输出
    return total


def effective_tax_rate(p: Period) -> float | None:
    """有效税率 = 所得税费用 / 税前利润。异常时返回 None。

    ⚠️ **必须先要求税前利润为正**。亏损年份税前为负、所得税收益也为负，
    两个负数相除得到一个**正的、看起来很正常的比值**，会被静默当成税率
    拿去算 NOPAT。实测埃克森美孚 2020 年（税前 −28.88B / 税额 −5.63B
    → 19.5%）、伯克希尔 2022 年（27.9%）都会命中这个陷阱。
    """
    if p.pretax_income is None or p.pretax_income <= 0:
        return None
    r = _div(p.tax_expense, p.pretax_income)
    if r is None or not (0 <= r <= 0.6):
        return None
    return r


LEASE_IMPLIED_RATE = 0.05
"""把经营租赁负债视作有息负债时，用于还原利息部分的隐含折现率。
5% 是 ASC 842 披露的加权平均折现率在美股大盘股中的常见量级。"""


def nopat(p: Period, fallback_rate: float = 0.21, capitalize_leases: bool = True) -> float | None:
    """税后经营利润 = 调整后 EBIT × (1 − 有效税率)。

    **口径一致性（这一条最容易被做错，且错了不会报错）**：
    如果把经营租赁负债算进投入资本（分母），就必须把租赁成本里的**利息部分**
    加回经营利润（分子）—— 否则等于「按借钱买资产计算占用的资本，却按
    租金全额扣减利润」，会系统性**低估**零售 / 餐饮 / 航空的 ROIC。

    这正是 ASC 842 与 IFRS 16 的关键差异：US GAAP 下经营租赁保留单一租金
    费用留在营业费用里，EBIT 已被全额租金扣过；IFRS 16 才拆成折旧 + 利息。
    所以对 10-K 报告主体，必须自己做这个还原。

    近似做法：利息部分 ≈ 租赁负债 × 隐含利率。这是近似，不是精确值 ——
    精确值需要读附注里的折现率与到期结构。

    有效税率异常（负数、>60%，多见于一次性税务事项）时回退到美国法定
    联邦税率 21%，此时报告会标注 —— **因为这是假设，不是事实**。
    """
    ebit = p.operating_income
    if ebit is None:
        return None
    if capitalize_leases:
        lease_liab = _add(p.lease_liab_long, p.lease_liab_short)
        if lease_liab:
            ebit = ebit + lease_liab * LEASE_IMPLIED_RATE
    rate = effective_tax_rate(p)
    return ebit * (1 - (rate if rate is not None else fallback_rate))


def balance_check(p: Period, tol: float = 0.005) -> bool | None:
    """最廉价的数据完整性护栏：资产 == 负债 + 所有者权益。

    拼接不同 `end` 日期的资产负债表科目（并购、财年切换时极易发生）会造出
    一张**现实中不存在的报表**，而这个会计恒等式几乎必然被打破。
    返回 None 表示无法校验（缺 `LiabilitiesAndStockholdersEquity` 标签）。
    """
    a, le = p.assets, p.liabilities_and_equity
    if a is None or le is None or a == 0:
        return None
    return abs(a - le) / abs(a) <= tol


def invested_capital(p: Period) -> float | None:
    """投入资本（融资视角）= 有息负债 + 租赁负债 + 股东权益 − 超额现金。

    含义：**为了产生经营利润，一共占用了多少钱**。ROIC 的分母必须是这个，
    而不是总资产 —— 总资产里混着不产生经营利润的现金和投资。
    """
    d = total_debt(p)
    e = p.equity
    if e is None:
        return None
    ic = _add(d, e)
    ec = excess_cash(p)
    return None if ic is None else ic - (ec or 0)


def _avg(cur: float | None, prev: float | None) -> float | None:
    """期初期末平均。没有上期就用期末值 —— 会略微高估周转率/回报率，
    因此报告里第一年的比率要标注为「仅期末口径」。"""
    if cur is None:
        return None
    return cur if prev is None else (cur + prev) / 2


def roic(p: Period, prev: Period | None) -> float | None:
    """ROIC = NOPAT / 平均投入资本。投入资本 ≤ 0 时返回 None。

    这是**判断一门生意好坏最核心的单一数字**：每投入 1 块钱资本，一年能
    产生多少税后经营利润。

    ⚠️ 它本身不说明价值创造 —— 必须和资本成本比。ROIC < 资本成本时，
    增长得越快毁灭的价值越多（见 FRAMEWORK.md §5 的四象限）。

    ⚠️ **投入资本为负时 ROIC 没有意义，这里返回 None 而不是一个数。**
    这不是罕见边界：实测苹果 FY2014–FY2020 投入资本连续为负（超额现金
    超过了有息负债 + 账面权益之和 —— 常年巨额回购把账面权益打得很薄，
    同时持有巨量有价证券）。此时公式会输出 −462% 到 +5627% 这类垃圾，
    而且**看起来像个数**。对这类公司应改看自由现金流对市值的回报率，
    或用经营性资产口径的 ROIC（路线图）。
    """
    a = invested_capital(p)
    b = invested_capital(prev) if prev else None
    if a is None or a <= 0 or (b is not None and b <= 0):
        return None
    return _div(nopat(p), _avg(a, b))


ROIC_MEANINGFUL_CEILING = 1.0
"""ROIC 超过 100% 时，它已经不再是一个有鉴别力的指标。

这**不是计算错误**：轻资产 + 负营运资本的公司（苹果、Visa、万事达）
占用的经营资本本来就极少，几百个百分点的 ROIC 是真实的。但正因为分母
接近于零，它对现金口径的微小变化极度敏感 —— 苹果 FY2022 到 FY2025 的
ROIC 在 942% 与 318% 之间摆动，摆动来自投入资本从 8B 到 52B 的变化，
而不是生意质地的变化。

到了这个区间，该换成看**自由现金流的绝对额与增长的持续性**，
而不是继续比较 ROIC 的大小。报告会对这类年份加标注。
"""


def roe(p: Period, prev: Period | None) -> float | None:
    return _div(p.net_income, _avg(p.equity, prev.equity if prev else None))


def dupont(p: Period, prev: Period | None) -> dict[str, float | None]:
    """杜邦三分解：ROE = 净利率 × 资产周转率 × 权益乘数。

    最有价值的用法不是算出 ROE，而是看出**同一个 ROE 背后是三种完全不同的生意**：
      · 高净利率、低周转  → 品牌/专利型（茅台、苹果、制药）
      · 低净利率、高周转  → 效率型（Costco、沃尔玛）
      · 靠权益乘数堆出来  → 杠杆型（银行、地产）—— 这种 ROE 最脆弱，
        因为杠杆在顺境放大收益，在逆境放大的是破产概率。
    """
    avg_assets = _avg(p.assets, prev.assets if prev else None)
    avg_equity = _avg(p.equity, prev.equity if prev else None)
    return {
        "net_margin": _div(p.net_income, p.revenue),
        "asset_turnover": _div(p.revenue, avg_assets),
        "equity_multiplier": _div(avg_assets, avg_equity),
        "roe": _div(p.net_income, avg_equity),
    }


def d_and_a_total(p: Period) -> float | None:
    """折旧摊销合计，必要时把收购无形资产摊销补上。

    `DepreciationDepletionAndAmortization` 已含摊销，直接用；
    但回退到 `DepreciationAndAmortization` 时，并购驱动的公司往往把收购无形
    资产摊销单独列示（实测 Marvell FY2022：前者 0.266B、后者 0.979B）。
    此时只用前者会把 D&A 低估近 5 倍，「资本开支/折旧」随之虚高，
    把一家在吃老本的公司误读成扩张期。
    """
    base = p.d_and_a
    if base is None:
        return None
    tag = p.tags_used.get("d_and_a", "")
    amort = p.amort_intangibles
    # 只有**窄口径**标签才需要补无形摊销；`DepreciationDepletionAndAmortization`
    # 与 `DepreciationAmortizationAndAccretionNet` 本身已含摊销，再加就重复了。
    NARROW = ("DepreciationAndAmortization", "Depreciation")
    if tag in NARROW and amort:
        return base + amort
    return base


def capex(p: Period) -> float | None:
    """资本开支，统一取正值。

    **XBRL 的符号约定是个静默错误源**：`PaymentsToAcquire*` 系列在 XBRL 里
    存的是**正数**（借方元素），报表上显示为负是靠 negatedLabel 渲染的。
    绝大多数申报人遵守这个约定，但偶有例外。若不统一符号，`OCF − CapEx`
    在个别公司身上会变成 `OCF + CapEx`，把最烧钱的公司算成现金奶牛。
    """
    return None if p.capex is None else abs(p.capex)


def fcf(p: Period) -> float | None:
    """自由现金流 = 经营现金流 − 资本开支。最常用的口径。"""
    return _sub(p.ocf, capex(p))


def fcf_ex_sbc(p: Period) -> float | None:
    """扣除股权激励后的自由现金流 = OCF − CapEx − SBC。

    为什么要有这个口径：股权激励是**真实的成本**（公司用股份代替现金支付薪酬），
    但它被当作非现金项目加回了经营现金流。对 SBC 占营收 5%+ 的科技公司，
    不扣 SBC 的 FCF 会系统性高估股东能拿到的钱——除非公司同时用等额回购
    把稀释买回来，而那笔回购是实实在在花掉的现金。

    实用判据：**回购金额 ≥ SBC 才算真回购**，否则那只是在替稀释擦屁股。
    """
    v = fcf(p)
    return None if v is None else v - (p.sbc or 0)


def buyback_quality(p: Period) -> float | None:
    """回购/SBC 比。>1 才是真正减少股本的回购；≈1 只是抵消稀释；<1 是净稀释。"""
    return _div(p.buybacks, p.sbc)


def accrual_ratio(p: Period, prev: Period | None) -> float | None:
    """应计比率 = (净利润 − 经营现金流) / 平均总资产。

    **这是财报质量最重要的单一信号。** 利润里没有变成现金的那部分，就是会计
    估计（应收、存货、资本化、递延）撑起来的部分。Sloan (1996) 的经典发现：
    高应计的公司未来回报显著更差，因为应计项终将回归现金。

    经验带（美股大盘股）：< 0 优秀（现金比利润多）；0~5% 正常；
    > 10% 需要解释；连续多年 > 10% 是红旗。

    ⚠️ 边界：高速扩张期的公司（营运资本随增长自然扩张）应计天然偏高，
    要和同业、和自己历史比，不能看绝对值。
    """
    return _div(_sub(p.net_income, p.ocf), _avg(p.assets, prev.assets if prev else None))


def cash_conversion(p: Period, prev: Period | None) -> dict[str, float | None]:
    """现金转换周期 CCC = DSO + DIO − DPO（天）。

    它衡量**一块钱从压进存货到收回现金要多久**。CCC 为负是极强的商业模式
    信号：先收钱后付货款，等于免费占用上下游的资金做生意（Costco、亚马逊、
    苹果都是负 CCC）。无息负债占用得越多，说明产业链话语权越强。
    """
    rev, cogs = p.revenue, p.cogs
    ar = _avg(p.receivables, prev.receivables if prev else None)
    inv = _avg(p.inventory, prev.inventory if prev else None)
    ap = _avg(p.payables, prev.payables if prev else None)
    dso = _div(ar, rev)
    dio = _div(inv, cogs)
    dpo = _div(ap, cogs)
    d = {
        "dso": dso * 365 if dso is not None else None,
        "dio": dio * 365 if dio is not None else None,
        "dpo": dpo * 365 if dpo is not None else None,
    }
    if all(v is not None for v in d.values()):
        d["ccc"] = d["dso"] + d["dio"] - d["dpo"]
    else:
        d["ccc"] = None
    return d


def margins(p: Period) -> dict[str, float | None]:
    gp = p.gross_profit
    if gp is None and p.revenue is not None and p.cogs is not None:
        gp = p.revenue - p.cogs
    return {
        "gross": _div(gp, p.revenue),
        "operating": _div(p.operating_income, p.revenue),
        "net": _div(p.net_income, p.revenue),
        "fcf": _div(fcf(p), p.revenue),
        "sbc_of_revenue": _div(p.sbc, p.revenue),
        # SBC/营收 会被毛利率结构污染：90% 毛利的软件公司 12% 的 SBC/营收，
        # 对股东的实际稀释可能低于 25% 毛利的硬件公司 8%。SBC/毛利 与
        # SBC/FCF 才是可跨行业比较的口径，最直接的则是净稀释率（见 dilution）。
        "sbc_of_gross_profit": _div(p.sbc, gp),
        "sbc_of_fcf": _div(p.sbc, fcf(p)),
        "capex_intensity": _div(capex(p), p.revenue),
        "capex_over_da": _div(capex(p), d_and_a_total(p)),
    }


NONOP_DOMINANT_THRESHOLD = 0.30
"""非经营损益占税前利润超过此比例时，净利润已不能代表经营成果。"""


def nonoperating_share(p: Period) -> float | None:
    """非经营损益 / 税前利润 —— **净利润有多少不是经营赚来的**。

    非经营损益 = 税前利润 − 营业利润，主要包含投资的公允价值变动、
    处置收益、汇兑损益等。ASU 2016-01 之后，**股权投资的未实现增值直接
    计入净利润**，于是持有大量非上市股权的公司，净利润会与经营脱节。

    这不是罕见情况，实测两例：
      · Alphabet 2026Q2：营业利润 408 亿（利润率 34%，正常），
        但股权投资重估收益 **990 亿**，把净利润推到 1122 亿 ——
        净利率 94%。TTM 净利 2442 亿里约 1360 亿是这类非现金收益，
        而同期自由现金流只有 533 亿。
      · Nebius FY2025：经营亏损 6.12 亿，靠 ClickHouse 重估收益 5.99 亿
        把净利润做成 +0.83 亿 —— 报表"盈利"，经营实亏。

    **看到这个比例高，净利润、净利率、ROE、PE 全部失去意义**，
    必须改看营业利润与自由现金流。
    """
    if p.pretax_income is None or p.operating_income is None or p.pretax_income == 0:
        return None
    return (p.pretax_income - p.operating_income) / p.pretax_income


def dilution(p: Period, prev: Period | None) -> float | None:
    """年度净稀释率 = 摊薄股数同比增幅。

    这是衡量股权激励对股东伤害的**最直接、最难粉饰**的口径 —— 它已经把
    SBC 与回购的净效果合并了。为正说明股东被稀释，为负说明回购真正
    减少了股本。

    ⚠️ 拆股会污染这条序列：companyfacts 里的股数是各次报送的 as-reported 值，
    老 filing 里是拆股前的数字，且不会被追溯改写（除非公司在后续 10-K 中
    重报该期间）。苹果 2014 年 7:1、2020 年 4:1，英伟达 4:1 与 10:1 ——
    跨越拆股年份的序列会混入不可比单位，看到 ±数百% 的跳变即为此。
    """
    if prev is None:
        return None
    return _div(_sub(p.shares_diluted, prev.shares_diluted), prev.shares_diluted)


def cagr(series: list[float | None], ends: list[str] | None = None) -> float | None:
    """复合年化增长率。跨度由**实际端点日期**算出，不由列表长度猜。

    首尾任一为非正数时返回 None —— 负基数的 CAGR 在数学上没有意义，
    很多财经网站在这里直接输出垃圾。

    ⚠️ **必须用端点日期算跨度，数个数是不够的。** 序列中间有缺失年份时，
    "存活值个数 − 1" 会低估真实跨度，从而高估增长率：
    实测美国运通 2010→2025（中间缺 2011–2015，只有 11 个观测点）按个数算得
    营收 CAGR 4.0%，而实际跨 15 年、真值 2.67% —— 虚高 51%。
    而这个数正是逆向 DCF 里用来检验隐含增长率的参照，错了会直接带偏结论。

    参数
      series  数值序列（可含 None）
      ends    与 series 等长的期末日期（ISO 字符串）。给了就用它算真实跨度；
              不给则退回"个数 − 1"，并且**只在你确信序列连续时才可以这样用**。
    """
    if ends is not None and len(ends) != len(series):
        raise ValueError("cagr: series 与 ends 长度必须一致")

    pairs = [(v, ends[i] if ends else None) for i, v in enumerate(series) if v is not None]
    if len(pairs) < 2:
        return None
    a, b = pairs[0][0], pairs[-1][0]
    if a <= 0 or b <= 0:
        return None

    if ends is not None:
        from datetime import date

        span = (date.fromisoformat(pairs[-1][1]) - date.fromisoformat(pairs[0][1])).days / 365.25
    else:
        span = len(pairs) - 1
    if span <= 0:
        return None
    return (b / a) ** (1 / span) - 1


def incremental_roic(periods: list[Period], span: int = 5) -> float | None:
    """增量 ROIC = Δ NOPAT / Δ 投入资本（近 span 年）。

    **比存量 ROIC 更能预测未来。** 存量 ROIC 高，可能只是十年前那笔投资
    留下的遗产；增量 ROIC 才回答"公司现在新投进去的钱，回报如何"。
    一家存量 ROIC 25%、增量 ROIC 5% 的公司，正在把好生意赚的钱倒进坏项目里——
    这是资本配置失败最典型的财务显影。

    ⚠️ 三道闸，缺一个就会输出天文数字：
      (1) 首尾投入资本都必须 > 0（负 IC 见 `roic` 的说明）；
      (2) ΔIC 必须 > 0；
      (3) **ΔIC 必须达到基期 IC 的 10% 以上** —— 分母是两个大数之差，
          微小变动会把比值放大到荒谬。实测 Visa 近 5 年 IC 只从 44.3B 增到
          45.8B（ΔIC 仅 1.5B），而 ΔNOPAT 8.8B，算出「增量 ROIC 587%」。
          资本基本没变动的公司，这个指标本就不适用，应显示「—」。
    """
    if len(periods) < span + 1:
        return None
    a, b = periods[-span - 1], periods[-1]
    ic_a, ic_b = invested_capital(a), invested_capital(b)
    if ic_a is None or ic_b is None or ic_a <= 0 or ic_b <= 0:
        return None
    di = ic_b - ic_a
    if di <= 0 or di < 0.10 * ic_a:
        return None  # 投入资本没有实质增长时，该指标无意义
    dn = _sub(nopat(b), nopat(a))
    return None if dn is None else dn / di
