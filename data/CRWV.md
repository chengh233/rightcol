# CoreWeave, Inc. (CRWV) — 确定性数据包

数据源：SEC EDGAR XBRL（申报原始口径，未经任何调整）· 财年数 3 · 最新财年止 **2025-12-31**

> 本文件只有数字，没有判断。判断请对照 `FRAMEWORK.md` 的三个闸门自行做出。
> 缺失一律显示 `—`，**绝不以 0 填充**——数据中断必须长得像数据中断。

## ⏱ 最新四个季度 · TTM

> 年报止 2025-12-31，最新季末 **2026-03-31**（新 90 天）。

| 季末 | 营收 | 环比 | 同比 | 毛利率 | 营业利润率 | 营业成本 | 存货/营收 | FCF |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-06-30 | 0.4B | 109.5% | — | 72.5% | 19.7% | 0.1B | — | -2.4B |
| 2024-09-30 | 0.6B | 47.7% | — | 75.5% | 20.1% | 0.1B | — | -0.6B |
| 2024-12-31 | 0.7B | 27.9% | — | 75.7% | 15.0% | 0.2B | — | -3.3B |
| 2025-03-31 | 1.0B | 31.5% | 420.4% | 73.3% | -2.7% | 0.3B | — | -1.3B |
| 2025-06-30 | 1.2B | 23.5% | 206.7% | 74.2% | 1.6% | 0.3B | — | -2.7B |
| 2025-09-30 | 1.4B | 12.5% | 133.7% | 73.0% | 3.8% | 0.4B | — | -0.7B |
| 2025-12-31 | 1.6B | 15.2% | 110.4% | 67.6% | -5.7% | 0.5B | — | -2.5B |
| 2026-03-31 | 2.1B | 32.2% | 111.6% | 65.5% | -6.9% | 0.7B | — | -4.7B |

| TTM（最近四季合计） | 营收 | 净利润 | 自由现金流 |
| --- | --- | --- | --- |
| **TTM** | 6.2B | -1.6B | -10.6B |
| 最新完整财年 | 5.1B | -1.2B | -7.3B |
| 差异 | 21.4% | 36.4% | 46.4% |

**怎么读**（详见 FRAMEWORK.md §5.8「季度视角」的四个动作）：

1. **拆价与量** —— 比较**营收**与**营业成本**的增速。成本不动而收入暴涨，
   说明增量几乎全是**价格**，而价格驱动的增长会引来供给、均值回归。
   实测 Micron：营收 +377% 而营业成本仅 +19%。
2. **看存货** —— 这里用 **存货/营收** 而非存货天数：价格暴涨时毛利率飙升、
   成本占比骤降，会让存货天数**假性上升**（实测 SanDisk 从 121「升」到 158，
   而存货绝对额是平的、存货/营收其实从 65% 降到 38%）。
3. **环比比同比先出信号** —— 对斜率陡峭的公司，同比会掩盖拐点。
   实测 AMD：同比仍 +37.8%，环比已 −0.2%。
4. **TTM 与最新财年差异越大**，年报视图越不能代表当下。

⚠️ 口径说明：**10-Q 里的现金流量表是年初至今累计的**，本项目用相邻累计值
相减还原单季；财年最后一季不在任何 10-Q 里，用「全年 − 前三季」倒推。
两类还原值在第七节的口径留痕里带 `+derived` 后缀。

## 一、赚不赚钱 · 盈利能力与资本回报

| 财年止 | 营收 | 营收YoY | 毛利率 | 营业利润率 | 净利率 | ROIC | ROE | 增量ROIC(5y) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-12-31 †💰 | 0.2B | — | 69.9% | -6.1% | -259.4% | — | 99.5% | — |
| 2024-12-31 ✂️†💰 | 1.9B | 736.2% | 74.3% | 16.9% | -45.1% | — | 170.7% | — |
| 2025-12-31 ✂️†💰 | 5.1B | 167.9% | 71.7% | -0.9% | -22.7% | 1.6% | -79.9% | — |

