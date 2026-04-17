# stock_data Markdown 化优化方案

## 问题

`stock_data` 是原始 CSV 字符串，盘中时最后一行 close/high/low/volume 均为未完成值，LLM 无感知，可能基于未完成数据做出错误技术判断。

## 消费方

| 文件 | 用途 | 当前处理 |
|------|------|---------|
| `market_analyst.py:61` | 主要 K 线数据，与技术指标并列 | 原样传入，无盘中处理 |
| `volume_price_analyst.py:64,71` | 辅助参考，附在 vpa_indicators 后 | 原样传入，无盘中处理 |

## 方案

### 新增 `stock_data_to_markdown`（放在 `data_collector.py`）

- 复用已有的 `_parse_csv_to_dataframe`、`_intraday_label`、`cn_today_str`
- 盘中：拆为"历史 K 线（已确认）"和"今日盘中 K 线（未完成）"两个表格，今日行日期附带 `_intraday_label` 返回的时间标注
- 盘后：单一 Markdown 表格，无标注

### 输出示例（盘中 13:40）

```
#### 历史 K 线（已确认）
| 日期 | 开盘 | 最高 | 最低 | 收盘 | 成交量 |
|------|------|------|------|------|--------|
| 04-14 | 91.68 | 97.54 | 90.88 | 97.54 | 93,744,080 |
| 04-15 | 98.60 | 99.13 | 92.00 | 92.78 | 133,625,801 |

#### 今日盘中 K 线（未完成，盘中13:40,约67%）
| 日期 | 开盘 | 最高(临时) | 最低(临时) | 当前价(临时) | 当前量 |
|------|------|-----------|-----------|------------|--------|
| 04-16(盘中13:40,约67%) | 92.25 | 95.46 | 91.91 | 94.40 | 77,292,906 |
> close/high/low/volume 为截至当前临时值。
```

### 输出示例（盘后）

```
| 日期 | 开盘 | 最高 | 最低 | 收盘 | 成交量 |
|------|------|------|------|------|--------|
| 04-14 | 91.68 | 97.54 | 90.88 | 97.54 | 93,744,080 |
| 04-15 | 98.60 | 99.13 | 92.00 | 92.78 | 133,625,801 |
| 04-16 | 92.25 | 95.46 | 91.91 | 94.40 | 115,362,546 |
```

## 改动范围

| 文件 | 改动 |
|------|------|
| `data_collector.py` | 新增 `stock_data_to_markdown` 函数 |
| `market_analyst.py` | import + 替换 `stock_data` → `stock_data_to_markdown(stock_data)` |
| `volume_price_analyst.py` | import + 替换两处 `stock_data` → `stock_data_to_markdown(stock_data)` |

## 完整函数实现

```python
def stock_data_to_markdown(raw_csv: str) -> str:
    df = _parse_csv_to_dataframe(raw_csv)
    if df is None or df.empty:
        return raw_csv

    intraday_label, is_intraday = _intraday_label()
    today_str = cn_today_str()

    last_dt = df.iloc[-1].get("date", "")
    last_dt_str = last_dt.strftime("%Y-%m-%d") if hasattr(last_dt, "strftime") else str(last_dt)
    is_today_last = is_intraday and last_dt_str == today_str

    def _row(r, label=""):
        dt = r.get("date", "")
        dt_s = (dt.strftime("%m-%d") if hasattr(dt, "strftime") else str(dt)[-5:]) + label
        vol = f"{int(r['volume']):,}" if pd.notna(r.get("volume")) else "-"
        return f"| {dt_s} | {r['open']:.2f} | {r['high']:.2f} | {r['low']:.2f} | {r['close']:.2f} | {vol} |"

    header  = "| 日期 | 开盘 | 最高 | 最低 | 收盘 | 成交量 |\n|------|------|------|------|------|--------|"
    h_today = "| 日期 | 开盘 | 最高(临时) | 最低(临时) | 当前价(临时) | 当前量 |\n|------|------|-----------|-----------|------------|--------|"

    if is_today_last:
        hist = "\n".join(_row(r) for _, r in df.iloc[:-1].iterrows())
        last_row = _row(df.iloc[-1], intraday_label)
        label_clean = intraday_label.strip("()")
        return (
            f"#### 历史 K 线（已确认）\n{header}\n{hist}\n\n"
            f"#### 今日盘中 K 线（未完成，{label_clean}）\n{h_today}\n{last_row}\n"
            "> close/high/low/volume 为截至当前临时值。"
        )

    return f"{header}\n" + "\n".join(_row(r) for _, r in df.iterrows())
```
