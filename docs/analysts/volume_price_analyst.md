# 量价分析师 (Volume Price Analyst)

## 角色定位

专注量价关系分析，通过预计算的量价指标和原始 K 线数据判断短期量价信号。

## 时间视角

固定**短期**（short，14 天窗口）

## 数据源

| 数据 | 工具/字段 | 说明 |
|------|-----------|------|
| 量价预计算指标 | `pool["vpa_indicators"]` | 由 data_collector 预计算的量价分析指标 |
| K 线数据 | `pool["stock_data"]` | 原始日 K 线数据（参考用） |

**注意**：量价分析师仅从 `data_collector` 缓存池读取数据，无独立 fallback 工具调用。若缓存池不存在或无对应字段，则数据为"无数据"。

## 分析逻辑

1. 从 `data_collector.get_window()` 获取窗口化的量价指标和 K 线数据
2. 结合用户意图构建 horizon 上下文
3. 调用 LLM 生成量价分析报告（`volume_price_report`）
4. 提取 `verdict` 和 `confidence`

## 输出

- `volume_price_report`：完整量价分析报告
- `analyst_traces`：包含 agent 名、horizon、数据窗口、结论、置信度
