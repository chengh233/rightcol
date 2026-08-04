# 名词表 —— 第一次读财报之前先看这个

> 财报晦涩，一半是因为不知道该问什么（那是 [`FRAMEWORK.md`](FRAMEWORK.md) 解决的），
> **另一半纯粹是因为术语**。这份表解决后一半。
>
> 用法：不用背。遇到看不懂的词回来查，查几次就记住了。

---

# 一、SEC 申报文件类型

美国公司必须向 **SEC（Securities and Exchange Commission，美国证券交易委员会）**
申报，所有文件公开在 **EDGAR** 数据库里。本项目的数据全部来自这里。

编号体系没有规律（历史遗留），只能记常用的几个。
**注意：不存在 "16-K" 这种文件。**

## 1.1 定期报告 —— 按时间表必须交的

| 编号 | 全称 | 中文 | 谁交 | 频率 |
|---|---|---|---|---|
| **10-K** | Annual Report | **年报** | 美国本土公司 | 每年一次 |
| **10-Q** | Quarterly Report | **季报** | 美国本土公司 | 每年**三次**（Q1/Q2/Q3）|
| **20-F** | Annual Report (Foreign Private Issuer) | 外国发行人年报 | 非美国公司 | 每年一次 |
| **40-F** | Annual Report (Canadian) | 加拿大发行人年报 | 加拿大公司 | 每年一次 |
| **11-K** | Annual Report of Employee Plans | 员工持股计划年报 | 有员工持股计划的公司 | 每年一次 |

> ⚠️ **10-Q 只有三份，没有 Q4。** 第四季度的数据**只出现在 10-K 里**，
> 而 10-K 报的是全年 —— 所以单独的 Q4 必须用「全年 − 前三季」倒推。
> 本项目的 `edgar.derive_q4()` 就在做这件事。

> ⚠️ **20-F 与 10-K 的差别不只是表格号**：外国发行人可以用 **IFRS**
> （International Financial Reporting Standards，国际财务报告准则）
> 而不是 **US GAAP**（Generally Accepted Accounting Principles，美国通用会计准则），
> 会计口径不同，跨公司比较要小心。Nebius 就是 20-F 申报人。

## 1.2 临时报告 —— 有大事随时交

| 编号 | 全称 | 中文 | 谁交 |
|---|---|---|---|
| **8-K** | Current Report | **重大事件即时报告** | 美国本土公司 |
| **6-K** | Report of Foreign Private Issuer | 外国发行人临时报告 | 非美国公司 |

**8-K 用 Item 编号说明"发生了什么事"，最值得记的几个：**

| Item | 含义 | 对投资者的意义 |
|---|---|---|
| 1.01 / 1.02 | 订立 / 终止重大协议 | 大合同签了或黄了 |
| 2.01 | 完成收购或处置资产 | 并购、分拆 |
| **2.02** | **Results of Operations —— 业绩发布** | ⭐ **财报季最重要的一个**，比 10-Q 早几天到两周 |
| 2.03 | 产生重大债务义务 | 新借了大钱 |
| 2.04 | 债务加速到期 | 🔴 可能违约 |
| 3.01 | 不符合上市规则 | 🔴 退市风险 |
| **4.01** | **会计师变更** | 🔴 **红旗**（见 FRAMEWORK §9）|
| **4.02** | **前期财务报表不可依赖** | 🔴🔴 **财务重述，最严重的红旗之一** |
| 5.02 | 董事 / 高管变动 | CEO/CFO 离职 |
| 7.01 | Regulation FD 披露 | 公平披露（如投资者会材料）|
| 8.01 | 其他事项 | 杂项 |
| **9.01** | **财务报表与附件** | 业绩新闻稿（**Ex-99.1**）就挂在这里 |

> **Ex-99.1** = Exhibit 99.1，附件编号。业绩发布的新闻稿正文通常在这个附件里，
> 而不在 8-K 主文档里 —— 本项目的 `edgar.earnings_releases()` 会自动定位它。

**特殊的 8-K：**

- **8-K12B** —— 继承发行人（Successor Issuer）申报。公司重组换了主体时用。
  ⚠️ 实测 ExxonMobil 2026 年 7 月用的就是这个，导致 ticker 指向了一个
  **没有历史数据的新壳** —— 本项目会自动回溯前身主体。

## 1.3 注册与发行 —— 要卖股票/债券时交

| 编号 | 中文 | 说明 |
|---|---|---|
| **S-1** | IPO 注册说明书 | 首次公开发行。**新公司最详细的一份文件** |
| **S-3** | 简易注册 | 已上市公司再融资 |
| **S-4** | 并购 / 换股注册 | 收购对价是股票时 |
| **424B**系列 | 最终招股说明书 | 定价后的正式版本 |
| **F-1 / F-3 / F-4** | 外国发行人对应版本 | 同上，但发行人是非美国公司 |

