import time
import requests
from datetime import datetime
import numpy as np
import pandas as pd
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://api.binance.com"
REQ_LIMIT = 1000
SUPPORT_INTERVAL = {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"}


def get_support_symbols():
    try:
        res = []
        end_point = "/api/v3/exchangeInfo"
        resp = requests.get(BASE_URL + end_point, timeout=10)
        for symbol_info in resp.json()["symbols"]:
            if symbol_info["status"] == "TRADING":
                symbol = "{}/{}".format(symbol_info["baseAsset"].upper(), symbol_info["quoteAsset"].upper())
                res.append(symbol)
        return res
    except Exception as e:
        print(f"获取交易对列表失败: {e}")
        return []


def get_klines(symbol, interval='1h', since=None, limit=1000, to=None):
    try:
        end_point = "/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        # 只有当since和to不为None时才添加到参数中
        if since is not None:
            params['startTime'] = int(since * 1000)  # 转换为毫秒
        if to is not None:
            params['endTime'] = int(to * 1000)  # 转换为毫秒
        
        # 创建一个带有重试策略的会话
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        resp = session.get(BASE_URL + end_point, params=params, timeout=30)
        return resp.json()
    except Exception as e:
        print(f"获取K线数据失败: {e}")
        return []


def download_full_klines(symbol, interval, start, end=None, save_to=None, req_interval=None, dimension="ohlcv"):
    if interval not in SUPPORT_INTERVAL:
        raise Exception("interval {} is not support!!!".format(interval))
    start_end_pairs = get_start_end_pairs(start, end, interval)
    klines = []

    print(f"开始下载 {symbol} 的 {interval} 数据...")
    for i, (start_ts, end_ts) in enumerate(start_end_pairs):
        print(f"正在下载第 {i+1}/{len(start_end_pairs)} 批数据...")
        tmp_kline = get_klines(symbol.replace("/", ""), interval, since=start_ts, limit=REQ_LIMIT, to=end_ts)
        if len(tmp_kline) > 0:
            klines.append(tmp_kline)
        else:
            print(f"第 {i+1} 批数据下载失败或无数据")
        if req_interval:
            time.sleep(req_interval)

    if not klines:
        print("未获取到任何数据")
        return

    klines = np.concatenate(klines)
    data = []
    cols = ["open_time", "open", "high", "low", "close", "volume",
            "close_time", "value", "trade_cnt",
            "active_buy_volume", "active_buy_value"]

    for i in range(len(klines)):
        tmp_kline = klines[i]
        data.append(tmp_kline[:-1])

    df = pd.DataFrame(np.array(data), columns=cols, dtype=float)
    df.drop("close_time", axis=1, inplace=True)
    for col in cols:
        if col in ["open_time", "trade_cnt"]:
            df[col] = df[col].astype(int)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")

    if dimension == "ohlcv":
        df = df[cols[:6]]

    # 将列名改为中文
    df.rename(columns={
        "open_time": "交易日期",
        "open": "开盘价",
        "high": "最高价",
        "low": "最低价",
        "close": "收盘价",
        "volume": "成交量"
    }, inplace=True)

    real_start = df["交易日期"].iloc[0].strftime("%Y-%m-%d")
    real_end = df["交易日期"].iloc[-1].strftime("%Y-%m-%d")

    # 如果没有指定保存路径，则使用默认路径和文件名格式
    if save_to is None:
        # 获取项目根目录下的数据文件夹路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, "数据")
        
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 生成文件名：交易对的基础货币名称_data_时间间隔.csv
        base_symbol = symbol.replace("/", "-").split("-")[0].lower()  # 获取交易对的基础货币名称
        save_to = os.path.join(data_dir, "{}_data_{}.csv".format(base_symbol, interval))
    
    df.to_csv(save_to, index=False)
    print(f"数据已保存至: {save_to}")
    print(f"共下载 {len(df)} 条数据记录")


def get_start_end_pairs(start, end, interval):
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    if end is None:
        end_dt = datetime.now()
    else:
        end_dt = datetime.strptime(end, "%Y-%m-%d")
    start_dt_ts = int(time.mktime(start_dt.timetuple()))
    end_dt_ts = int(time.mktime(end_dt.timetuple()))

    ts_interval = interval_to_seconds(interval)

    res = []
    cur_start = cur_end = start_dt_ts
    while cur_end < end_dt_ts - ts_interval:
        cur_end = min(end_dt_ts, cur_start + (REQ_LIMIT - 1) * ts_interval)
        res.append((cur_start, cur_end))
        cur_start = cur_end + ts_interval
    return res


def interval_to_seconds(interval):
    seconds_per_unit = {"m": 60, "h": 60 * 60, "d": 24 * 60 * 60, "w": 7 * 24 * 60 * 60, "M": 30 * 24 * 60 * 60}
    return int(interval[:-1]) * seconds_per_unit[interval[-1]]


# 注释掉自动运行的代码，避免在导入时自动执行
"""
if __name__ == '__main__':
    # 示例：下载BTC月线数据（少量数据用于测试）
    print("开始下载BTC测试数据...")
    download_full_klines(symbol="BTC/USDT", interval="1M", start="2023-01-01", end="2023-12-31")
    print("BTC测试数据下载完成")
"""

# 如果需要测试，可以取消注释上面的代码或创建单独的测试脚本
