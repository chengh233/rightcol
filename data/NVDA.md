# NVIDIA CORP (NVDA) — 确定性数据包

数据源：SEC EDGAR XBRL（申报原始口径，未经任何调整）· 财年数 8 · 最新财年止 **2026-01-25**

> 本文件只有数字，没有判断。判断请对照 `FRAMEWORK.md` 的三个闸门自行做出。
> 缺失一律显示 `—`，**绝不以 0 填充**——数据中断必须长得像数据中断。

## 一、赚不赚钱 · 盈利能力与资本回报

| 财年止 | 营收 | 营收YoY | 毛利率 | 营业利润率 | 净利率 | ROIC | ROE | 增量ROIC(5y) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-01-27 † | 11.7B | — | 61.2% | 32.5% | 35.3% | 76.9% | 44.3% | — |
| 2020-01-26 | 10.9B | -6.8% | 62.0% | 26.1% | 25.6% | 69.0% | 26.0% | — |
| 2021-01-31 | 16.7B | 52.7% | 62.3% | 27.2% | 26.0% | 52.8% | 29.8% | — |
| 2022-01-30 | 26.9B | 61.4% | 64.9% | 37.3% | 36.2% | 65.3% | 44.8% | — |
| 2023-01-29 † | 27.0B | 0.2% | 56.9% | 15.7% | 16.2% | 17.8% | 17.9% | — |
| 2024-01-28 ∞ | 60.9B | 125.9% | 72.7% | 54.1% | 48.8% | 118.9% | 91.5% | 108.0% |
| 2025-01-26 ∞ | 130.5B | 114.2% | 75.0% | 62.4% | 55.8% | 190.0% | 119.2% | 160.3% |
| 2026-01-25 ∞ | 215.9B | 65.5% | 71.1% | 60.4% | 55.6% | 134.3% | 101.5% | 100.7% |

**数据完整性标注**：

- † **有效税率异常**（亏损年或一次性税务事项），NOPAT 与 ROIC 使用了21% 法定税率**假设**，不是该年实际税率。
  涉及财年：2019-01-27, 2023-01-29
- ∞ **ROIC > 100%**：轻资产 + 负营运资本使投入资本极小。这个数真实但**已失去鉴别力**（分母接近零，微小口径变化就能让它剧烈摆动），请改看自由现金流的绝对额与增长的持续性。
  涉及财年：2024-01-28, 2025-01-26, 2026-01-25

> ROIC 显示 `—` 的年份，多数是**投入资本为负**（超额现金超过有息负债+账面权益，
> 常见于常年巨额回购 + 持有巨量有价证券的公司）。此时 ROIC 在数学上无意义，
> 本项目返回 `—` 而不是一个看起来像数的垃圾值。

**怎么读**：ROIC 是判断生意质地最核心的单一数字，但它必须和**资本成本**比——
ROIC 低于资本成本时，增长得越快毁灭的价值越多。增量 ROIC 比存量 ROIC 更能预测未来：
存量高可能只是十年前那笔投资的遗产，增量才回答「现在新投的钱回报如何」。

## 二、靠什么赚 · 杜邦拆解

| 财年止 | 净利率 | 资产周转率 | 权益乘数 | = ROE |
| --- | --- | --- | --- | --- |
| 2019-01-27 | 35.3% | 0.88× | 1.42× | 44.3% |
| 2020-01-26 | 25.6% | 0.71× | 1.42× | 26.0% |
| 2021-01-31 | 26.0% | 0.72× | 1.58× | 29.8% |
| 2022-01-30 | 36.2% | 0.74× | 1.68× | 44.8% |
| 2023-01-29 | 16.2% | 0.63× | 1.75× | 17.9% |
| 2024-01-28 | 48.8% | 1.14× | 1.64× | 91.5% |
| 2025-01-26 | 55.8% | 1.47× | 1.45× | 119.2% |
| 2026-01-25 | 55.6% | 1.36× | 1.35× | 101.5% |

**怎么读**：同一个 ROE 背后可以是三种完全不同的生意——
高净利率低周转＝品牌/专利型；低净利率高周转＝效率型；靠权益乘数堆出来的＝杠杆型。
**杠杆型的 ROE 最脆弱**：杠杆在顺境放大收益，在逆境放大的是破产概率。

## 三、赚的是不是真钱 · 现金质量