## 1.4 股权与所有权 —— 谁持有、谁在买卖

| 编号 | 中文 | 说明 |
|---|---|---|
| **Form 3** | 内部人首次持股申报 | 董事/高管/10%以上股东上任时 |
| **Form 4** | **内部人持股变动** | ⭐ 高管买卖自家股票，**2 个工作日内**必须申报 |
| **Form 5** | 年度补报 | 漏报的补上 |
| **SC 13D** | 收购 >5% 且**有控制意图** | 可能是要约收购、激进投资者 |
| **SC 13G** | **被动**持有 >5% | 指数基金常见，无控制意图 |
| **13F-HR** | 机构季度持仓 | 管理 >$1 亿的机构必须披露持仓 |
| **144** | 限售股转售通知 | 内部人准备卖股票的预告 |

## 1.5 委托书与其他

| 编号 | 中文 | 说明 |
|---|---|---|
| **DEF 14A** | **正式委托书**（Definitive Proxy Statement）| ⭐ 高管薪酬、董事选举、股东提案。**看"以利益还是以是非为标准"的最佳材料**（FRAMEWORK §9）|
| PRE 14A | 初步委托书 | 正式版之前的草稿 |
| **NT 10-K / NT 10-Q** | **延期申报通知** | 🔴 **红旗** —— 交不出财报通常有原因 |
| SD | 冲突矿产披露 | 供应链尽调 |

---

# 二、三张表与常用术语

## 2.1 三张表

| 表 | 英文 | 回答什么 | 时间性质 |
|---|---|---|---|
| **资产负债表** | Balance Sheet | 某一天我有什么、欠谁的 | **时点**（快照）|
| **利润表** | Income Statement / P&L | 一段时间赚了多少（**账面**）| **时期** |
| **现金流量表** | Cash Flow Statement | 同一段时间钱真的进出多少 | **时期** |

## 2.2 利润表：从上到下

| 术语 | 英文 / 缩写 | 含义 |
|---|---|---|
| **营业收入 / 营收** | Revenue / Sales | 卖东西收到（或应收到）的钱 |
| **营业成本** | COGS = Cost of Goods Sold | 卖出去那批东西的**直接成本** |
| **毛利** | Gross Profit | 营收 − 营业成本 |
| **毛利率** | Gross Margin | 毛利 ÷ 营收。**反映定价权** |
| **研发费用** | R&D = Research and Development | |
| **销售管理费用** | SG&A = Selling, General and Administrative | 销售、行政、管理的开销 |
| **营业利润** | Operating Income / **EBIT** = Earnings Before Interest and Taxes | 毛利 − 各项营业费用。**扣息扣税之前** |
| **利息费用** | Interest Expense | 付给债主的钱 |
| **税前利润** | Pre-tax Income | 营业利润 ± 非经营损益 − 利息 |
| **所得税费用** | Income Tax Expense | |
| **净利润** | Net Income | 最后剩下的，**归股东** |
| **归母净利润** | Net Income Attributable to Parent | 扣掉少数股东那部分后，真正归母公司股东的 |
| **每股收益** | EPS = Earnings Per Share | 净利润 ÷ 股数 |
| **摊薄每股收益** | Diluted EPS | 假设所有期权、可转债都转成股票后的 EPS（**更保守，用这个**）|

## 2.3 现金流量表：三个部分

| 部分 | 英文 | 含义 |
|---|---|---|
| **经营活动现金流** | **OCF** = Operating Cash Flow | ⭐ 主营业务真正收到的现金 |
| 投资活动现金流 | Investing Cash Flow | 买卖资产、投资 |
| 融资活动现金流 | Financing Cash Flow | 借钱、还钱、分红、回购 |

**关键的派生指标：**

| 术语 | 公式 | 含义 |
|---|---|---|
| **资本开支** | CapEx = Capital Expenditures | 买厂房、设备、服务器的钱 |
| **自由现金流** | **FCF** = Free Cash Flow = OCF − CapEx | ⭐ **真正能拿走的钱**。本框架最看重的数字 |
| **折旧摊销** | **D&A** = Depreciation and Amortization | 把过去买的资产的成本，分摊到每一年。**是费用但不花现金** |
| **股权激励** | **SBC** = Stock-Based Compensation | 用股票代替现金发工资。**是真实成本**，但不在 OCF 里扣 |

> ⚠️ **10-Q 里的现金流量表是「年初至今累计」的**，不是单季 ——
> 想要单季数字必须用相邻两期相减。本项目自动做了这件事，
> 还原值会带 `+derived` 标记。

## 2.4 资产负债表

**恒等式：资产 = 负债 + 股东权益**

