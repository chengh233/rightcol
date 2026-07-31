"""rightcol — 自下而上的企业财报认知框架。

主产品是 `FRAMEWORK.md`（认知框架），本包是它的自动化：

    edgar     SEC EDGAR XBRL 客户端（节流 / 缓存 / 重述去重 / 主体重组回溯）
    concepts  us-gaap 标签 → 统一口径的回退链
    metrics   指标计算（ROIC / 杜邦 / FCF / 应计 / CCC / 增量 ROIC）
    valuation 逆向 DCF · 价值驱动 PE · 敏感性
    peers     行业横切（中位数 + 分位数）
    report    数据包渲染

设计上只做一件事：**把数字算对，并且在算不对的时候说出来**。
所有判断留给 FRAMEWORK.md 和使用者。
"""

__version__ = "0.1.0"
