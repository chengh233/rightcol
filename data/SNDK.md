# Sandisk Corporation (SNDK) — 确定性数据包

数据源：SEC EDGAR XBRL（申报原始口径，未经任何调整）· 财年数 3 · 最新财年止 **2025-06-27**

> 本文件只有数字，没有判断。判断请对照 `FRAMEWORK.md` 的三个闸门自行做出。
> 缺失一律显示 `—`，**绝不以 0 填充**——数据中断必须长得像数据中断。

## ⏱ 最新四个季度 · TTM

> 🔴 **年报视图已过期 280 天**（最新财年止 2025-06-27，最新季末 2026-04-03）。
> **对周期股这是致命的** —— 下面所有年度表格反映的可能是完全不同的经营状态，
> 请以本节的 TTM 与季度趋势为准。

| 季末 | 营收 | 营收YoY | 毛利率 | 营业利润率 | 净利润 | 经营现金流 | 资本开支 | FCF |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-06-28 | 1.8B | — | 36.1% | 11.3% | 0.1B | -0.1B | 0.0B | -0.2B |
| 2024-09-27 | 1.9B | — | 38.6% | 15.5% | 0.2B | -0.1B | 0.1B | -0.2B |
| 2024-12-27 | 1.9B | 12.7% | 32.3% | 10.4% | 0.1B | 0.1B | 0.0B | 0.0B |
| 2025-03-28 | 1.7B | -0.6% | 22.5% | -111.0% | -1.9B | 0.0B | 0.0B | -0.0B |
| 2025-06-27 | 1.9B | 8.0% | 26.2% | 0.9% | -0.0B | 0.1B | 0.0B | 0.0B |
| 2025-10-03 | 2.3B | 22.6% | 29.8% | 7.6% | 0.1B | 0.5B | 0.1B | 0.4B |
| 2026-01-02 | 3.0B | 61.2% | 50.9% | 35.2% | 0.8B | 1.0B | 0.0B | 1.0B |
| 2026-04-03 | 6.0B | 251.0% | 78.4% | 69.1% | 3.6B | 3.0B | 0.0B | 3.0B |

| TTM（最近四季合计） | 营收 | 净利润 | 自由现金流 |
| --- | --- | --- | --- |
| **TTM** | 13.2B | 4.5B | 4.5B |
| 最新完整财年 | 7.4B | -1.6B | -0.1B |
| 差异 | 79.3% | -374.6% | -3816.7% |

**怎么读**：季度同比用的是**四个季度前**同期，不是环比——季节性会淹没趋势。
TTM 与最新财年的差异越大，说明年报视图越不能代表当下。

⚠️ 口径说明：**10-Q 里的现金流量表是年初至今累计的**，本项目用相邻累计值
相减还原单季；财年最后一季不在任何 10-Q 里，用「全年 − 前三季」倒推。
两类还原值在第七节的口径留痕里带 `+derived` 后缀。

## 一、赚不赚钱 · 盈利能力与资本回报

| 财年止 | 营收 | 营收YoY | 毛利率 | 营业利润率 | 净利率 | ROIC | ROE | 增量ROIC(5y) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-06-30 † | 6.1B | — | 7.1% | -33.4% | -35.2% | -14.4% | -18.7% | — |
| 2024-06-28 † | 6.7B | 9.5% | 16.1% | -7.0% | -10.1% | -3.3% | -6.0% | — |
| 2025-06-27 † | 7.4B | 10.4% | 30.1% | -18.7% | -22.3% | -10.4% | -16.2% | — |

**数据完整性标注**：

- † **有效税率异常**（亏损年或一次性税务事项），NOPAT 与 ROIC 使用了21% 法定税率**假设**，不是该年实际税率。
  涉及财年：2023-06-30, 2024-06-28, 2025-06-27

> ROIC 显示 `—` 的年份，多数是**投入资本为负**（超额现金超过有息负债+账面权益，
> 常见于常年巨额回购 + 持有巨量有价证券的公司）。此时 ROIC 在数学上无意义，
> 本项目返回 `—` 而不是一个看起来像数的垃圾值。

**怎么读**：ROIC 是判断生意质地最核心的单一数字，但它必须和**资本成本**比——
ROIC 低于资本成本时，增长得越快毁灭的价值越多。增量 ROIC 比存量 ROIC 更能预测未来：
存量高可能只是十年前那笔投资的遗产，增量才回答「现在新投的钱回报如何」。

## 二、靠什么赚 · 杜邦拆解

| 财年止 | 净利率 | 资产周转率 | 权益乘数 | = ROE |
| --- | --- | --- | --- | --- |
| 2023-06-30 | -35.2% | — | — | -18.7% |
| 2024-06-28 | -10.1% | 0.49× | 1.20× | -6.0% |
| 2025-06-27 | -22.3% | 0.56× | 1.31× | -16.2% |

**怎么读**：同一个 ROE 背后可以是三种完全不同的生意——
高净利率低周转＝品牌/专利型；低净利率高周转＝效率型；靠权益乘数堆出来的＝杠杆型。
**杠杆型的 ROE 最脆弱**：杠杆在顺境放大收益，在逆境放大的是破产概率。

## 三、赚的是不是真钱 · 现金质量