| 财年止 | 净利润 | 经营现金流 | OCF/净利 | 资本开支 | 自由现金流 | FCF(扣SBC) | 应计比率 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-01-27 | 4.1B | 3.7B | 0.90× | — | — | — | 3.0% |
| 2020-01-26 | 2.8B | 4.8B | 1.70× | — | — | — | -12.8% |
| 2021-01-31 | 4.3B | 5.8B | 1.34× | — | — | — | -6.5% |
| 2022-01-30 | 9.8B | 9.1B | 0.93× | 1.0B | 8.1B | 6.1B | 1.8% |
| 2023-01-29 | 4.4B | 5.6B | 1.29× | 1.8B | 3.8B | 1.1B | -3.0% |
| 2024-01-28 | 29.8B | 28.1B | 0.94× | 1.1B | 27.0B | 23.5B | 3.1% |
| 2025-01-26 | 72.9B | 64.1B | 0.88× | 3.2B | 60.9B | 56.1B | 9.9% |
| 2026-01-25 | 120.1B | 102.7B | 0.86× | 6.0B | 96.7B | 90.3B | 10.9% |

**怎么读**：利润是观点，现金是事实。但 **OCF/净利润 不是可靠的单一警报**——
股权激励与折旧都要加回经营现金流，会把科技公司和重资产公司的这个比值
**结构性抬高**，两类恰恰都是你想警惕的对象。

真正有鉴别力的是右侧两列：**FCF(扣SBC)** 与 **应计比率**，加上第五节的摊薄股数变化。
应计比率经验带：< 0 优秀 · 0~5% 正常 · > 10% 需要解释 · 连续多年 > 10% 是红旗。
（高速扩张期营运资本自然膨胀，应计天然偏高，须与自身历史和同业比。）

## 四、产业链话语权 · 现金转换周期

| 财年止 | DSO 应收天数 | DIO 存货天数 | DPO 付款天数 | CCC 现金周期 |
| --- | --- | --- | --- | --- |
| 2019-01-27 | 44 | 126 | 41 | 130 |
| 2020-01-26 | 52 | 112 | 53 | 111 |
| 2021-01-31 | 45 | 82 | 53 | 73 |
| 2022-01-30 | 48 | 86 | 57 | 77 |
| 2023-01-29 | 57 | 122 | 47 | 133 |
| 2024-01-28 | 41 | 115 | 43 | 113 |
| 2025-01-26 | 46 | 86 | 50 | 82 |
| 2026-01-25 | 52 | 92 | 47 | 97 |

**怎么读**：CCC 为负＝**先收钱后付货款**，等于免费占用上下游资金做生意，
是产业链话语权极强的证据。DSO / DIO 增速持续快于营收增速，是渠道压货或需求转弱的**早期**信号——
它通常比营收下滑早出现一到两个季度。

## 五、赚的钱归谁 · 资本配置

| 财年止 | SBC | SBC/毛利 | 回购 | 回购/SBC | 摊薄股数 | 净稀释率 | 分红 | 资本开支/折旧 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-01-27 | 0.6B | 7.8% | 1.6B | 2.83× | 625M | — | 0.4B | — |
| 2020-01-26 | 0.8B | 12.5% | 0.0B | 0.00× | 2,472M | 295.5% | 0.4B | — |
| 2021-01-31 | 1.4B | 13.4% | 0.0B | 0.00× | 2,510M | 1.5% | 0.4B | — |
| 2022-01-30 | 2.0B | 11.5% | 0.0B | 0.00× | 2,535M | 1.0% | 0.4B | 0.83× |
| 2023-01-29 | 2.7B | 17.6% | 10.0B | 3.71× | 25,070M | 889.0% | 0.4B | 1.19× |
| 2024-01-28 | 3.5B | 8.0% | 9.5B | 2.69× | 24,940M | -0.5% | 0.4B | 0.71× |
| 2025-01-26 | 4.7B | 4.8% | 33.7B | 7.12× | 24,804M | -0.5% | 0.8B | 1.74× |
| 2026-01-25 | 6.4B | 4.2% | 40.1B | 6.28× | 24,514M | -1.2% | 1.0B | 2.13× |

**怎么读**：**摊薄股数与净稀释率是股权激励伤害股东最直接、最难粉饰的证据** ——
净稀释率为正说明股东在被稀释，为负说明回购真正减少了股本。
⚠️ 拆股会污染这条序列（申报值是拆股前原始数字，不做追溯调整），
看到 ±数百% 的跳变先查是不是拆股，不要当成稀释。

