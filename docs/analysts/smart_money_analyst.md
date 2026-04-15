# 主力资金分析师 (Smart Money Analyst)

## 角色定位

追踪主力资金动向，通过资金流向、龙虎榜和成交量指标判断机构/大资金行为。

## 时间视角

固定**短期**（short）

## 数据源详解

### 1. 主力资金净流向 (`get_individual_fund_flow`)

**输入参数：**
- `symbol`: 股票代码（如 "600519"）

**底层采集接口：**
```python
akshare.stock_individual_fund_flow(stock=code, market=market)
# market: "sh"（沪市：5/6/9开头）或 "sz"（深市）
```

**数据来源：** 东方财富网个股资金流向

**原始返回格式（实测 600519）：**
```
columns: ['日期', '收盘价', '涨跌幅', '主力净流入-净额', '主力净流入-净占比',
          '超大单净流入-净额', '超大单净流入-净占比', '大单净流入-净额', '大单净流入-净占比',
          '中单净流入-净额', '中单净流入-净占比', '小单净流入-净额', '小单净流入-净占比']
shape: (120, 13)  # 约120个交易日

最近5条（tail）：
日期         收盘价     涨跌幅   主力净流入-净额    超大单净流入-净额   大单净流入-净额
2026-04-07  1440.02  -1.37%  -340527856.0   -272269584.0   -68258272.0
2026-04-08  1465.02  +1.74%   201450816.0   -17807024.0   219257840.0
2026-04-09  1460.49  -0.31%  -241092656.0   -52333824.0  -188758832.0
2026-04-10  1453.96  -0.45%  -163078000.0   -27641152.0  -135436848.0
2026-04-13  1443.31  -0.73%  -250575824.0   -50204624.0  -200371200.0
```

> **注意：** 今日盘中数据**不在返回结果中**，最新数据为上一个已收盘交易日。

**输出格式：**
```
600519 近5日主力资金净流向：
     日期    主力净流入   超大单净流入   大单净流入   中单净流入   小单净流入
2026-04-07  -1234.56    -800.00      -434.56     500.00      734.56
...
```

**数据窗口：** 最近5个交易日（约120条历史，取 tail(5)）

**快速测试脚本：**
```python
import akshare as ak
df = ak.stock_individual_fund_flow(stock='600519', market='sh')
print('columns:', df.columns.tolist())
print('shape:', df.shape)
print(df.tail(5).to_string())
```

---

### 2. 龙虎榜明细 (`get_lhb_detail`)

**输入参数：**
- `symbol`: 股票代码
- `date`: 查询日期（格式：YYYY-MM-DD）

**底层采集接口：**
```python
akshare.stock_lhb_detail_em(start_date=date_fmt, end_date=date_fmt)
# date_fmt: "20260407" (去掉横杠)
# 返回全市场数据，代码内手动过滤指定股票
```

**数据来源：** 东方财富网龙虎榜

**原始返回格式（实测 2026-04-10 至 2026-04-14）：**
```
columns: ['序号', '代码', '名称', '上榜日', '解读', '收盘价', '涨跌幅',
          '龙虎榜净买额', '龙虎榜买入额', '龙虎榜卖出额', '龙虎榜成交额',
          '市场总成交额', '净买额占总成交比', '成交额占总成交比', '换手率',
          '流通市值', '上榜原因', '上榜后1日', '上榜后2日', '上榜后5日', '上榜后10日']
shape: (147, 21)  # 全市场所有上榜股票，需按代码过滤

示例：
代码      名称    上榜日         上榜原因                  龙虎榜净买额
000070  特发信息  2026-04-13  日振幅值达到15%的前5只证券   2.93亿
000400  许继电气  2026-04-13  日跌幅偏离值达到7%的前5只证券  -2.89亿
```

> **注意：** 接口返回全市场数据，代码内按 `symbol` 过滤。今日盘中**不返回当日数据**，最新数据为上一个已收盘交易日。非异动日该股无上榜记录属正常。

**输出格式：**
```
600519 龙虎榜明细（2026-04-07）：
代码    名称    上榜原因    买入金额    卖出金额    净买入    营业部
600519  贵州茅台  日涨幅偏离值达7%  5000.00    2000.00    3000.00   机构专用
...
```

**特殊情况：** 非异动日无数据属正常（返回"无龙虎榜数据"）

---

### 3. 技术指标 (`get_indicators`)

**输入参数：**
- `symbol`: 股票代码
- `indicator`: 指标名（如 "vwma"、"rsi"、"macd" 等，见支持列表）
- `curr_date`: 当前日期
- `look_back_days`: 回溯天数（smart_money 使用 20）

