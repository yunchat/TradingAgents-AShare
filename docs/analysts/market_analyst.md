# 市场技术分析师 (Market Analyst)

## 角色定位

基于 K 线数据与技术指标，分析个股短期技术走势。

## 时间视角

固定**短期**（short，14 天窗口）

## 数据源

### K 线数据

| 字段 | 工具 | 参数 | 说明 |
|------|------|------|------|
| OHLCV | `get_stock_data` | symbol, start_date, end_date | 近 14 天日 K 线（开/高/低/收/量） |

**获取接口：**
```python
get_stock_data(
    symbol: str,       # 股票代码，如 "000001.SZ"
    start_date: str,   # 开始日期 "YYYY-MM-DD"
    end_date: str,     # 结束日期 "YYYY-MM-DD"
) -> str               # CSV 格式 OHLCV 数据
```

路由分类：`core_stock_apis`，供应商链：`cn_akshare → cn_baostock → yfinance`

---

### 技术指标

| 指标 | 工具 | 说明 |
|------|------|------|
| `close_50_sma` | `get_indicators` | 50 日收盘均线 |
| `close_200_sma` | `get_indicators` | 200 日收盘均线 |
| `close_10_ema` | `get_indicators` | 10 日指数均线 |
| `rsi` | `get_indicators` | 相对强弱指数（14日） |
| `macd` | `get_indicators` | MACD 差离值 / 信号线 / 柱状图 |
| `boll` | `get_indicators` | 布林带中轨（20日均线） |
| `boll_ub` | `get_indicators` | 布林带上轨（+2σ） |
| `boll_lb` | `get_indicators` | 布林带下轨（-2σ） |
| `atr` | `get_indicators` | 平均真实波幅（14日） |
| `vwma` | `get_indicators` | 成交量加权移动均线 |

**获取接口：**
```python
get_indicators(
    symbol: str,           # 股票代码
    indicator: str,        # 指标名，如 "rsi"、"macd"
    curr_date: str,        # 当前交易日 "YYYY-MM-DD"
    look_back_days: int,   # 回看天数，默认 14（短期）/ 90（中期）
) -> str                   # 指标数值序列（文本格式）
```

路由分类：`technical_indicators`，供应商链：`cn_akshare → cn_baostock → yfinance`

---

### 数据获取流程

```
data_collector.get_window(pool, "short", current_date)
    ├── 命中缓存 → 直接返回 stock_data + indicators（无网络请求）
    └── 未命中  → _fetch_direct() 并行调用：
                    ├── get_stock_data(...)
                    ├── get_indicators(..., "close_50_sma")
                    ├── get_indicators(..., "close_200_sma")
                    ├── ... (共 10 个指标，asyncio.gather 并行)
                    └── get_indicators(..., "vwma")
```

所有 11 个请求（1 个 K 线 + 10 个指标）通过 `asyncio.gather` **并行**发起，任一失败返回错误文本，不影响其他指标。

---

## 输入状态

| 字段 | 类型 | 说明 |
|------|------|------|
| `trade_date` | str | 当前交易日 "YYYY-MM-DD" |
| `company_of_interest` | str | 股票代码 |
| `user_intent.focus_areas` | list | 用户关注领域（影响 prompt 侧重） |
| `user_intent.specific_questions` | list | 用户具体问题 |

## 输出状态

| 字段 | 类型 | 说明 |
|------|------|------|
| `market_report` | str | 完整技术面分析报告（流式输出） |
| `analyst_traces` | list | 包含 agent 名、horizon、数据窗口、结论、置信度 |

### analyst_traces 结构

```json
{
  "agent": "market_analyst",
  "horizon": "short",
  "data_window": "14天",
  "key_finding": "市场技术面结论：<verdict>",
  "verdict": "bullish | bearish | neutral",
  "confidence": 0.0
}
```

## 分析逻辑

1. 从 `data_collector` 缓存池读取窗口数据（缓存未命中时并行调用所有工具）
2. 结合用户意图（`focus_areas`、`specific_questions`）构建 horizon 上下文
3. 调用 LLM 流式生成技术面分析报告（`market_report`）
4. 从报告中提取 `verdict`（多空判断）和 `confidence`（置信度）
