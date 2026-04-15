"""测试 Volume Price Analyst 使用的数据源（vpa_indicators + stock_data）"""
import asyncio
from datetime import datetime


def _get_df(ticker, date, look_back_days=30):
    """获取原始 OHLCV DataFrame"""
    from tradingagents.agents.utils.agent_utils import get_stock_data
    from datetime import datetime, timedelta
    import pandas as pd

    end_date = date
    start_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=look_back_days + 10)).strftime("%Y-%m-%d")
    result = get_stock_data.invoke({"symbol": ticker, "start_date": start_date, "end_date": end_date})
    return result


def test_stock_data(ticker="600519", date=None, look_back_days=30):
    """测试原始 K 线数据获取"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"测试 get_stock_data: {ticker} @ {date}, 回溯{look_back_days}天")
    print(f"{'='*60}\n")

    try:
        result = _get_df(ticker, date, look_back_days)
        print(result)
        print(f"\n返回长度: {len(result)} 字符")
    except Exception as exc:
        print(f"调用失败：{exc}")


def test_vpa_indicators(ticker="600519", date=None, look_back_days=30):
    """测试 vpa_indicators 预计算（直接调用 _compute_vpa_indicators）"""
    import io
    import pandas as pd
    from datetime import datetime, timedelta
    from tradingagents.graph.data_collector import _compute_vpa_indicators, _parse_csv_to_dataframe
    from tradingagents.agents.utils.agent_utils import get_stock_data

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"测试 _compute_vpa_indicators: {ticker} @ {date}, 回溯{look_back_days}天")
    print(f"{'='*60}\n")

    try:
        start_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=look_back_days + 10)).strftime("%Y-%m-%d")
        raw_csv = get_stock_data.invoke({"symbol": ticker, "start_date": start_date, "end_date": date})

        df = _parse_csv_to_dataframe(raw_csv)
        if df is None or df.empty:
            print("获取 DataFrame 失败，无法计算 VPA 指标")
            return

        print(f"原始数据形状: {df.shape}")
        print(f"列名: {list(df.columns)}")
        print(f"最近3行:\n{df.tail(3)}\n")

        result = _compute_vpa_indicators(df.copy())
        print(result)
        print(f"\n返回长度: {len(result)} 字符")

    except Exception as exc:
        import traceback
        print(f"调用失败：{exc}")
        traceback.print_exc()


def test_all(ticker="600519", date=None):
    """测试所有数据源（模拟 Volume Price Analyst 实际调用）"""
    import time

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"完整测试 Volume Price Analyst 数据源: {ticker} @ {date}")
    print(f"{'='*60}\n")

    start = time.time()
    test_stock_data(ticker, date)
    test_vpa_indicators(ticker, date)
    print(f"\n⏱️  总耗时: {time.time() - start:.2f}秒")


def test_realtime_row(ticker="600519"):
    """测试 _fetch_realtime_row 今日实时数据（需要 XQ_A_TOKEN）"""
    import os
    from tradingagents.dataflows.providers.cn_akshare_provider import CnAkshareProvider

    print(f"\n{'='*60}")
    print(f"测试 _fetch_realtime_row: {ticker}")
    print(f"XQ_A_TOKEN: {'已设置' if os.environ.get('XQ_A_TOKEN') else '未设置（将失败）'}")
    print(f"{'='*60}\n")

    try:
        p = CnAkshareProvider()
        rt = p._fetch_realtime_row(ticker)
        if rt.empty:
            print("返回空 DataFrame（接口失败或非交易时段）")
        else:
            print(rt.to_string())
            vol = rt.iloc[0]["Volume"]
            print(f"\n⚠️  注意：雪球成交量单位为【股】，历史数据单位为【手(100股)】")
            print(f"   原始 volume={vol:.0f} 股 ≈ {vol/100:.0f} 手")
    except Exception as exc:
        import traceback
        print(f"调用失败：{exc}")
        traceback.print_exc()


def test_akshare_raw(ticker="600519", date=None, look_back_days=30):
    """测试 akshare 3个原始接口返回的数据格式"""
    import akshare as ak
    from datetime import datetime, timedelta

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    start_date = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=look_back_days)).strftime("%Y-%m-%d")
    date_fmt = date.replace("-", "")
    start_fmt = start_date.replace("-", "")

    # 1. stock_zh_a_hist
    print(f"\n{'='*60}")
    print(f"测试 ak.stock_zh_a_hist: {ticker} [{start_date} ~ {date}]")
    print(f"{'='*60}\n")
    try:
        df = ak.stock_zh_a_hist(symbol=ticker, period="daily", start_date=start_fmt, end_date=date_fmt, adjust="")
        print(f"形状: {df.shape}, 列名: {list(df.columns)}")
        print(df.tail(3).to_string())
    except Exception as exc:
        print(f"失败: {exc}")

    # 2. stock_zh_a_daily
    print(f"\n{'='*60}")
    print(f"测试 ak.stock_zh_a_daily: {ticker} [{start_date} ~ {date}]")
    print(f"{'='*60}\n")
    try:
        df = ak.stock_zh_a_daily(symbol=ticker, start_date=start_fmt, end_date=date_fmt, adjust="")
        print(f"形状: {df.shape}, 列名: {list(df.columns)}")
        print(df.tail(3).to_string())
    except Exception as exc:
        print(f"失败: {exc}")

    # 3. stock_zh_a_hist_tx
    print(f"\n{'='*60}")
    print(f"测试 ak.stock_zh_a_hist_tx: {ticker} [{start_date} ~ {date}]")
    print(f"{'='*60}\n")
    try:
        df = ak.stock_zh_a_hist_tx(symbol=ticker, start_date=start_date, end_date=date)
        print(f"形状: {df.shape}, 列名: {list(df.columns)}")
        print(df.tail(3).to_string())
    except Exception as exc:
        print(f"失败: {exc}")


def print_usage():
    print("""
使用方法:

1. 测试单个数据源:
   python tests/test_volume_price_data.py stock_data [股票代码] [日期] [回溯天数]
   python tests/test_volume_price_data.py vpa [股票代码] [日期] [回溯天数]
   python tests/test_volume_price_data.py akshare_raw [股票代码] [日期] [回溯天数]

2. 测试所有数据源:
   python tests/test_volume_price_data.py all [股票代码] [日期]

3. 运行所有测试（默认）:
   python tests/test_volume_price_data.py

示例:
   python tests/test_volume_price_data.py stock_data 000001
   python tests/test_volume_price_data.py vpa 600519 2026-04-10 30
   python tests/test_volume_price_data.py akshare_raw 600519 2026-04-10 30
   python tests/test_volume_price_data.py all 600519
""")


if __name__ == "__main__":
    import sys

    ticker = "600036"
    date = datetime.now().strftime("%Y-%m-%d")

    print_usage()

    if len(sys.argv) > 1:
        command = sys.argv[1]
        ticker = sys.argv[2] if len(sys.argv) > 2 else ticker
        date = sys.argv[3] if len(sys.argv) > 3 else date
        look_back = int(sys.argv[4]) if len(sys.argv) > 4 else 30

        if command == "stock_data":
            test_stock_data(ticker, date, look_back)
        elif command == "vpa":
            test_vpa_indicators(ticker, date, look_back)
        elif command == "realtime":
            test_realtime_row(ticker)
        elif command == "akshare_raw":
            test_akshare_raw(ticker, date, look_back)
        elif command == "all":
            test_all(ticker, date)
        else:
            print(f"未知命令: {command}")
    else:
        test_all(ticker, date)
