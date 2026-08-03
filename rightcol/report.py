"""把算好的指标渲染成**数据包**（markdown）。

这份数据包不是给人读的最终报告，它是**给 LLM 精读层的输入**：
确定性层负责"数字保证是对的"，精读层负责"所以呢"。

分工的理由：数字算错了，再漂亮的叙事都是有害的；而数字本身不会告诉你
管理层今年悄悄改了口径。两件事必须由两种东西来做。
"""

from __future__ import annotations

from . import metrics as M
from .metrics import Period


def _pct(x: float | None, digits: int = 1) -> str:
    return "—" if x is None else f"{x * 100:.{digits}f}%"


def _num(x: float | None, scale: float = 1e-9, digits: int = 1, suffix: str = "B") -> str:
    return "—" if x is None else f"{x * scale:,.{digits}f}{suffix}"


def _days(x: float | None) -> str:
    return "—" if x is None else f"{x:.0f}"


def _x(x: float | None, digits: int = 2) -> str:
    return "—" if x is None else f"{x:.{digits}f}×"


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _quarterly_section(ps: list[Period], qs: list[Period]) -> str:
    """季度视图 + TTM。放在最前面，因为**「数据有多旧」是你该知道的第一件事**。"""
    L: list[str] = []
    A = L.append
    stale = M.staleness_days(ps[-1].end, qs[-1].end)

    A("## ⏱ 最新四个季度 · TTM")
    A("")
    if stale is not None and stale >= 180:
        A(f"> 🔴 **年报视图已过期 {stale} 天**（最新财年止 {ps[-1].end}，最新季末 {qs[-1].end}）。")
        A("> **对周期股这是致命的** —— 下面所有年度表格反映的可能是完全不同的经营状态，")
        A("> 请以本节的 TTM 与季度趋势为准。")
    elif stale:
        A(f"> 年报止 {ps[-1].end}，最新季末 **{qs[-1].end}**（新 {stale} 天）。")
    else:
        A(f"> 年报已是最新（止 {ps[-1].end}），季度视图仅用于看季内趋势。")
    A("")

    A(_row(["季末", "营收", "环比", "同比", "毛利率", "营业利润率", "营业成本", "存货/营收", "FCF"]))
    A(_row(["---"] * 9))
    by_end = {q.end: q for q in qs}
    for i, q in enumerate(qs[-8:]):
        mg = M.margins(q)
        # 同比：找 4 个季度前那一期（不用环比 —— 季节性会淹没趋势）
        idx = qs.index(q)
        yoy = None
        if idx >= 4 and qs[idx - 4].revenue:
            yoy = M._div(M._sub(q.revenue, qs[idx - 4].revenue), qs[idx - 4].revenue)
        # 环比：拐点比同比早两三个季度出信号（实测 AMD 同比 +37.8% 而环比已 −0.2%）
        qoq = M._div(M._sub(q.revenue, qs[idx - 1].revenue), qs[idx - 1].revenue) if idx else None
        # 营业成本：与营收增速对比 → 拆出增长里有多少是价格
        cogs = q.cogs if q.cogs is not None else (
            q.revenue - q.gross_profit if (q.revenue is not None and q.gross_profit is not None) else None
        )
        A(
            _row(
                [
                    q.end,
                    _num(q.revenue),
                    _pct(qoq),
                    _pct(yoy),
                    _pct(mg["gross"]),
                    _pct(mg["operating"]),
                    _num(cogs),
                    _pct(M._div(q.inventory, q.revenue)),
                    _num(M.fcf(q)),
                ]
            )
        )
    A("")

    t_rev, t_ni, t_fcf = M.ttm(qs, "revenue"), M.ttm(qs, "net_income"), M.ttm_fcf(qs)
    A(_row(["TTM（最近四季合计）", "营收", "净利润", "自由现金流"]))
    A(_row(["---"] * 4))
    A(_row(["**TTM**", _num(t_rev), _num(t_ni), _num(t_fcf)]))
    A(_row(["最新完整财年", _num(ps[-1].revenue), _num(ps[-1].net_income), _num(M.fcf(ps[-1]))]))
    if t_rev and ps[-1].revenue:
        A(_row(["差异", _pct(t_rev / ps[-1].revenue - 1),
                _pct(t_ni / ps[-1].net_income - 1) if t_ni and ps[-1].net_income else "—",
                _pct(t_fcf / M.fcf(ps[-1]) - 1) if t_fcf and M.fcf(ps[-1]) else "—"]))
    A("")
    A("**怎么读**（详见 FRAMEWORK.md §5.8「季度视角」的四个动作）：")
    A("")
    A("1. **拆价与量** —— 比较**营收**与**营业成本**的增速。成本不动而收入暴涨，")
    A("   说明增量几乎全是**价格**，而价格驱动的增长会引来供给、均值回归。")
    A("   实测 Micron：营收 +377% 而营业成本仅 +19%。")
    A("2. **看存货** —— 这里用 **存货/营收** 而非存货天数：价格暴涨时毛利率飙升、")
    A("   成本占比骤降，会让存货天数**假性上升**（实测 SanDisk 从 121「升」到 158，")
    A("   而存货绝对额是平的、存货/营收其实从 65% 降到 38%）。")
    A("3. **环比比同比先出信号** —— 对斜率陡峭的公司，同比会掩盖拐点。")
    A("   实测 AMD：同比仍 +37.8%，环比已 −0.2%。")
    A("4. **TTM 与最新财年差异越大**，年报视图越不能代表当下。")
    A("")
    A("⚠️ 口径说明：**10-Q 里的现金流量表是年初至今累计的**，本项目用相邻累计值")
    A("相减还原单季；财年最后一季不在任何 10-Q 里，用「全年 − 前三季」倒推。")
    A("两类还原值在第七节的口径留痕里带 `+derived` 后缀。")
    A("")
    return "\n".join(L)