**回购/SBC > 1 才是真回购**；≈1 只是在抵消股权激励的稀释；<1 是净稀释。
SBC 的分母用**毛利**而非营收 —— 营收口径会被毛利率结构污染，
90% 毛利的软件公司和 25% 毛利的硬件公司不可直接比。
资本开支/折旧 长期 < 1 说明公司在吃老本（产能在萎缩）；持续 > 1.5 是扩张期，要问回报率。
并购支出大而增量 ROIC 低，是资本配置失败最典型的组合。

## 六、会不会突然死 · 财务健康

| 财年止 | 总资产 | 股东权益 | 有息负债(含租赁) | 现金+短投 | 净负债 | 净负债/FCF | 商誉/权益 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2019-01-27 | 13.3B | 9.3B | 2.0B | 7.4B | -5.4B | — | 6.6% |
| 2020-01-26 | 17.3B | 12.2B | 2.6B | 10.9B | -8.3B | — | 5.1% |
| 2021-01-31 | 28.8B | 16.9B | 7.7B | 11.6B | -3.8B | — | 24.8% |
| 2022-01-30 | 44.2B | 26.6B | 11.8B | 21.2B | -9.4B | -1.15× | 16.3% |
| 2023-01-29 | 41.2B | 22.1B | 12.0B | 13.3B | -1.3B | -0.33× | 19.8% |
| 2024-01-28 | 65.7B | 43.0B | 11.1B | 26.0B | -14.9B | -0.55× | 10.3% |
| 2025-01-26 | 111.6B | 79.3B | 10.3B | 43.2B | -32.9B | -0.54× | 6.5% |
| 2026-01-25 | 206.8B | 157.3B | 11.4B | 50.1B | -38.7B | -0.40× | 13.2% |

**怎么读**：净负债/FCF 是「不吃不喝几年能还清」。>4× 就要认真看到期结构。
商誉/权益高，意味着账面净资产里很大一块是过去并购付出的溢价——**它只会减值，不会增值**。

## 七、口径留痕（跨公司比较前必读）

最新财年各科目实际命中的 us-gaap 标签：

```
acquisitions             PaymentsToAcquireBusinessesNetOfCashAcquired
amort_intangibles        AmortizationOfIntangibleAssets
assets                   Assets
buybacks                 PaymentsForRepurchaseOfCommonStock
capex                    PaymentsToAcquireProductiveAssets
cash                     CashAndCashEquivalentsAtCarryingValue
cogs                     CostOfRevenue
current_assets           AssetsCurrent
current_liabilities      LiabilitiesCurrent
d_and_a                  DepreciationDepletionAndAmortization
debt_current_total       DebtCurrent
debt_lt_current          LongTermDebtCurrent
debt_lt_noncurrent       LongTermDebtNoncurrent
debt_lt_total            LongTermDebt
dividends_paid           PaymentsOfDividends
eps_diluted              EarningsPerShareDiluted
equity                   StockholdersEquity
goodwill                 Goodwill
gross_profit             GrossProfit
intangibles              IntangibleAssetsNetExcludingGoodwill
inventory                InventoryNet
lease_cost               OperatingLeaseCost
lease_liab_long          OperatingLeaseLiabilityNoncurrent
lease_liab_short         OperatingLeaseLiabilityCurrent
liabilities_and_equity   LiabilitiesAndStockholdersEquity
net_income               NetIncomeLoss
ocf                      NetCashProvidedByUsedInOperatingActivities
operating_income         OperatingIncomeLoss
payables                 AccountsPayableCurrent
ppe_net                  PropertyPlantAndEquipmentNet
pretax_income            IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest
receivables              AccountsReceivableNetCurrent
revenue                  Revenues
rnd                      ResearchAndDevelopmentExpense
sbc                      ShareBasedCompensation
sgna                     SellingGeneralAndAdministrativeExpense
shares_basic             WeightedAverageNumberOfSharesOutstandingBasic
shares_diluted           WeightedAverageNumberOfDilutedSharesOutstanding
shares_outstanding       CommonStockSharesOutstanding
tax_expense              IncomeTaxExpenseBenefit
total_investments        AvailableForSaleSecuritiesDebtSecurities
```
