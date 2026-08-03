"""us-gaap 标签 → 统一口径的回退链。

XBRL 的残酷现实：**同一个概念没有唯一标签**。同一家公司会随会计准则变更换标签
（Apple 的营收在 ASC 606 生效后从 `Revenues` 改成
`RevenueFromContractWithCustomerExcludingAssessedTax`），不同行业更是用完全
不同的科目体系。所以每个概念都必须给一条**按优先级排序的回退链**，并且回退是
**逐年**判定的 —— 某一年首选标签缺失就用次选，而不是整条序列二选一。

下面每条链都在 AAPL / COST / JPM / XOM / NVDA 五个行业样本上实测过（2026-07）。

⚠️ 一个必须记住的结构性事实（实测得到，不是理论）：
    **银行没有毛利、没有存货、没有资本开支、没有"营业利润"。**
    JPM 在这套通用科目上只能命中 12/18。这不是数据缺失，是**生意结构不同**。
    对金融股套用制造业的指标体系（毛利率、周转率、FCF）会得到纯粹的噪音——
    详见 FRAMEWORK.md「什么时候这套框架不适用」。
"""

from __future__ import annotations

# kind="flow"：利润表 / 现金流量表，期间值（需 ~365 天区间）
# kind="stock"：资产负债表，时点值
FLOW = "flow"
STOCK = "stock"