| 财年止 | 净利润 | 经营现金流 | OCF/净利 | 资本开支 | 自由现金流 | FCF(扣SBC) | 应计比率 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-06-30 | -2.1B | -0.7B | 0.33× | 0.2B | -0.9B | -1.1B | — |
| 2024-06-28 | -0.7B | -0.3B | 0.46× | 0.2B | -0.5B | -0.6B | -2.7% |
| 2025-06-27 | -1.6B | 0.1B | -0.05× | 0.2B | -0.1B | -0.3B | -13.0% |

**怎么读**：利润是观点，现金是事实。但 **OCF/净利润 不是可靠的单一警报**——
股权激励与折旧都要加回经营现金流，会把科技公司和重资产公司的这个比值
**结构性抬高**，两类恰恰都是你想警惕的对象。

真正有鉴别力的是右侧两列：**FCF(扣SBC)** 与 **应计比率**，加上第五节的摊薄股数变化。
应计比率经验带：< 0 优秀 · 0~5% 正常 · > 10% 需要解释 · 连续多年 > 10% 是红旗。
（高速扩张期营运资本自然膨胀，应计天然偏高，须与自身历史和同业比。）

## 四、产业链话语权 · 现金转换周期

| 财年止 | DSO 应收天数 | DIO 存货天数 | DPO 付款天数 | CCC 现金周期 |
| --- | --- | --- | --- | --- |
| 2023-06-30 | — | — | — | — |
| 2024-06-28 | 51 | 128 | — | — |
| 2025-06-27 | 50 | 143 | — | — |

**怎么读**：CCC 为负＝**先收钱后付货款**，等于免费占用上下游资金做生意，
是产业链话语权极强的证据。DSO / DIO 增速持续快于营收增速，是渠道压货或需求转弱的**早期**信号——
它通常比营收下滑早出现一到两个季度。

## 五、赚的钱归谁 · 资本配置

| 财年止 | SBC | SBC/毛利 | 回购 | 回购/SBC | 摊薄股数 | 净稀释率 | 分红 | 资本开支/折旧 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-06-30 | 0.2B | 38.4% | — | — | 145M | — | — | 0.38× |
| 2024-06-28 | 0.1B | 13.9% | — | — | 145M | 0.0% | — | 0.74× |
| 2025-06-27 | 0.2B | 8.2% | — | — | 145M | 0.0% | — | 1.25× |

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
| 2023-06-30 | — | 11.4B | — | 0.3B | — | — | — |
| 2024-06-28 | 13.5B | 11.1B | 0.2B | 0.3B | -0.1B | 0.31× | 65.0% |
| 2025-06-27 | 13.0B | 9.2B | 2.1B | 1.5B | 0.6B | -4.89× | 54.2% |

**怎么读**：净负债/FCF 是「不吃不喝几年能还清」。>4× 就要认真看到期结构。
商誉/权益高，意味着账面净资产里很大一块是过去并购付出的溢价——**它只会减值，不会增值**。

## 七、口径留痕（跨公司比较前必读）

最新财年各科目实际命中的 us-gaap 标签：

```
assets                   Assets
capex                    PaymentsToAcquirePropertyPlantAndEquipment
cash                     CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents
cogs                     CostOfGoodsAndServicesSold
current_assets           AssetsCurrent
current_liabilities      LiabilitiesCurrent
d_and_a                  DepreciationAndAmortization
debt_lt_current          LongTermDebtCurrent
debt_lt_noncurrent       LongTermDebtNoncurrent
debt_lt_total            LongTermDebt
eps_diluted              EarningsPerShareDiluted
equity                   StockholdersEquity
goodwill                 Goodwill
gross_profit             GrossProfit
inventory                InventoryNet
lease_cost               OperatingLeaseCost
lease_liab_long          OperatingLeaseLiabilityNoncurrent
lease_liab_short         OperatingLeaseLiabilityCurrent
liabilities_and_equity   LiabilitiesAndStockholdersEquity
net_income               NetIncomeLoss
ocf                      NetCashProvidedByUsedInOperatingActivities
operating_income         OperatingIncomeLoss
ppe_net                  PropertyPlantAndEquipmentNet
pretax_income            IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest
receivables              AccountsReceivableNetCurrent
revenue                  RevenueFromContractWithCustomerExcludingAssessedTax
rnd                      ResearchAndDevelopmentExpense
sbc                      ShareBasedCompensation
sgna                     SellingGeneralAndAdministrativeExpense
shares_basic             WeightedAverageNumberOfSharesOutstandingBasic
shares_diluted           WeightedAverageNumberOfDilutedSharesOutstanding
shares_outstanding       CommonStockSharesOutstanding
tax_expense              IncomeTaxExpenseBenefit
```

## 八、10-K 原文（精读层入口）

- 2025-08-21（报告期 2025-06-27）— https://www.sec.gov/Archives/edgar/data/2023554/000202355425000034/sndk-20250627.htm

数字之外，这些地方性价比最高：**风险因素的逐年 diff**（新增/删除了什么）、MD&A 里管理层对变化的解释、附注中的分部数据与客户集中度、以及会计政策变更。措辞的变化常常比财务指标更早反映问题。