**数据完整性标注**：

- † **有效税率异常**（亏损年或一次性税务事项），NOPAT 与 ROIC 使用了21% 法定税率**假设**，不是该年实际税率。
  涉及财年：2023-12-31, 2024-12-31, 2025-12-31
- 💰 **净利润的三成以上不是经营赚来的** —— 非经营损益（多为股权投资的公允价值重估、处置收益）占税前利润超过 30%。ASU 2016-01 之后股权投资的**未实现**增值直接计入净利润，是非现金的。此时**净利率 / ROE / PE 全部失真**，请改看营业利润与自由现金流。
  涉及财年：2023-12-31, 2024-12-31, 2025-12-31
- ✂️ **营收同比剧变（±80% 以上）** —— 请回原文确认这是真实经营变化，还是**业务重组 / 分拆 / 并购**导致的口径断裂。若是后者，**任何跨越该年的 CAGR、趋势与平均值都无意义**。（实测 Nebius 2022 年 −99.7% 是剥离俄罗斯业务；CoreWeave 2024 年 +736% 则是真实增长——所以这只是提示，不是判定。）
  涉及财年：2024-12-31, 2025-12-31

> ROIC 显示 `—` 的年份，多数是**投入资本为负**（超额现金超过有息负债+账面权益，
> 常见于常年巨额回购 + 持有巨量有价证券的公司）。此时 ROIC 在数学上无意义，
> 本项目返回 `—` 而不是一个看起来像数的垃圾值。

**怎么读**：ROIC 是判断生意质地最核心的单一数字，但它必须和**资本成本**比——
ROIC 低于资本成本时，增长得越快毁灭的价值越多。增量 ROIC 比存量 ROIC 更能预测未来：
存量高可能只是十年前那笔投资的遗产，增量才回答「现在新投的钱回报如何」。

## 二、靠什么赚 · 杜邦拆解

| 财年止 | 净利率 | 资产周转率 | 权益乘数 | = ROE |
| --- | --- | --- | --- | --- |
| 2023-12-31 | -259.4% | — | — | 99.5% |
| 2024-12-31 | -45.1% | 0.11× | -35.28× | 170.7% |
| 2025-12-31 | -22.7% | 0.15× | 22.98× | -79.9% |

**怎么读**：同一个 ROE 背后可以是三种完全不同的生意——
高净利率低周转＝品牌/专利型；低净利率高周转＝效率型；靠权益乘数堆出来的＝杠杆型。
**杠杆型的 ROE 最脆弱**：杠杆在顺境放大收益，在逆境放大的是破产概率。

## 三、赚的是不是真钱 · 现金质量

| 财年止 | 净利润 | 经营现金流 | OCF/净利 | 资本开支 | 自由现金流 | FCF(扣SBC) | 应计比率 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-12-31 | -0.6B | 1.8B | -3.09× | 2.9B | -1.1B | -1.1B | — |
| 2024-12-31 | -0.9B | 2.7B | -3.19× | 8.7B | -6.0B | -6.0B | -20.3% |
| 2025-12-31 | -1.2B | 3.1B | -2.62× | 10.3B | -7.3B | -7.9B | -12.6% |

**怎么读**：利润是观点，现金是事实。但 **OCF/净利润 不是可靠的单一警报**——
股权激励与折旧都要加回经营现金流，会把科技公司和重资产公司的这个比值
**结构性抬高**，两类恰恰都是你想警惕的对象。

真正有鉴别力的是右侧两列：**FCF(扣SBC)** 与 **应计比率**，加上第五节的摊薄股数变化。
应计比率经验带：< 0 优秀 · 0~5% 正常 · > 10% 需要解释 · 连续多年 > 10% 是红旗。
（高速扩张期营运资本自然膨胀，应计天然偏高，须与自身历史和同业比。）

## 四、产业链话语权 · 现金转换周期

| 财年止 | DSO 应收天数 | DIO 存货天数 | DPO 付款天数 | CCC 现金周期 |
| --- | --- | --- | --- | --- |
| 2023-12-31 | — | — | — | — |
| 2024-12-31 | 79 | — | 643 | — |
| 2025-12-31 | 128 | — | 313 | — |

