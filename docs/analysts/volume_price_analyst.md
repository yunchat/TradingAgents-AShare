# 量价分析师 (Volume Price Analyst)

## 角色定位

专注量价关系分析，通过预计算的量价指标和原始 K 线数据判断短期量价信号。

## 时间视角

固定**短期**（short，14 天窗口）

## 数据源详解

**注意**：量价分析师仅从 `data_collector` 缓存池读取数据，**无独立 fallback 工具调用**。若缓存池不存在或无对应字段，则数据为"无数据"。

### 1. 量价预计算指标 (`vpa_indicators`)

**来源：** `data_collector.py` 中的 `_compute_vpa_indicators(df)` 函数

**底层数据：** 基于 akshare `stock_zh_a_hist` 拉取的 OHLCV 日K数据，**不调用额外 API**

**包含指标：**

| 指标 | 说明 |
|------|------|
| `vol_ma` | 20日滚动均量 |
| `volume_ratio` | 当日量 / `vol_ma`（量比） |
| `bar_spread` | (high - low) / close（K线实体相对大小） |
| `close_position` | 收盘价在高低范围内的位置（0-1，越高越强） |
| `bar_type` | K线类型：阳线 / 阴线 / 十字星 |
| `upper_shadow` | 上影线比例（相对高低范围） |
| `lower_shadow` | 下影线比例（相对高低范围） |
| `pct_change` | 日涨跌幅 |
| `vol_ma5` | 5日滚动均量 |
| `vol_trend_ratio` | `vol_ma5` / `vol_ma`（短期量能趋势） |
| `vp_harmony` | 量价关系标签（一致(涨+放量) / 背离(涨+缩量) 等） |
| `obv` | OBV 能量潮（累计），含10日MA趋势标签（上升/下降） |

**模式识别（文本标注）：**
- 顶部背离（价涨量缩）
- 底部放量（潜在反转）
- 卖出高潮（放量大跌）
- 放量滞涨（上涨乏力）

**输出格式（纯文本 Markdown）：**
```
## VPA 预计算指标（基于 20 日均量基准）

**OBV 趋势（10日）**: 上升
**近5日量能趋势**: 放量（5日均量/20日均量 = 1.35）

### 逐日量价数据

| 日期  | 类型 | 涨跌幅 | 实体大小    | 收盘位置    | 上影线 | 下影线 | 量比        | 量价关系      |
|-------|------|--------|-------------|-------------|--------|--------|-------------|---------------|
| 04-10 | 阳线 | +1.2%  | 中(0.022)   | 高位(0.75)  | 0.10   | 0.15   | 1.3(温和放量) | 一致(涨+放量) |
...

### 关键量价模式识别

- 健康上涨信号: 近5日价格上涨且成交量配合递增
```

**数据窗口：** 最近 30 个交易日（由 `get_window()` 裁剪为 14 天窗口传入 LLM）

---

### 2. 原始 K 线数据 (`stock_data`)

**来源：** `data_collector` 缓存池中的 `stock_data` 字段

**说明：** 与 `market_analyst` 使用的同一份日K数据，作为参考背景传入 LLM

> **时间维度注意：** `stock_data` 包含当日盘中实时数据（未收盘），而 `vpa_indicators` 基于历史已收盘数据计算，两者最新时间点不一致。

---

## 数据流向

```
┌─────────────────────────────────────────┐
│  volume_price_analyst_node              │
│  输入: state (ticker, current_date)     │
└─────────────────┬───────────────────────┘
                  │
                  ├─ data_collector.get_window(pool, "short", current_date)
                  │  ├─ windowed["vpa_indicators"]  → 量价预计算指标
                  │  ├─ windowed["stock_data"]       → 原始K线（参考）
                  │  └─ windowed["_data_window"]     → 数据窗口描述（默认"14天"）
                  │
                  ├─ 构建 Prompt
                  │  ├─ SystemMessage: horizon_ctx + volume_price_system_message
                  │  └─ HumanMessage: vpa_data + stock_data
                  │
                  ├─ LLM 流式生成分析报告
                  │  └─ Token级实时输出到 tracker
                  │
                  └─ 提取 verdict + confidence
                     └─ 返回 volume_price_report + analyst_traces
```

## 分析逻辑

1. 从 `data_collector.get_window()` 获取窗口化的量价指标和 K 线数据
2. 结合用户意图构建 horizon 上下文
3. 调用 LLM 生成量价分析报告（`volume_price_report`）
4. 提取 `verdict` 和 `confidence`

## 输出结构

### `volume_price_report` (str)
LLM 生成的完整量价分析报告（中文），包含：
- OBV 趋势与量能判断
- 逐日量价关系解读
- 关键量价模式识别与信号

### `analyst_traces` (list)
```python
[{
    "agent": "volume_price_analyst",
    "horizon": "short",
    "data_window": "14天",
    "key_finding": "量价分析结论：看多/看空/中性",
    "verdict": "看多/看空/中性",
    "confidence": 0.75  # 0-1之间
}]
```

## 关键特性

- **无 fallback**：完全依赖 data_collector 预计算，无独立 API 调用
- **纯计算指标**：vpa_indicators 基于 OHLCV 本地计算，无额外网络请求
- **流式输出**：Token 级实时流式输出到前端