**底层采集接口：**
```python
# 通过 cn_akshare 获取日K历史数据
# 取回溯窗口与260天中的较大值，确保指标计算有足够历史
start_dt = curr_dt - timedelta(days=max(look_back_days, 260))
_fetch_hist_df(symbol, start_date, curr_date)
# 然后用 stockstats.wrap() 计算指定指标
```

**数据来源：** AkShare（东方财富日K线）

**计算逻辑：**
1. 拉取 `max(look_back_days, 260)` 天的日K数据（保证均线类指标有足够历史）
2. 用 `stockstats` 计算指标序列
3. 按日期倒序输出 `look_back_days` 范围内的值
4. 对每个日期判断 N/A 原因：
   - `pd.isna(val)` → 调用 `cn_no_data_reason(date)`
     - 非交易日 → `"N/A：非交易日（A股休市）"`
     - 今日盘中 → `"N/A：今日盘中，日线未收盘（可参考实时价）"`
     - 今日未开盘 → `"N/A：今日尚未开盘"`
   - 日期不在数据集中（akshare 未返回该日） → 同上

**支持的指标：**
| 指标 | 说明 |
|------|------|
| `close_50_sma` | 50日均线 |
| `close_200_sma` | 200日均线 |
| `close_10_ema` | 10日EMA |
| `macd` / `macds` / `macdh` | MACD三线 |
| `rsi` | RSI |
| `boll` / `boll_ub` / `boll_lb` | 布林带 |
| `atr` | ATR |
| `vwma` | 成交量加权均线 |
| `mfi` | 资金流量指标 |

**`_fetch_hist_df` 原始返回格式：**
```
columns: ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
Date 类型: datetime64
Volume 类型: float

示例（600519, 2026-04-10 至 2026-04-14）：
        Date     Open     High     Low    Close   Volume
0 2026-04-10  1459.14  1459.71  1441.1  1453.96  28866.0
1 2026-04-13  1444.00  1446.50  1433.0  1443.31  25214.0
```

> **注意：** akshare 日K接口**不返回未收盘的当日数据**。今天盘中时，`_fetch_hist_df` 结果中不含今日行，因此 `values_by_date` 里没有今天的 key，最终由 `cn_no_data_reason` 填充为 `"N/A：今日盘中，日线未收盘（可参考实时价）"`。

**输出格式：**
```
## vwma 指标值（2026-03-25 至 2026-04-14）：

2026-04-14: N/A：今日盘中，日线未收盘（可参考实时价）
2026-04-13: 1440.91
2026-04-12: N/A：非交易日（A股休市）
...
2026-03-25: 1435.20

VWMA：成交量加权均线。
```

**数据窗口：** `look_back_days` 个自然日（含非交易日占位）

---

## 数据流向

```
┌─────────────────────────────────────────┐
│  smart_money_analyst_node               │
│  输入: state (ticker, current_date)     │
└─────────────────┬───────────────────────┘
                  │
                  ├─ 优先从 data_collector 缓存读取
                  │  pool["fund_flow_individual"]
                  │  pool["lhb"]
                  │  pool["indicators"]["vwma"]
                  │
                  ├─ 缓存未命中 → 并行调用3个工具
                  │  ├─ get_individual_fund_flow(symbol)
                  │  ├─ get_lhb_detail(symbol, date)
                  │  └─ get_indicators(symbol, "volume", date, 20)
                  │
                  ├─ 构建 Prompt
                  │  ├─ SystemMessage: smart_money_system_message
                  │  └─ HumanMessage: horizon_ctx + 3个数据块
                  │
                  ├─ LLM 流式生成分析报告
                  │  └─ Token级实时输出到 tracker
                  │
                  └─ 提取 verdict + confidence
                     └─ 返回 smart_money_report + analyst_traces
```

## 分析逻辑

1. 并行获取主力资金流向 + 龙虎榜 + vwma 指标
2. 结合用户意图构建 horizon 上下文
3. 调用 LLM 生成主力资金分析报告（`smart_money_report`）
4. 提取 `verdict` 和 `confidence`

## 输出结构

### `smart_money_report` (str)
LLM 生成的完整主力资金分析报告（中文），包含：
- 资金流向解读
- 龙虎榜席位分析
- 成交量异常判断

### `analyst_traces` (list)
```python
[{
    "agent": "smart_money_analyst",
    "horizon": "short",
    "data_window": "近期可用",
    "key_finding": "主力资金分析结论：看多/看空/中性",
    "verdict": "看多/看空/中性",
    "confidence": 0.75  # 0-1之间
}]
```

## 关键特性

- **并行获取**：3个数据源异步并发调用，提升速度
- **缓存优先**：优先使用 data_collector 预取的数据，减少重复请求
- **容错处理**：单个数据源失败返回"无数据"，不阻断整体分析
- **流式输出**：Token级实时流式输出到前端，提升用户体验
