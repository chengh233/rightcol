"""SEC EDGAR XBRL 客户端 —— rightcol 的确定性数据地基。

这一层只做一件事：**把 SEC 官方数据取出来、对齐口径、去掉重述噪音**。
它不做任何判断，不算任何"好坏"，也绝不调用 LLM。判断在 FRAMEWORK.md 里，
由你（和 .claude/skills/ 里的精读层）来做。

为什么直连 EDGAR 而不用第三方财经 API：
  - 官方、免费、无密钥、无调用额度，且是**申报原始口径**——没有中间商粉饰。
  - 第三方 API 常年偷偷做口径调整（把 SBC 加回、把一次性项目平滑掉），
    而这个项目的整个方法论建立在"分辨管理层调整过什么"之上。用调整过的
    二手数据看财报质量，等于用嫌疑人写的笔录破案。

已验证的三个官方端点（2026-07 实测通过）：
  ticker→CIK   https://www.sec.gov/files/company_tickers.json
  全部事实      https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json
  单个概念      https://data.sec.gov/api/xbrl/companyconcept/CIK##########/us-gaap/<Tag>.json
  申报列表      https://data.sec.gov/submissions/CIK##########.json

SEC 的两条硬性要求（违反会被封 IP）：
  1. User-Agent 必须带真实联系方式，形如 "Name email@example.com"。
  2. 速率上限 10 次/秒。本模块统一节流到 ~7 次/秒留余量。
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import requests

# --------------------------------------------------------------------------
# 配置
# --------------------------------------------------------------------------

# SEC 要求 UA 带可联系到你的信息。改成你自己的邮箱，或设环境变量 RIGHTCOL_UA。
DEFAULT_UA = os.environ.get("RIGHTCOL_UA", "rightcol/0.1 (chengh233x@gmail.com)")

CACHE_DIR = Path(os.environ.get("RIGHTCOL_CACHE", Path(__file__).resolve().parent.parent / "data" / "cache"))
TICKER_MAP_PATH = Path(__file__).resolve().parent.parent / "data" / "company_tickers.json"

# companyfacts 单个大公司可达数 MB，且一天最多更新一次 —— 默认缓存 24h。
CACHE_TTL_SEC = int(os.environ.get("RIGHTCOL_CACHE_TTL", 24 * 3600))

_SEC_MIN_INTERVAL = 1.0 / 7.0  # ~7 req/s，官方上限 10/s
_rate_lock = threading.Lock()
_last_call = [0.0]


def _throttle() -> None:
    with _rate_lock:
        wait = _last_call[0] + _SEC_MIN_INTERVAL - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.monotonic()


def _get_json(url: str, cache_key: str | None = None, ttl: int = CACHE_TTL_SEC) -> dict:
    """带节流、重试与本地缓存的 GET。缓存命中不消耗 SEC 配额。"""
    path = CACHE_DIR / f"{cache_key}.json" if cache_key else None
    if path and path.exists() and (time.time() - path.stat().st_mtime) < ttl:
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            path.unlink(missing_ok=True)  # 缓存损坏就重取

    last_err: Exception | None = None
    for attempt in range(4):
        _throttle()
        try:
            r = requests.get(url, headers={"User-Agent": DEFAULT_UA, "Accept-Encoding": "gzip, deflate"}, timeout=30)
            if r.status_code == 404:
                raise FileNotFoundError(f"EDGAR 404: {url}")
            r.raise_for_status()
            data = r.json()
            if path:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(data))
            return data
        except FileNotFoundError:
            raise
        except Exception as e:  # 网络抖动 / 429 / 5xx
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"EDGAR 请求失败（已重试 4 次）: {url}") from last_err


# --------------------------------------------------------------------------
# ticker -> CIK
# --------------------------------------------------------------------------


def _ticker_map() -> dict:
    if not TICKER_MAP_PATH.exists() or (time.time() - TICKER_MAP_PATH.stat().st_mtime) > 30 * 86400:
        data = _get_json("https://www.sec.gov/files/company_tickers.json")
        TICKER_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
        TICKER_MAP_PATH.write_text(json.dumps(data))
        return data
    return json.loads(TICKER_MAP_PATH.read_text())


def cik_candidates(ticker: str) -> list[str]:
    """一个 ticker 可能对应**多个** CIK —— 这不是理论问题，是实测踩到的坑。

    实例（2026-07 实测）：`XOM` 同时映射到
        CIK 0002115436  ExxonMobil Holdings Corp  —— 重组新设的控股主体，
                                                    XBRL 历史**完全为空**
        CIK 0000034088  EXXON MOBIL CORP          —— 真正有数据的申报主体
    如果闭着眼睛取第一个匹配，XOM 的分析会安静地返回空结果。同类情形还会出现在
    公司重组、换壳上市、双重股权分设主体的场合。

    所以这里返回**全部**候选，由 `company_facts` 挑出真正有 us-gaap 事实的那个。
    """
    ticker = ticker.strip().upper()
    hits = [str(r["cik_str"]).zfill(10) for r in _ticker_map().values() if r["ticker"].upper() == ticker]
    if not hits:
        raise KeyError(
            f"EDGAR 里找不到 ticker {ticker!r}。可能原因：ETF / 指数无 XBRL 申报、"
            f"已退市或被并购、或该公司以 20-F 申报（非美国发行人，见 README「数据的诚实声明」）。"
        )
    return list(dict.fromkeys(hits))


def _has_gaap(cik: str, require_annual: bool = True) -> bool:
    """该 CIK 是否有可用的 us-gaap 事实。

    ⚠️ `require_annual=True` 是关键，而且是**被现实教出来的**：

    最初这里只检查"有没有 us-gaap 事实"。但 ExxonMobil 重组后，新设的
    `ExxonMobil Holdings Corp` 在几周内提交了首份 **10-Q** —— 于是它突然
    有了 94 个 us-gaap 标签，护栏判定"有数据"，主体回溯不再触发。
    可这个壳**一份 10-K 都没有**，而年度序列只认 10-K，结果是
    「取不到年度数据」。前身 CIK 那边有 438 个标签、10-K 回溯到 2007 年。

    教训：**"有数据"和"有你需要的那种数据"是两件事。** 继承发行人会先
    交季报再交年报，中间这段窗口足以骗过一个只看"有没有"的检查。
    """
    try:
        facts = _get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", cache_key=f"facts_{cik}")
        ug = facts.get("facts", {}).get("us-gaap")
        if not ug:
            return False
        if not require_annual:
            return True
        annual_forms = {"10-K", "10-K/A", "20-F", "20-F/A"}
        for tag in ("Assets", "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "NetIncomeLoss"):
            for rows in ug.get(tag, {}).get("units", {}).values():
                if any(r.get("form") in annual_forms for r in rows):
                    return True
        return False
    except Exception:
        return False


def _search_cik_by_name(name: str) -> list[str]:
    """按公司名在 EDGAR 检索有 10-K 历史的主体，返回 CIK 列表。"""
    import re
    import urllib.parse

    q = urllib.parse.quote_plus(name)
    url = (
        f"https://www.sec.gov/cgi-bin/browse-edgar?company={q}&CIK=&type=10-K"
        f"&dateb=&owner=include&count=20&action=getcompany&output=atom"
    )
    _throttle()
    try:
        r = requests.get(url, headers={"User-Agent": DEFAULT_UA}, timeout=30)
        r.raise_for_status()
        return list(dict.fromkeys(re.findall(r"<cik>(\d{10})</cik>", r.text)))
    except Exception:
        return []


def cik_for(ticker: str) -> str:
    """解析成单个 CIK，并在**主体重组**后自动接回真正有财务历史的前身主体。

    为什么需要这一层（2026-07 实测的真实事故）：
        ExxonMobil 于 2026 年 7 月完成控股公司重组（申报 `8-K12B`——继承发行人
        专用表格）。SEC 的 ticker 映射表**立刻**把 `XOM` 指向新设的
        `ExxonMobil Holdings Corp` (CIK 2115436)，而该主体的 XBRL 事实**完全为空**；
        全部财务历史仍留在 `EXXON MOBIL CORP` (CIK 34088) 上。

    这类事件（控股重组、换壳、重新注册地）每年都会发生几起。若不处理，你会
    对着一家 30 年历史的巨头得到"查无数据"，或更糟——得到一个只有几个月历史的
    序列，还以为那就是全部。

    解析顺序：手工覆盖 → ticker 映射（多候选取有数据者）→ 按公司名回溯前身。
    """
    ticker = ticker.strip().upper()

    # 1) 手工覆盖永远优先 —— 自动推断出错时你有确定的逃生舱
    ov_path = Path(__file__).resolve().parent.parent / "data" / "cik_overrides.json"
    if ov_path.exists():
        ov = json.loads(ov_path.read_text())
        if ticker in ov:
            return str(ov[ticker]).zfill(10)

    cands = cik_candidates(ticker)
    for cik in cands:
        if _has_gaap(cik):
            return cik

    # 2) 映射到的主体没有财务事实 —— 按名字回溯前身
    stale = cands[0]
    try:
        sub = _get_json(f"https://data.sec.gov/submissions/CIK{stale}.json", cache_key=f"sub_{stale}", ttl=6 * 3600)
        raw = sub.get("name", "")
    except Exception:
        raw = ""
    # 去掉重组后加上的壳字样，用主干名去搜前身。
    # 要试多个变体：重组后的新名常把词连写（ExxonMobil），而前身在 EDGAR 里
    # 是分写的（EXXON MOBIL CORP），直接搜连写版**搜不到**（实测）。
    import re as _re

    stem = _re.sub(r"\b(holdings?|holdco|group|inc|corp|corporation|co|plc|ltd|new)\b\.?", " ", raw, flags=_re.I)
    stem = " ".join(stem.split())
    camel = " ".join(_re.findall(r"[A-Z][a-z]+|[A-Z]{2,}(?![a-z])|\d+", stem)) or stem
    variants = [v for v in dict.fromkeys([stem, camel, stem.split(" ")[0] if stem else ""]) if len(v) >= 3]

    # ⚠️ 按名搜索必须校验，否则会静默返回**完全无关的公司**。
    # 只接受名称与目标主干名有实质重叠的候选（共享一个 ≥4 字符的词），
    # 且该主体必须真的有 us-gaap 事实。宁可失败并抛出可读错误，
    # 也不能把 A 公司的财报当成 B 公司交给用户。
    stem_words = {w.lower() for w in _re.findall(r"[A-Za-z]{4,}", camel or stem)}
    for v in variants:
        for cik in _search_cik_by_name(v):
            if cik == stale or not _has_gaap(cik):
                continue
            try:
                cand_name = _get_json(
                    f"https://data.sec.gov/submissions/CIK{cik}.json", cache_key=f"sub_{cik}", ttl=6 * 3600
                ).get("name", "")
            except Exception:
                continue
            cand_words = {w.lower() for w in _re.findall(r"[A-Za-z]{4,}", cand_name)}
            if stem_words & cand_words:
                return cik

    return stale  # 找不到就交回原 CIK，由 company_facts 抛出可读的错误


def company_name(ticker: str) -> str:
    """返回**实际取数主体**的名称，不是 ticker 映射表里的名字。

    这两者在主体重组后会不一致：`XOM` 在映射表里叫 "ExxonMobil Holdings Corp"
    （XBRL 完全为空的新壳），而数据实际来自 "Exxon Mobil Corporation"。
    报告标题必须显示后者 —— 否则你就失去了「一眼看出取错了主体」这道人工校验。
    """
    try:
        cik = cik_for(ticker)
        facts = _get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", cache_key=f"facts_{cik}")
        if facts.get("entityName"):
            return facts["entityName"].strip()
    except Exception:
        pass
    data = json.loads(TICKER_MAP_PATH.read_text()) if TICKER_MAP_PATH.exists() else {}
    for row in data.values():
        if row["ticker"].upper() == ticker.strip().upper():
            return row["title"]
    return ticker.upper()


def entity_info(ticker: str) -> dict:
    """报告头部用：同时给出实体名与实际使用的 CIK，方便人工核对取数主体。"""
    cik = cik_for(ticker)
    return {"cik": cik, "name": company_name(ticker), "ticker": ticker.upper()}


# --------------------------------------------------------------------------
# 事实抽取
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Fact:
    """一个已对齐口径的财务事实。

    tag    实际命中的 us-gaap 标签（回退链里到底用了哪个——必须留痕，否则
           跨公司对比时你不知道自己在比什么）
    start  期间起（流量项；存量项为 None）
    end    期间止 / 时点
    val    数值（原始单位，通常是 USD）
    fy/fp  申报归属财年与期间
    form   10-K / 10-Q / 8-K ...
    filed  申报日期——用于在重述中取最新版本
    """

    tag: str
    start: str | None
    end: str
    val: float
    fy: int | None
    fp: str | None
    form: str
    filed: str
    unit: str

    @property
    def days(self) -> int | None:
        if not self.start:
            return None
        from datetime import date

        a = date.fromisoformat(self.start)
        b = date.fromisoformat(self.end)
        return (b - a).days


def company_facts(ticker: str) -> dict:
    """拉取该公司**全部** XBRL 事实（一次请求，之后本地缓存 24h）。

    拿不到 us-gaap 事实时**直接抛错**，绝不返回空壳让下游把"没有数据"算成
    "指标为 0"。数据中断必须长得像数据中断。
    """
    cik = cik_for(ticker)
    facts = _get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", cache_key=f"facts_{cik}")
    if not facts.get("facts", {}).get("us-gaap"):
        taxes = list(facts.get("facts", {}).keys())
        raise ValueError(
            f"{ticker} (CIK {cik}) 没有 us-gaap 事实，只有 {taxes}。"
            f"常见原因：该主体是重组新设的控股壳（历史在前身 CIK 上）、"
            f"以 IFRS 申报的外国发行人（用 ifrs-full 分类），或尚未有年报。"
        )
    return facts


def _extract(facts: dict, tag: str, taxonomy: str = "us-gaap") -> list[Fact]:
    node = facts.get("facts", {}).get(taxonomy, {}).get(tag)
    if not node:
        return []
    out: list[Fact] = []
    for unit, rows in node.get("units", {}).items():
        for r in rows:
            out.append(
                Fact(
                    tag=tag,
                    start=r.get("start"),
                    end=r["end"],
                    val=float(r["val"]),
                    fy=r.get("fy"),
                    fp=r.get("fp"),
                    form=r.get("form", ""),
                    filed=r.get("filed", ""),
                    unit=unit,
                )
            )
    return out


def annual_series(
    facts: dict,
    tags: list[str],
    *,
    kind: str = "flow",
    taxonomy: str = "us-gaap",
    strict_priority: bool = False,
) -> dict[str, Fact]:
    """按**回退优先级**在 tags 里逐个尝试，取出年度序列，key 为期末日期。

    这个函数是整个数据层最关键、也最容易出错的地方，三个坑都在这里处理：

    坑 1 —— 同一概念标签会变。
        Apple 的营收 2018 年前用 `Revenues`，之后改用
        `RevenueFromContractWithCustomerExcludingAssessedTax`（ASC 606 生效）。
        所以必须给**回退链**而不是单个标签，并且回退是**逐年**做的：
        某一年首选标签缺失就用次选，而不是整条序列二选一。

    坑 2 —— 重述（restatement）。
        同一个财年会被申报多次（当年 10-K 一次，之后作为比较期再出现若干次，
        口径可能已被重述）。这里按 (start, end) 分组，取 `filed` 最新的那条——
        即**公司自己最新承认的口径**。想看"当年原始申报值"是另一个需求，
        用 `original=True`（未实现，路线图）。

    坑 3 —— 期间对齐。
        流量项（利润表 / 现金流量表）必须筛出 ~365 天的区间，否则会把季度
        数据混进年度序列；存量项（资产负债表）是时点值，没有 start。
        财年不等于日历年（Apple 财年 9 月底结束），因此 key 用**期末日期**而
        非年份——跨公司比较时你必须自己意识到财年错位。
    """
    return _period_series(
        facts, tags, kind=kind, taxonomy=taxonomy, strict_priority=strict_priority,
        forms=("10-K", "10-K/A", "20-F", "20-F/A"), day_range=(340, 400),
    )


ANNUAL_FORMS = ("10-K", "10-K/A", "20-F", "20-F/A")
QUARTERLY_FORMS = ("10-Q", "10-Q/A", "10-K", "10-K/A")


def _period_series(
    facts: dict,
    tags: list[str],
    *,
    kind: str,
    taxonomy: str,
    strict_priority: bool,
    forms: tuple[str, ...],
    day_range: tuple[int, int],
) -> dict[str, Fact]:
    """按期间长度与申报类型抽取序列的公共内核（年度 / 季度共用）。"""
    lo_d, hi_d = day_range
    # 第一步：按标签分别收集合格事实，并在标签内部做重述去重（取 filed 最新）
    by_tag: dict[str, dict[tuple[str | None, str], Fact]] = {}
    for tag in tags:
        raw = _extract(facts, tag, taxonomy)

        # ⚠️ **绝不能把不同计量单位的事实混进同一条序列。**
        #
        # 实测事故：Nebius（前身 Yandex N.V.，外国发行人用 20-F 申报）同时以
        # **卢布和美元**申报营收 —— RUB 覆盖 2009–2023，USD 覆盖 2011–2025。
        # 不按单位过滤的话，2020 年会取到 2183.44 亿**卢布**，被当成 2183 亿
        # **美元**排进序列（真实值 29.56 亿美元，差 74 倍），而且不报错。
        #
        # 规则：一条序列只用一个单位。货币优先 USD（本项目只做美股，所有
        # 横向比较都隐含美元口径）；没有 USD 时取记录最多的那个单位。
        units = {}
        for f in raw:
            units.setdefault(f.unit, 0)
            units[f.unit] += 1
        if len(units) > 1:
            chosen = "USD" if "USD" in units else max(units, key=lambda u: units[u])
            raw = [f for f in raw if f.unit == chosen]

        bucket: dict[tuple[str | None, str], Fact] = {}
        for f in raw:
            if f.form not in forms:
                continue
            if kind == "flow":
                if f.start is None or not (lo_d <= (f.days or 0) <= hi_d):
                    continue
            else:  # stock / instant
                if f.start is not None:
                    continue
            key = (f.start, f.end)
            prev = bucket.get(key)
            if prev is None or f.filed > prev.filed:
                bucket[key] = f
        if bucket:
            by_tag[tag] = bucket

    if not by_tag:
        return {}

    # 第二步：选**主标签** = 覆盖期间数最多的那个，而不是回退链里排最前的那个。
    #
    # 为什么不能简单按回退链优先级逐年取（这是修掉的一个真实事故）：
    # 万事达同时申报 `Revenues`（净额口径，2007–2025 连续 18 年）与
    # `RevenueFromContractWithCustomerExcludingAssessedTax`（**毛额**口径，
    # 仅 2018–2021 四年，2018 年为 21.83B vs 净额 14.95B）。若按回退链优先
    # 取后者，序列会在 2018 年凭空跳 +75%、2022 年再跌 −25% —— 两个都是
    # 口径切换造成的**假增速**，而报告会把它当成真实经营变化。
    #
    # 「覆盖最广者为主」这条规则同时对苹果成立：ASC 606 后的新标签覆盖 8 年、
    # 旧的 `Revenues` 只剩 3 年，主标签正确地落在新标签上，早年再用旧标签补。
    #
    # ⚠️ 但这条规则**只对「同义标签」成立**。当回退链里含有口径更窄的标签
    # （税务附注的境内分部、含库存股的已发行股数、不含摊销的狭义折旧），
    # 按覆盖度选主会让分项冒充总额 —— 实测这会让 41 家里 23 家的有效税率翻倍。
    # 这类概念用 strict_priority=True，严格按链序取首个可用者为主标签。
    # 名单见 concepts.STRICT_PRIORITY。
    if strict_priority:
        primary = next(t for t in tags if t in by_tag)
    else:
        primary = max(by_tag, key=lambda t: (len(by_tag[t]), -tags.index(t)))
    picked: dict[tuple[str | None, str], Fact] = dict(by_tag[primary])

    # 第三步：主标签没覆盖到的期间，才按回退链顺序补
    for tag in tags:
        if tag == primary or tag not in by_tag:
            continue
        for key, f in by_tag[tag].items():
            picked.setdefault(key, f)

    return {f.end: f for f in sorted(picked.values(), key=lambda x: x.end)}


def latest_n(series: dict[str, Fact], n: int) -> dict[str, Fact]:
    keys = sorted(series)[-n:]
    return {k: series[k] for k in keys}


def quarterly_series(
    facts: dict,
    tags: list[str],
    *,
    kind: str = "flow",
    taxonomy: str = "us-gaap",
    strict_priority: bool = False,
) -> dict[str, Fact]:
    """取出**单季度**序列，key 为季末日期。

    为什么必须单独实现、不能复用年度那套：

    坑 1 —— **同一家公司在 10-K 和 10-Q 里可能用不同标签**（实测）。
        英伟达年报的营收用 `RevenueFromContractWithCustomerExcludingAssessedTax`，
        季报却用 `Revenues`。所以季度序列必须**独立**跑一遍主标签选择，
        不能沿用年报选出的主标签，否则会得到一个几乎全空的序列。

    坑 2 —— **10-Q 里同时含单季值和年初至今(YTD)值**，两者 `end` 相同、
        `start` 不同。这里用 80~100 天的区间长度筛掉 YTD。

    坑 3 —— **Q4 不在任何 10-Q 里**。财年最后一季只出现在 10-K，而 10-K 报的是
        全年。所以 Q4 必须用「全年 − 前三季」倒推，见 `derive_q4()`。

    坑 4 —— 部分公司（尤其外国发行人、部分金融机构）**只报 YTD 不报单季**，
        此时这里会返回空或缺季，需要用相邻 YTD 相减补，见 `_from_ytd()`。
    """
    q = _period_series(
        facts, tags, kind=kind, taxonomy=taxonomy, strict_priority=strict_priority,
        forms=QUARTERLY_FORMS, day_range=(QUARTER_MIN_DAYS, QUARTER_MAX_DAYS),
    )
    if kind == "flow":
        # ⚠️ **必须无条件做 YTD 差分来补缺口**，不能只在"季度数不足"时才做。
        #
        # 因为**现金流量表在 10-Q 里永远是年初至今累计的**（实测 Micron：
        # 90天 / 181天 / 272天，只有 Q1 恰好等于单季）。跨多年之后，
        # 光是各年的 Q1 就能凑够 4 条，于是"不足才补"的条件永远不成立，
        # 而 Q2/Q3 永远缺失 —— TTM 现金流因此长期算不出来。
        #
        # 真实的单季值优先，差分值只用来填空。
        derived = _from_ytd(facts, tags, taxonomy=taxonomy, strict_priority=strict_priority)
        q = {**derived, **q}
    return dict(sorted(q.items()))


QUARTER_MIN_DAYS, QUARTER_MAX_DAYS = 80, 120
"""单季区间的容许长度。