def data_pack(ticker: str, name: str, periods: list[Period], quarters: list[Period] | None = None) -> str:
    """生成一家公司的确定性数据包。`quarters` 给了就额外输出季度视图与 TTM。"""
    if not periods:
        return f"# {ticker}\n\n⚠️ 无可用年度数据。"

    ps = periods
    ends = [p.end for p in ps]
    out: list[str] = []
    A = out.append

    A(f"# {name} ({ticker}) — 确定性数据包")
    A("")
    A(f"数据源：SEC EDGAR XBRL（申报原始口径，未经任何调整）· 财年数 {len(ps)} · 最新财年止 **{ends[-1]}**")
    A("")
    A("> 本文件只有数字，没有判断。判断请对照 `FRAMEWORK.md` 的三个闸门自行做出。")
    A("> 缺失一律显示 `—`，**绝不以 0 填充**——数据中断必须长得像数据中断。")
    A("")

    if quarters:
        A(_quarterly_section(ps, quarters))

    # ---------------- 闸门一：这是不是一门好生意 ----------------
    A("## 一、赚不赚钱 · 盈利能力与资本回报")
    A("")
    A(_row(["财年止", "营收", "营收YoY", "毛利率", "营业利润率", "净利率", "ROIC", "ROE", "增量ROIC(5y)"]))
    A(_row(["---"] * 9))
    # 按「类别 → 涉及年份」归并，同一类问题只写一行说明，后面跟年份列表。
    # 逐年重复同一段解释会淹没真正需要注意的东西。
    notes: dict[str, list[str]] = {}

    def _note(kind: str, year: str) -> None:
        notes.setdefault(kind, []).append(year)

    for i, p in enumerate(ps):
        # 与上一年之间有缺失年份时，所有跨期指标（YoY、期初期末平均）都不可信
        prev = M.prev_of(ps, i)
        mg = M.margins(p)
        yoy = M._div(M._sub(p.revenue, prev.revenue), prev.revenue) if prev else None
        inc = M.incremental_roic(ps[: i + 1]) if i >= 5 else None
        r = M.roic(p, prev)
        flag = ""
        if p.gap_before:
            flag += "🕳"
            _note("gap", p.end)
        if p.balance_ok is False:
            flag += "⚠️"
            _note("balance", p.end)
        if p.structural_break:
            flag += "✂️"
            _note("structural_break", p.end)
        if r is not None and r > M.ROIC_MEANINGFUL_CEILING:
            flag += "∞"
            _note("roic_ceiling", p.end)
        if M.effective_tax_rate(p) is None and p.operating_income is not None:
            flag += "†"
            _note("tax_fallback", p.end)
        nonop = M.nonoperating_share(p)
        if nonop is not None and nonop > M.NONOP_DOMINANT_THRESHOLD:
            flag += "💰"
            _note("nonop", p.end)
        A(
            _row(
                [
                    p.end + (f" {flag}" if flag else ""),
                    _num(p.revenue),
                    _pct(yoy),
                    _pct(mg["gross"]),
                    _pct(mg["operating"]),
                    _pct(mg["net"]),
                    _pct(r),
                    _pct(M.dupont(p, prev)["roe"]),
                    _pct(inc),
                ]
            )
        )
    A("")
    if notes:
        legend = {
            "gap": ("🕳", "与上一行之间存在**缺失财年** —— 该行的 YoY 及所有「期初期末平均」类"
                          "指标（ROIC/ROE/应计）已置为 `—`，因为它们会跨越数年而非一年。"),
            "balance": ("⚠️", "**未通过会计恒等式**（资产 ≠ 负债+权益）—— 该年的资产负债表科目"
                              "来自不同申报期，周转率/权益乘数/应计/ROIC 均受影响，请勿采信。"),
            "roic_ceiling": ("∞", "**ROIC > 100%**：轻资产 + 负营运资本使投入资本极小。这个数"
                                  "真实但**已失去鉴别力**（分母接近零，微小口径变化就能让它剧烈摆动），"
                                  "请改看自由现金流的绝对额与增长的持续性。"),
            "structural_break": ("✂️", "**营收同比剧变（±80% 以上）** —— 请回原文确认这是真实经营变化，"
                                       "还是**业务重组 / 分拆 / 并购**导致的口径断裂。若是后者，"
                                       "**任何跨越该年的 CAGR、趋势与平均值都无意义**。"
                                       "（实测 Nebius 2022 年 −99.7% 是剥离俄罗斯业务；"
                                       "CoreWeave 2024 年 +736% 则是真实增长——所以这只是提示，不是判定。）"),
            "nonop": ("💰", "**净利润的三成以上不是经营赚来的** —— 非经营损益（多为股权投资的"
                            "公允价值重估、处置收益）占税前利润超过 30%。ASU 2016-01 之后股权投资的"
                            "**未实现**增值直接计入净利润，是非现金的。此时**净利率 / ROE / PE 全部失真**，"
                            "请改看营业利润与自由现金流。"),
            "tax_fallback": ("†", "**有效税率异常**（亏损年或一次性税务事项），NOPAT 与 ROIC 使用了"
                                  "21% 法定税率**假设**，不是该年实际税率。"),
        }
        A("**数据完整性标注**：")
        A("")
        for kind, years in notes.items():
            sym, text = legend[kind]
            A(f"- {sym} {text}")
            A(f"  涉及财年：{', '.join(years)}")
        A("")
    A("> ROIC 显示 `—` 的年份，多数是**投入资本为负**（超额现金超过有息负债+账面权益，")
    A("> 常见于常年巨额回购 + 持有巨量有价证券的公司）。此时 ROIC 在数学上无意义，")
    A("> 本项目返回 `—` 而不是一个看起来像数的垃圾值。")
    A("")
    A("**怎么读**：ROIC 是判断生意质地最核心的单一数字，但它必须和**资本成本**比——")
    A("ROIC 低于资本成本时，增长得越快毁灭的价值越多。增量 ROIC 比存量 ROIC 更能预测未来：")
    A("存量高可能只是十年前那笔投资的遗产，增量才回答「现在新投的钱回报如何」。")
    A("")

    # ---------------- 杜邦 ----------------
    A("## 二、靠什么赚 · 杜邦拆解")
    A("")
    A(_row(["财年止", "净利率", "资产周转率", "权益乘数", "= ROE"]))
    A(_row(["---"] * 5))
    for i, p in enumerate(ps):
        d = M.dupont(p, M.prev_of(ps, i))
        A(_row([p.end, _pct(d["net_margin"]), _x(d["asset_turnover"]), _x(d["equity_multiplier"]), _pct(d["roe"])]))
    A("")
    A("**怎么读**：同一个 ROE 背后可以是三种完全不同的生意——")
    A("高净利率低周转＝品牌/专利型；低净利率高周转＝效率型；靠权益乘数堆出来的＝杠杆型。")
    A("**杠杆型的 ROE 最脆弱**：杠杆在顺境放大收益，在逆境放大的是破产概率。")
    A("")

    # ---------------- 现金质量 ----------------
    A("## 三、赚的是不是真钱 · 现金质量")
    A("")
    A(_row(["财年止", "净利润", "经营现金流", "OCF/净利", "资本开支", "自由现金流", "FCF(扣SBC)", "应计比率"]))
    A(_row(["---"] * 8))
    for i, p in enumerate(ps):
        prev = M.prev_of(ps, i)
        A(
            _row(
                [
                    p.end,
                    _num(p.net_income),
                    _num(p.ocf),
                    _x(M._div(p.ocf, p.net_income)),
                    _num(p.capex),
                    _num(M.fcf(p)),
                    _num(M.fcf_ex_sbc(p)),
                    _pct(M.accrual_ratio(p, prev)),
                ]
            )
        )
    A("")
    A("**怎么读**：利润是观点，现金是事实。但 **OCF/净利润 不是可靠的单一警报**——")
    A("股权激励与折旧都要加回经营现金流，会把科技公司和重资产公司的这个比值")
    A("**结构性抬高**，两类恰恰都是你想警惕的对象。")
    A("")
    A("真正有鉴别力的是右侧两列：**FCF(扣SBC)** 与 **应计比率**，加上第五节的摊薄股数变化。")
    A("应计比率经验带：< 0 优秀 · 0~5% 正常 · > 10% 需要解释 · 连续多年 > 10% 是红旗。")
    A("（高速扩张期营运资本自然膨胀，应计天然偏高，须与自身历史和同业比。）")
    A("")

    # ---------------- 营运效率 ----------------
    A("## 四、产业链话语权 · 现金转换周期")
    A("")
    A(_row(["财年止", "DSO 应收天数", "DIO 存货天数", "DPO 付款天数", "CCC 现金周期"]))
    A(_row(["---"] * 5))
    for i, p in enumerate(ps):
        c = M.cash_conversion(p, M.prev_of(ps, i))
        A(_row([p.end, _days(c["dso"]), _days(c["dio"]), _days(c["dpo"]), _days(c["ccc"])]))
    A("")
    A("**怎么读**：CCC 为负＝**先收钱后付货款**，等于免费占用上下游资金做生意，")
    A("是产业链话语权极强的证据。DSO / DIO 增速持续快于营收增速，是渠道压货或需求转弱的**早期**信号——")
    A("它通常比营收下滑早出现一到两个季度。")
    A("")

    # ---------------- 资本配置 ----------------
    A("## 五、赚的钱归谁 · 资本配置")
    A("")
    A(_row(["财年止", "SBC", "SBC/毛利", "回购", "回购/SBC", "摊薄股数", "净稀释率", "分红", "资本开支/折旧"]))
    A(_row(["---"] * 9))
    for i, p in enumerate(ps):
        mg = M.margins(p)
        A(
            _row(
                [
                    p.end,
                    _num(p.sbc),
                    _pct(mg["sbc_of_gross_profit"]),
                    _num(p.buybacks),
                    _x(M.buyback_quality(p)),
                    _num(p.shares_diluted, scale=1e-6, suffix="M", digits=0),
                    _pct(M.dilution(p, M.prev_of(ps, i))),
                    _num(p.dividends_paid),
                    _x(mg["capex_over_da"]),
                ]
            )
        )
    A("")
    A("**怎么读**：**摊薄股数与净稀释率是股权激励伤害股东最直接、最难粉饰的证据** ——")
    A("净稀释率为正说明股东在被稀释，为负说明回购真正减少了股本。")
    A("⚠️ 拆股会污染这条序列（申报值是拆股前原始数字，不做追溯调整），")
    A("看到 ±数百% 的跳变先查是不是拆股，不要当成稀释。")
    A("")
    A("**回购/SBC > 1 才是真回购**；≈1 只是在抵消股权激励的稀释；<1 是净稀释。")
    A("SBC 的分母用**毛利**而非营收 —— 营收口径会被毛利率结构污染，")
    A("90% 毛利的软件公司和 25% 毛利的硬件公司不可直接比。")
    A("资本开支/折旧 长期 < 1 说明公司在吃老本（产能在萎缩）；持续 > 1.5 是扩张期，要问回报率。")
    A("并购支出大而增量 ROIC 低，是资本配置失败最典型的组合。")
    A("")

    # ---------------- 财务健康 ----------------
    A("## 六、会不会突然死 · 财务健康")
    A("")
    A(_row(["财年止", "总资产", "股东权益", "有息负债(含租赁)", "现金+短投", "净负债", "净负债/FCF", "商誉/权益"]))
    A(_row(["---"] * 8))
    for p in ps:
        debt = M.total_debt(p)
        cash = M.excess_cash(p)
        net = M._sub(debt, cash)
        A(
            _row(
                [
                    p.end,
                    _num(p.assets),
                    _num(p.equity),
                    _num(debt),
                    _num(cash),
                    _num(net),
                    _x(M._div(net, M.fcf(p))),
                    _pct(M._div(p.goodwill, p.equity)),
                ]
            )
        )
    A("")
    A("**怎么读**：净负债/FCF 是「不吃不喝几年能还清」。>4× 就要认真看到期结构。")
    A("商誉/权益高，意味着账面净资产里很大一块是过去并购付出的溢价——**它只会减值，不会增值**。")
    A("")

    # ---------------- 口径留痕 ----------------
    A("## 七、口径留痕（跨公司比较前必读）")
    A("")
    last = ps[-1]
    used = {k: v for k, v in sorted(last.tags_used.items())}
    A("最新财年各科目实际命中的 us-gaap 标签：")
    A("")
    A("```")
    for k, v in used.items():
        A(f"{k:24} {v}")
    A("```")
    A("")
    missing = [k for k in ("revenue", "operating_income", "gross_profit", "capex", "inventory") if k not in used]
    if missing:
        A(f"⚠️ 最新财年缺失：`{'`, `'.join(missing)}`。")
        A("若这是金融机构（银行/保险），**这些科目是结构性不存在，不是数据缺失**——")
        A("对它套用毛利率、周转率、FCF 会得到纯噪音，须改用 NIM / 拨备覆盖 / 资本充足率等专用指标。")
        A("")
    return "\n".join(out)