**怎么读**：CCC 为负＝**先收钱后付货款**，等于免费占用上下游资金做生意，
是产业链话语权极强的证据。DSO / DIO 增速持续快于营收增速，是渠道压货或需求转弱的**早期**信号——
它通常比营收下滑早出现一到两个季度。

## 五、赚的钱归谁 · 资本配置

| 财年止 | SBC | SBC/毛利 | 回购 | 回购/SBC | 摊薄股数 | 净稀释率 | 分红 | 资本开支/折旧 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-12-31 | 0.0B | 9.4% | — | — | 192M | — | — | 28.57× |
| 2024-12-31 | 0.0B | 2.2% | 0.0B | 0.06× | 218M | 13.5% | — | 10.08× |
| 2025-12-31 | 0.6B | 17.1% | — | — | 436M | 100.0% | — | 4.20× |

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
| 2023-12-31 | — | -0.6B | — | 0.5B | — | — | -0.0% |
| 2024-12-31 | 17.8B | -0.4B | 10.5B | 2.1B | 8.5B | -1.42× | -4.8% |
| 2025-12-31 | 49.3B | 3.3B | 29.6B | 4.2B | 25.4B | -3.50× | 33.0% |

**怎么读**：净负债/FCF 是「不吃不喝几年能还清」。>4× 就要认真看到期结构。
商誉/权益高，意味着账面净资产里很大一块是过去并购付出的溢价——**它只会减值，不会增值**。

## 七、口径留痕（跨公司比较前必读）

最新财年各科目实际命中的 us-gaap 标签：

```
acquisitions             PaymentsToAcquireBusinessesNetOfCashAcquired
amort_intangibles        AmortizationOfIntangibleAssets
assets                   Assets
capex                    PaymentsToAcquirePropertyPlantAndEquipment
cash                     CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents
cogs                     CostOfGoodsAndServicesSold
current_assets           AssetsCurrent
current_liabilities      LiabilitiesCurrent
d_and_a                  DepreciationDepletionAndAmortization
debt_lt_current          LongTermDebtCurrent
debt_lt_noncurrent       LongTermDebtNoncurrent
debt_lt_total            LongTermDebt
eps_diluted              EarningsPerShareDiluted
equity                   StockholdersEquity
goodwill                 Goodwill
intangibles              IntangibleAssetsNetExcludingGoodwill
interest_expense         InterestExpenseDebt
lease_cost               OperatingLeaseCost
lease_liab_long          OperatingLeaseLiabilityNoncurrent
lease_liab_short         OperatingLeaseLiabilityCurrent
liabilities_and_equity   LiabilitiesAndStockholdersEquity
long_term_investments    AvailableForSaleSecuritiesDebtSecuritiesNoncurrent
net_income               NetIncomeLoss
ocf                      NetCashProvidedByUsedInOperatingActivities
operating_income         OperatingIncomeLoss
payables                 AccountsPayableCurrent
ppe_net                  PropertyPlantAndEquipmentNet
pretax_income            IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest
receivables              AccountsReceivableNetCurrent
revenue                  RevenueFromContractWithCustomerExcludingAssessedTax
rnd                      ResearchAndDevelopmentExpense
sbc                      ShareBasedCompensation
sgna                     GeneralAndAdministrativeExpense
shares_basic             WeightedAverageNumberOfSharesOutstandingBasic
shares_diluted           WeightedAverageNumberOfDilutedSharesOutstanding
short_term_investments   MarketableSecuritiesCurrent
tax_expense              IncomeTaxExpenseBenefit
```

⚠️ 最新财年缺失：`gross_profit`, `inventory`。
若这是金融机构（银行/保险），**这些科目是结构性不存在，不是数据缺失**——
对它套用毛利率、周转率、FCF 会得到纯噪音，须改用 NIM / 拨备覆盖 / 资本充足率等专用指标。