上限取 120 而非 100，是因为 **52/53 周财年制**（零售业普遍）的第四财季是
**16 周 = 112 天**：实测 Costco 的季度是 12/12/12/16 周。窗口卡在 100 会把
这类公司的 Q4 整个丢掉，TTM 因而永远算不出来。
101~120 天之间不存在别的合法期间类型，放宽是安全的。"""


def _from_ytd(
    facts: dict, tags: list[str], *, taxonomy: str, strict_priority: bool
) -> dict[str, Fact]:
    """用**相邻累计值相减**还原单季。

    为什么这一步不可省：**10-Q 里的现金流量表永远是年初至今累计的**，
    不是单季（实测 Micron：90 / 181 / 272 天）。不做差分就永远拿不到
    单季现金流，TTM 自由现金流也就永远是空的。

    做法：把**共享同一个 start** 的所有累计区间（Q1 / H1 / 9M / 全年）按终点
    排序，逐个相减。关键是**必须把 Q1 那条也纳入链条** —— 它既是单季也是
    首个累计值，漏掉它会让 Q2 差分不出来（这是第一版的 bug）。

    还原出来的事实 `tag` 带 `+derived(YTD差分)` 后缀 —— **口径必须留痕**，
    因为它是算出来的，不是申报的。
    """
    from datetime import date

    # 收集全部累计区间：Q1(~90天) / H1(~181) / 9M(~272) / 全年(~365)
    cumulative: dict[tuple[str | None, str], Fact] = {}
    for lo, hi in ((QUARTER_MIN_DAYS, QUARTER_MAX_DAYS), (160, 200), (250, 290), (340, 400)):
        got = _period_series(
            facts, tags, kind="flow", taxonomy=taxonomy, strict_priority=strict_priority,
            forms=QUARTERLY_FORMS + ANNUAL_FORMS, day_range=(lo, hi),
        )
        for f in got.values():
            cumulative[(f.start, f.end)] = f
    if not cumulative:
        return {}

    # 按 start 分组 —— 同一财年的各期累计值共享同一个起点
    groups: dict[str, list[Fact]] = {}
    for f in cumulative.values():
        if f.start:
            groups.setdefault(f.start, []).append(f)

    out: dict[str, Fact] = {}
    for start, fs in groups.items():
        fs.sort(key=lambda x: x.end)
        prev_end, prev_val = start, 0.0
        for f in fs:
            span = (date.fromisoformat(f.end) - date.fromisoformat(prev_end)).days
            if QUARTER_MIN_DAYS <= span <= QUARTER_MAX_DAYS:
                out[f.end] = Fact(
                    tag=f.tag + "+derived(YTD差分)", start=prev_end, end=f.end,
                    val=f.val - prev_val, fy=f.fy, fp=f.fp, form=f.form,
                    filed=f.filed, unit=f.unit,
                )
            prev_end, prev_val = f.end, f.val
    return out


def derive_q4(quarters: dict[str, Fact], annuals: dict[str, Fact]) -> dict[str, Fact]:
    """用「全年 − 前三季」倒推财年最后一季，补进季度序列。

    **这一步不做，任何 TTM 都是错的** —— 因为最近四个季度里必然有一个 Q4，
    而它从不出现在 10-Q 里。实测英伟达：漏掉 Q4 会让 TTM 净利润从 1596 亿
    变成拼错的数，P/E 从 30.3× 变成 35.7×。

    只在**恰好凑齐前三季**时倒推；凑不齐就不猜（返回时不含该财年 Q4）。
    """
    from datetime import date

    out = dict(quarters)
    for fy_end, a in annuals.items():
        if fy_end in out or a.start is None:
            continue
        fy_start = date.fromisoformat(a.start)
        inner = [f for k, f in quarters.items() if a.start < k < fy_end and date.fromisoformat(k) > fy_start]
        if len(inner) != 3:
            continue  # 凑不齐三季就不倒推，绝不猜
        covered = sum(f.val for f in inner)
        last_end = max(f.end for f in inner)
        span = (date.fromisoformat(fy_end) - date.fromisoformat(last_end)).days
        if not (QUARTER_MIN_DAYS <= span <= QUARTER_MAX_DAYS):
            continue
        out[fy_end] = Fact(
            tag=a.tag + "+derived(全年−前三季)", start=last_end, end=fy_end,
            val=a.val - covered, fy=a.fy, fp="Q4", form=a.form, filed=a.filed, unit=a.unit,
        )
    return dict(sorted(out.items()))


# --------------------------------------------------------------------------
# 申报原文 —— LLM 精读层的输入
# --------------------------------------------------------------------------


def filings(ticker: str, form: str = "10-K", limit: int = 5) -> list[dict]:
    """列出最近的申报，返回可直接打开的主文档 URL。

    这是**给 LLM 精读层用的**：数字层回答"是多少"，原文层回答"管理层怎么说、
    以及和去年比措辞变了什么"。风险因素章节的逐年 diff 常常比任何财务指标都
    先反映出问题。
    """
    cik = cik_for(ticker)
    sub = _get_json(f"https://data.sec.gov/submissions/CIK{cik}.json", cache_key=f"sub_{cik}", ttl=6 * 3600)
    recent = sub["filings"]["recent"]
    out = []
    for i, ft in enumerate(recent["form"]):
        if ft != form:
            continue
        accn = recent["accessionNumber"][i].replace("-", "")
        out.append(
            {
                "form": ft,
                "filed": recent["filingDate"][i],
                "period": recent.get("reportDate", [None] * len(recent["form"]))[i],
                "accession": recent["accessionNumber"][i],
                "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}/{recent['primaryDocument'][i]}",
            }
        )
        if len(out) >= limit:
            break
    return out