| 术语 | 英文 | 含义 |
|---|---|---|
| **总资产** | Total Assets | |
| 流动资产 | Current Assets | 一年内能变现的 |
| **应收账款** | AR = Accounts Receivable | 卖了货但还没收到的钱 |
| **存货** | Inventory | 仓库里的货。**按成本计价，不是售价** |
| **固定资产净额** | Net PP&E = Property, Plant and Equipment | 厂房设备原值 − 累计折旧 |
| **商誉** | Goodwill | 并购时付出的、**超过对方净资产**的溢价。⚠️ **只会减值，不会增值** |
| **无形资产** | Intangible Assets | 专利、客户关系、品牌等 |
| **应付账款** | AP = Accounts Payable | 欠供应商的货款。**无息负债 —— 占用它是好事** |
| **有息负债** | Interest-Bearing Debt | 要付利息的债：银行贷款、公司债、商业票据 |
| **经营租赁负债** | Operating Lease Liability | 2019 年起上表。经济实质**就是借钱占用资产**，本框架计入有息负债 |
| **股东权益** | Shareholders' Equity（= **净资产** = **账面价值** Book Value）| 总资产 − 总负债 |
| **少数股东权益** | NCI = Non-controlling Interest | 子公司里不属于母公司的那部分 |

## 2.5 回报率三兄弟

| 缩写 | 全称 | 中文 | 分子 | 分母 |
|---|---|---|---|---|
| **ROIC** | Return on Invested Capital | 投入资本回报率 | NOPAT | 有息负债+权益−超额现金 |
| **ROE** | Return on Equity | 净资产收益率 | 净利润 | 股东权益 |
| **ROA** | Return on Assets | 总资产收益率 | 净利润 | 总资产 |
| **NOPAT** | Net Operating Profit After Tax | 税后经营利润 | 营业利润 × (1−有效税率) | — |

> **为什么框架以 ROIC 为主**：它是三者里唯一同时排除了「融资结构」和
> 「闲置现金」干扰的。**ROE 能靠加杠杆做高**，ROA 会被现金稀释。
> 详见 [`FRAMEWORK.md` §5「ROIC 到底是什么」](FRAMEWORK.md)。

## 2.6 估值术语

| 缩写 | 全称 | 中文 | 说明 |
|---|---|---|---|
| **PE** | Price-to-Earnings | 市盈率 | 股价 ÷ 每股收益 |
| **PB** | Price-to-Book | 市净率 | 市值 ÷ 账面净资产 |
| **EV** | Enterprise Value | 企业价值 | 市值 + 有息负债 − 现金。**买下整家公司的代价** |
| **DCF** | Discounted Cash Flow | 现金流折现 | 一切估值的母公式 |
| **WACC** | Weighted Average Cost of Capital | 加权平均资本成本 | 你要求的最低回报率 |
| **TTM** | Trailing Twelve Months | 最近十二个月 | 最近四个季度合计。**比年报新** |
| **CAGR** | Compound Annual Growth Rate | 复合年化增长率 | |
| **YoY / QoQ** | Year-over-Year / Quarter-over-Quarter | 同比 / 环比 | |

## 2.7 常见的"要小心"的词

| 术语 | 英文 | 为什么要小心 |
|---|---|---|
| **non-GAAP** | non-GAAP | 公司自定义的口径，**常把 SBC 和收购摊销加回** —— 数字更好看 |
| **调整后 EBITDA** | Adjusted EBITDA | 息税折旧摊销前利润，**再加回一堆东西**。芒格批评过它 |
| **一次性项目** | One-time / Non-recurring | ⚠️ **每年都发生的"一次性"就是经常性** |
| **积压订单** | RPO = Remaining Performance Obligations / Backlog | 已签约未确认的收入。**要看确认节奏，不只看总额** |
| **重述** | Restatement | 🔴 承认过去的财报是错的 |
| **重大缺陷** | Material Weakness | 🔴 内控有问题，所有数字都要打折看 |
| **关键审计事项** | CAM = Critical Audit Matters | 审计师认为最难判断的地方 —— **正是最该看的地方** |

---

# 三、行业特有的量价指标

**美国会计准则不要求披露销量**，XBRL 里也没有。但很多公司会在 **MD&A**
（Management's Discussion and Analysis，管理层讨论与分析）里主动拆 —— 这是
判断"增长里有多少是价、多少是量"的唯一来源。

| 行业 | 常见披露 |
|---|---|
| 存储半导体 | **bit shipments**（位出货量）、**ASP** = Average Selling Price（平均售价）|
| 航空 | RPM（收入客英里）、ASM（可用座位英里）、Load Factor（客座率）|
| 能源 | 产量（barrels per day，桶/日）、Realized Price（实现价格）|
| 汽车 | Deliveries（交付量）|
| 零售 | **Same-Store Sales**（同店销售）—— 天然剔除了开店影响 |
| 软件 | **NDR** = Net Dollar Retention（净收入留存率）、ARR = Annual Recurring Revenue |
| 银行 | **NIM** = Net Interest Margin（净息差）、拨备覆盖率、资本充足率 |

---

*本表随使用持续补充。看到不认识的词，欢迎让我加进来。*
