"""估值层 —— 回答"合理的价格"那一半。

这个模块刻意**不告诉你一家公司值多少钱**。

因为那个数字是假的：正向 DCF 的结果几乎完全由你自己填进去的增长率决定，
你想要什么答案就能算出什么答案。芒格说他从没见过巴菲特算 DCF，就是这个道理。

这里做的是**反过来问**：

    「以当前这个价格买入，市场在替我假设未来会发生什么？
      这个假设，我信不信？」

这个问法的好处是它把主观性挤到了明处 —— 输出不是一个价格，而是一个
**可证伪的命题**：「这个价格要求它未来十年 FCF 年化增长 14%」。
14% 合不合理，你可以拿它的历史增速、行业天花板、竞争格局去检验。
这是认知，前者只是算术。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DCFAssumptions:
    """折现现金流的全部假设。**每一个都是假设，不是事实** —— 所以全部显式列出。"""

    discount_rate: float = 0.09
    """折现率 r。个人投资者的实用取法有两种，二选一但要一以贯之：
       (a) 机会成本法：你要求的最低年化回报（巴菲特长期用 ~10%，段永平类似）。
       (b) CAPM 近似：10 年期美债收益率 + 股权风险溢价（历史区间约 2%~6.5%，
           均值 ~4.7%，**不要固定成一个数**）。口径以 FRAMEWORK §5「资本成本 r 怎么取」为准。
    ⚠️ (b) 就是**本项目与 macroscope 的接口**：无风险利率由宏观决定，它一动，
       所有资产的现值同时重估。久期越长（现金流越靠后）的公司越敏感。"""

    terminal_growth: float = 0.025
    """永续增长率 g_t。**必须 < 长期名义 GDP 增速**（约 4%），否则你在假设这家公司
       最终会大于整个经济体。2.5% 已是偏乐观的常用值。
       check() 在 4.5% 才拦截，留了 0.5pp 缓冲。"""

    years: int = 10
    """显式预测期。10 年是惯例：足够长到让竞争优势的差异显现，又短到终值
       不至于吞掉全部估值。"""

    def check(self) -> list[str]:
        warn = []
        if self.terminal_growth >= self.discount_rate:
            warn.append("永续增长率 ≥ 折现率 —— 数学上估值发散到无穷，结果无意义")
        if self.terminal_growth > 0.045:
            warn.append(f"永续增长率 {self.terminal_growth:.1%} 高于长期名义 GDP，隐含它最终吞掉整个经济")
        if self.discount_rate < 0.05:
            warn.append(f"折现率 {self.discount_rate:.1%} 过低 —— 低于长期股权回报，会系统性高估")
        return warn


def pv_of_growing_fcf(fcf0: float, growth: float, a: DCFAssumptions) -> float:
    """给定起点 FCF 与增长率，算现值（显式期 + 终值）。

    终值用 Gordon 永续增长模型。**终值通常占总现值的 60~80%** —— 这意味着
    DCF 的结论主要由你对"十年后"的假设决定，而那是最不可知的部分。
    知道这一点，你就不会再迷信 DCF 算出来的精确数字。
    """
    if a.terminal_growth >= a.discount_rate:
        # 不能只警告不拦截：g_t > r 时这个函数会返回一个**负的现值**
        # （实测 r=5%、g_t=6%、fcf0=1e9 → −960 亿），既不报错也不返回 None，
        # 而 implied_growth 的二分法在这种参数下单调性也不再成立。
        raise ValueError(
            f"永续增长率 {a.terminal_growth:.2%} ≥ 折现率 {a.discount_rate:.2%}："
            f"Gordon 模型在此发散，估值无意义。请下调永续增长率或上调折现率。"
        )
    pv = 0.0
    cf = fcf0
    for t in range(1, a.years + 1):
        cf = cf * (1 + growth)
        pv += cf / (1 + a.discount_rate) ** t
    terminal = cf * (1 + a.terminal_growth) / (a.discount_rate - a.terminal_growth)
    pv += terminal / (1 + a.discount_rate) ** a.years
    return pv


def terminal_value_share(fcf0: float, growth: float, a: DCFAssumptions) -> float:
    """终值占总现值的比重 —— 用来提醒你这个估值有多依赖遥远的未来。"""
    total = pv_of_growing_fcf(fcf0, growth, a)
    cf = fcf0 * (1 + growth) ** a.years
    tv = cf * (1 + a.terminal_growth) / (a.discount_rate - a.terminal_growth)
    return (tv / (1 + a.discount_rate) ** a.years) / total if total else float("nan")


def implied_growth(target_value: float, fcf0: float, a: DCFAssumptions) -> float | None:
    """**逆向 DCF 的核心**：解出当前价格隐含的显式期 FCF 年化增长率。

    用二分法求解 pv_of_growing_fcf(fcf0, g) == target_value。

    参数
      target_value  市场当前给这些现金流开的价（通常用企业价值 EV，
                    或对净现金/净负债不大的公司直接用市值）
      fcf0          起点自由现金流。**用什么口径决定结论** ——
                    建议用近 3 年平均 FCF 而非最新一年，避免周期高点/低点失真；
                    科技股应同时看扣除 SBC 的版本。

    返回 None 表示无解（例如 FCF 为负 —— 此时 DCF 不适用，
    需要改用其他框架，见 FRAMEWORK.md「什么时候这套框架不适用」）。
    """
    if fcf0 is None or fcf0 <= 0 or target_value is None or target_value <= 0:
        return None
    lo, hi = -0.50, 1.00
    if pv_of_growing_fcf(fcf0, hi, a) < target_value:
        return None  # 即便年化 100% 增长十年也撑不起这个价
    if pv_of_growing_fcf(fcf0, lo, a) > target_value:
        return None  # 即便每年萎缩 50% 也比这个价贵 —— 市场在定价破产/清算
    for _ in range(200):
        mid = (lo + hi) / 2
        if pv_of_growing_fcf(fcf0, mid, a) < target_value:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# --------------------------------------------------------------------------
# 价值驱动公式 —— 治好"PE 高就是贵"的直觉误区
# --------------------------------------------------------------------------


def justified_pe(growth: float, roic: float, discount_rate: float) -> float | None:
    """合理市盈率（对 NOPAT 而言）= (1 − g/ROIC) / (r − g)

    这是 McKinsey《Valuation》的价值驱动公式，把 PE 拆回它的三个源头：
    增长 g、资本回报 ROIC、折现率 r。

    它说明的第一件事：**增长要花钱买。** 分子里的 (1 − g/ROIC) 就是再投资率——
    想长得快，就得把利润留下来再投；ROIC 越低，同样的增长要留存的利润越多，
    能分给股东的越少。

    第二件事，也是最反直觉的一件：**同样的增长率，ROIC 不同，配得上的 PE 天差地别。**
      g=8%, ROIC=40%, r=9%  →  PE ≈ 80   （再投资率仅 20%，增长几乎白送）
      g=8%, ROIC=10%, r=9%  →  PE ≈ 20   （再投资率 80%，增长基本自己吃光）
    所以"PE 40 太贵了"这句话本身没有信息量 —— 除非你同时说出它的 ROIC 和增速。

    第三件事：当 ROIC = r 时，公式退化成 1/r，**增长完全不创造价值**。
    ROIC < r 时，g 越大 PE 越低 —— 增长在毁灭价值。这就是 ROIC×增长
    四象限里"低 ROIC 高增长 = 价值毁灭机"那一格的数学证明。
    """
    if roic is None or roic <= 0 or discount_rate <= growth:
        return None
    reinvestment = growth / roic
    if reinvestment >= 1:
        return None  # 增长快过资本回报能支撑的极限，必须外部融资
    return (1 - reinvestment) / (discount_rate - growth)


def earnings_yield_spread(fcf_yield: float | None, risk_free: float | None) -> float | None:
    """自由现金流收益率 − 无风险利率 = 你为承担股权风险拿到的补偿。

    **这是 rightcol 与 macroscope 真正接上的地方。** 一家公司的 FCF 收益率
    5%，在 10 年期美债 1% 的环境里是慷慨的（利差 4%），在美债 5% 的环境里
    则毫无吸引力（利差 0）—— 公司一个字没变，价值判断却反转了。

    所以「合理的价格」从来不是一个绝对数，它是**相对无风险利率**的。
    宏观定分母，微观定分子，两边必须同时看。
    """
    if fcf_yield is None or risk_free is None:
        return None
    return fcf_yield - risk_free


def sensitivity(fcf0: float, a: DCFAssumptions, growths: list[float], rates: list[float]) -> dict:
    """估值对「增长 × 折现率」的敏感性网格。

    做这个表的目的不是找到"正确答案"，而是让你亲眼看到估值对假设有多敏感 ——
    这会让你对任何一个精确的目标价永久性地失去信任，这是好事。

    ⚠️ 敏感度**不要写死成一个数**。它随永续增长率、显式期、以及现金流的
    久期变化：默认参数（g_t=2.5%、10 年显式期）下，折现率上行 1pp 大约
    让估值下移 13~16%；久期更长的假设下会更大。`bin/value.py` 按实际表格
    动态算出这个区间，而不是印一句可能被自己表格证伪的经验值。
    """
    grid = {}
    for r in rates:
        aa = DCFAssumptions(discount_rate=r, terminal_growth=a.terminal_growth, years=a.years)
        grid[r] = {g: pv_of_growing_fcf(fcf0, g, aa) for g in growths}
    return grid