CONCEPTS: dict[str, tuple[str, list[str]]] = {
    # ---------------- 利润表 ----------------
    "revenue": (
        FLOW,
        [
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "RevenueFromContractWithCustomerIncludingAssessedTax",
            "Revenues",
            "SalesRevenueNet",
            "SalesRevenueGoodsNet",
        ],
    ),
    "cogs": (
        FLOW,
        [
            "CostOfGoodsAndServicesSold",
            "CostOfRevenue",
            "CostOfGoodsSold",
            "CostOfServices",
        ],
    ),
    "gross_profit": (FLOW, ["GrossProfit"]),
    "rnd": (FLOW, ["ResearchAndDevelopmentExpense"]),
    "sgna": (
        FLOW,
        ["SellingGeneralAndAdministrativeExpense", "GeneralAndAdministrativeExpense"],
    ),
    "operating_income": (FLOW, ["OperatingIncomeLoss"]),
    # ⚠️ 刻意**不含** `...BeforeIncomeTaxesDomestic` —— 那是税务附注里的
    # **美国境内分部**，不是合并税前利润。它的申报年份数往往比合并口径标签更多，
    # 一旦被当成主标签，就会用「合并所得税 ÷ 境内税前利润」算有效税率，
    # 税率被系统性抬高一倍（实测万事达 54.3% vs 真实 19.4%），
    # NOPAT 与 ROIC 随之全错（万事达 ROIC 51.8% vs 91.3%）。
    # 宁可某些年返回 None，也不能用分项冒充总额。
    "pretax_income": (
        FLOW,
        [
            "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
            "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
        ],
    ),
    "tax_expense": (FLOW, ["IncomeTaxExpenseBenefit"]),
    "net_income": (FLOW, ["NetIncomeLoss", "ProfitLoss"]),
    "interest_expense": (
        FLOW,
        ["InterestExpense", "InterestExpenseDebt", "InterestIncomeExpenseNet"],
    ),
    "eps_diluted": (FLOW, ["EarningsPerShareDiluted"]),
    "shares_diluted": (FLOW, ["WeightedAverageNumberOfDilutedSharesOutstanding"]),
    "shares_basic": (FLOW, ["WeightedAverageNumberOfSharesOutstandingBasic", "WeightedAverageNumberOfSharesOutstanding"]),
    # ---------------- 现金流量表 ----------------
    "ocf": (
        FLOW,
        [
            "NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        ],
    ),
    "capex": (
        FLOW,
        [
            "PaymentsToAcquirePropertyPlantAndEquipment",
            "PaymentsToAcquireProductiveAssets",
            "PaymentsForCapitalImprovements",
            "PaymentsToExploreAndDevelopOilAndGasProperties",
        ],
    ),
    # ⚠️ 链尾的裸 `Depreciation` **只含折旧不含摊销**，单用会低估。
    # 实测 Marvell：真实 D&A 主要是收购无形资产摊销（0.9B+），而 `Depreciation`
    # 只有 0.2B —— 单用会把「资本开支/折旧」高估数倍，误读成扩张期。
    # 但直接把它排除也不对：微软与谷歌**只申报这一个标签**，排除会让它们的
    # 折旧完全取不到。正解是保留它，并在 metrics.d_and_a_total() 里
    # 与 amort_intangibles 相加还原完整口径。
    "d_and_a": (
        FLOW,
        [
            "DepreciationDepletionAndAmortization",
            "DepreciationAmortizationAndAccretionNet",
            "DepreciationAndAmortization",
            # 裸 `Depreciation` 放在链尾 —— 它**只含折旧不含摊销**，单用会低估。
            # 但微软与谷歌恰恰只申报这一个标签（实测 MSFT FY2026 = 34.3B、
            # GOOGL FY2025 = 21.1B），删掉它会让这两家的折旧完全取不到。
            # 解法不是排除它，而是在 metrics.d_and_a_total() 里与无形资产
            # 摊销相加 —— 排除是我修 Marvell 时的过度反应。
            "Depreciation",
        ],
    ),
    # 收购无形资产摊销，单列。`DepreciationAndAmortization` 在并购驱动的公司里
    # 常常**不含**这块：实测 Marvell FY2022 该标签只有 0.266B，而无形资产摊销
    # 有 0.979B —— 真实 D&A 是 1.245B，用前者会把「资本开支/折旧」高估 4.7 倍，
    # 直接把一家吃老本的公司读成扩张期。见 metrics.d_and_a_total()。
    "amort_intangibles": (FLOW, ["AmortizationOfIntangibleAssets", "AmortizationOfAcquiredIntangibleAssets"]),
    # 股权激励：科技股的关键科目。它是**真实成本**（用股份代替现金发工资），
    # 但不在 OCF 里扣 —— 这是 FCF 口径争议的核心，见 FRAMEWORK.md。
    "sbc": (FLOW, ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"]),
    "buybacks": (
        FLOW,
        [
            "PaymentsForRepurchaseOfCommonStock",
            "TreasuryStockValueAcquiredCostMethod",
        ],
    ),
    "dividends_paid": (
        FLOW,
        ["PaymentsOfDividendsCommonStock", "PaymentsOfDividends"],
    ),
    "acquisitions": (
        FLOW,
        ["PaymentsToAcquireBusinessesNetOfCashAcquired", "PaymentsToAcquireBusinessesGross"],
    ),
    # ---------------- 资产负债表 ----------------
    "assets": (STOCK, ["Assets"]),
    # 用于最廉价的数据完整性护栏：资产 == 负债+权益。
    # 若拼表时把不同 end 日期的科目混在一起（并购、财年切换时极易发生），
    # 这个恒等式几乎必然被打破 —— 一行断言就能拦住一张"不存在的报表"。
    "liabilities_and_equity": (STOCK, ["LiabilitiesAndStockholdersEquity"]),
    "equity": (
        STOCK,
        [
            "StockholdersEquity",
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        ],
    ),
    "cash": (
        STOCK,
        [
            "CashAndCashEquivalentsAtCarryingValue",
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        ],
    ),
    # 有价证券必须分流动/非流动两段取，且**不能漏掉非流动那段**。
    # 实测苹果 FY2019：现金及等价物仅 488 亿，而 MarketableSecuritiesNoncurrent
    # 高达 1053 亿 —— 只取「现金 + 短期投资」会漏掉约千亿美元的净现金，
    # 直接击穿"扣掉净现金后它到底多贵"这条推理。
    # 另注：苹果的申报里**根本没有 ShortTermInvestments 这个标签**，用的是
    # MarketableSecuritiesCurrent —— 这正是必须给回退链而不是单标签的又一例证。
    # 回退链要覆盖三套命名习惯：ShortTerm* / MarketableSecurities* /
    # AvailableForSale*（或 DebtSecuritiesAvailableForSale*）。实测英伟达
    # FY2026 三套里只用第三套（`AvailableForSaleSecuritiesDebtSecurities*`
    # 合计 39.5B）—— 链子不全就会把这 39.5B 当成不存在，投入资本虚高、
    # ROIC 被系统性压低，而且返回的是个「看起来合理」的数字。
    "short_term_investments": (
        STOCK,
        [
            "ShortTermInvestments",
            "MarketableSecuritiesCurrent",
            "AvailableForSaleSecuritiesCurrent",
            "AvailableForSaleSecuritiesDebtSecuritiesCurrent",
            "DebtSecuritiesAvailableForSaleCurrent",
        ],
    ),
    "long_term_investments": (
        STOCK,
        [
            "MarketableSecuritiesNoncurrent",
            "LongTermInvestments",
            "AvailableForSaleSecuritiesNoncurrent",
            "AvailableForSaleSecuritiesDebtSecuritiesNoncurrent",
            "DebtSecuritiesAvailableForSaleNoncurrent",
        ],
    ),
    # 不带 Current/Noncurrent 后缀的**整体合计**标签，单列成一个概念。
    #
    # ⚠️ 它绝不能放进上面任何一条链的链尾。曾经那样做过，后果是：
    # 短期链命中 `MarketableSecuritiesCurrent`、长期链回退到这个**合计**标签，
    # 两者相加 → 流动那段被算了两遍。实测英伟达 FY2015 算出「超额现金 9.04B」，
    # 而它当年总资产只有 7.20B —— 数学上不可能，却不报错。
    # 正确用法见 metrics.excess_cash()：只在两条拆分链都落空时才用它，且只用一次。
    "total_investments": (STOCK, ["AvailableForSaleSecuritiesDebtSecurities", "AvailableForSaleSecurities"]),
    "receivables": (
        STOCK,
        ["AccountsReceivableNetCurrent", "ReceivablesNetCurrent", "AccountsAndOtherReceivablesNetCurrent"],
    ),
    "inventory": (STOCK, ["InventoryNet"]),
    "payables": (STOCK, ["AccountsPayableCurrent", "AccountsPayableAndAccruedLiabilitiesCurrent"]),
    "current_assets": (STOCK, ["AssetsCurrent"]),
    "current_liabilities": (STOCK, ["LiabilitiesCurrent"]),
    "goodwill": (STOCK, ["Goodwill"]),
    "intangibles": (STOCK, ["IntangibleAssetsNetExcludingGoodwill", "FiniteLivedIntangibleAssetsNet"]),
    "ppe_net": (STOCK, ["PropertyPlantAndEquipmentNet"]),
    # ⚠️ 有息负债**绝不能用回退链**，必须分项相加 —— 这是最容易静默算错的地方。
    #
    # 两个致命陷阱：
    #   (1) `LongTermDebt` 的定义**已经包含当期部分**。若把它和 `DebtCurrent`
    #       相加会重复计算长期负债的当期部分。实测 PEP@2025-12-27：
    #       LongTermDebt 46.351B、LongTermDebtNoncurrent 42.321B、DebtCurrent 6.861B
    #       —— 相加得 53.21B，真实有息负债只有 49.18B，虚增 8.2%。
    #   (2) 短期有息负债有**多个并列科目**（长期负债当期部分 / 短期借款 / 商业票据），
    #       用回退链只会取到其中一个。实测苹果同时有 LongTermDebtCurrent 与
    #       CommercialPaper，回退链会静默漏掉约 20 亿美元商业票据。
    #
    # 正确口径：TotalDebt = LongTermDebtNoncurrent + DebtCurrent
    #          （DebtCurrent 缺失时 = 长期负债当期部分 + 短期借款 + 商业票据）
    # 组装逻辑见 metrics.total_debt()。
    # 有些公司只申报一个**长短期合计**的总额标签，不做流动性拆分。
    # 实测甲骨文 FY2026 只有 `DebtLongtermAndShorttermCombinedAmount` = 129.54B，
    # 而 LongTermDebtNoncurrent / LongTermDebt 全部缺失 —— 若不覆盖这个标签，
    # 有息负债只会算出 DebtCurrent 的 7.20B，**漏掉约 1220 亿美元**，
    # 净负债从真实的约 1280 亿变成 55 亿，整个财务健康判断全反。
    # ⚠️ 它已含当期部分，因此在 metrics.total_debt() 里**独占**、不与分项相加。
    "debt_combined_total": (STOCK, ["DebtLongtermAndShorttermCombinedAmount"]),
    "debt_lt_noncurrent": (STOCK, ["LongTermDebtNoncurrent"]),
    "debt_lt_total": (STOCK, ["LongTermDebt"]),
    "debt_lt_current": (STOCK, ["LongTermDebtCurrent"]),
    "debt_current_total": (STOCK, ["DebtCurrent"]),
    "short_term_borrowings": (STOCK, ["ShortTermBorrowings", "OtherShortTermBorrowings"]),
    "commercial_paper": (STOCK, ["CommercialPaper"]),
    # 经营租赁负债：ASC 842 之后才有。不把它算进有息负债，会系统性低估
    # 零售 / 餐饮 / 航空这类"租来的重资产"生意的真实杠杆和投入资本。
    "lease_liab_long": (STOCK, ["OperatingLeaseLiabilityNoncurrent"]),
    "lease_liab_short": (STOCK, ["OperatingLeaseLiabilityCurrent"]),
    "lease_cost": (FLOW, ["OperatingLeaseCost", "LeaseCost"]),
    # ⚠️ 刻意**不含** `CommonStockSharesIssued` —— 已发行股数**含库存股**，
    # 与流通股不是一回事。实测摩根大通 Issued 常年恒为 4.105B（纹丝不动），
    # 而真实流通股是 2.696B，用它换算市值会高估 52%，逆向 DCF 的企业价值全错。
    "shares_outstanding": (STOCK, ["CommonStockSharesOutstanding"]),
}


# ⚠️ 这些概念的回退链**必须严格按顺序**，不能用「覆盖年份最多者为主标签」的策略。
#
# 原因：回退链里其实混着两类标签，它们的可替换性完全不同 ——
#   · **同义标签**（Revenues / SalesRevenueNet / RevenueFromContractWithCustomer…）
#     指同一个东西，只是准则或年代不同 → 可以按覆盖度选主，谁覆盖广用谁。
#   · **口径更窄的标签**（分项、含库存股、狭义 D&A…）
#     指的是**另一个东西** → 只能在首选缺失时勉强顶上，绝不能因为"它年份多"就上位。
#
# 把第二类当成第一类，就会得到一个「看起来合理、其实答非所问」的序列 ——
# 这正是本项目最想避免的那种错误。
STRICT_PRIORITY: set[str] = {
    "pretax_income",
    "shares_outstanding",
    "shares_diluted",
    "shares_basic",
    "d_and_a",
    "equity",
    "net_income",
    "debt_lt_noncurrent",
    "debt_current_total",
}


def chain(name: str) -> tuple[str, list[str]]:
    """取某个概念的 (kind, 回退链)。"""
    if name not in CONCEPTS:
        raise KeyError(f"未定义的概念 {name!r}。已定义：{sorted(CONCEPTS)}")
    return CONCEPTS[name]


# 银行 / 保险等金融机构在这套通用科目上必然缺失的项 —— 用于在报告里把
# 「结构上不适用」和「数据没取到」区分开。把两者混为一谈是分析事故的开始。
NA_FOR_FINANCIALS = {"gross_profit", "cogs", "operating_income", "inventory", "capex"}
