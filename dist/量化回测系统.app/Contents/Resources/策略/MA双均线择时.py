import pandas as pd
import numpy as np

# 策略描述
STRATEGY_DESCRIPTION = "双均线择时策略：通过计算短期和长期均线的交叉来产生买卖信号。当短期均线上穿长期均线时买入，下穿时卖出。"

# 策略参数描述
STRATEGY_PARAM_DESCRIPTIONS = [
    "短期均线周期(如: 5)",
    "长期均线周期(如: 20)",
    "本金金额(如: 100000)",
    "手续费率(如: 0.001)",
    "参数 5"
]

def equity_signal(btc_df: pd.DataFrame, *args) -> pd.Series:
    """
    根据BTC数据，使用短期和长期均线择时信号
    :param btc_df: 包含 BTC 数据的 DataFrame，必须包含 '收盘价' 列
    :param args: 均线参数 
                 args[0]=短期均线周期，
                 args[1]=长期均线周期，
                 args[2]=本金金额（可选），
                 args[3]=手续费率（可选）
    :return: 返回包含信号的 Series（1=做多，0=空仓）
    """
    # ===== 获取策略参数
    short_n = int(args[0])  # 短期均线周期，例如5表示5日均线
    long_n = int(args[1])  # 长期均线周期，例如20表示20日均线
    # 本金和手续费参数是可选的，用于后续的收益计算
    principal = float(args[2]) if len(args) > 2 and args[2] else 100000.0  # 默认本金10万元
    fee_rate = float(args[3]) if len(args) > 3 and args[3] else 0.001  # 默认手续费率0.1%

    # ===== 计算均线
    ma_short = btc_df['收盘价'].rolling(short_n, min_periods=1).mean()
    ma_long = btc_df['收盘价'].rolling(long_n, min_periods=1).mean()

    # ===== 初始化信号 Series，默认空仓
    signals = pd.Series(np.nan, index=btc_df.index)

    # ===== 找出金叉买入信号（短期均线上穿长期均线）
    condition_buy = (ma_short > ma_long) & (ma_short.shift(1) <= ma_long.shift(1))
    signals[condition_buy] = 1.0

    # ===== 找出死叉平仓信号（短期均线下穿长期均线）
    condition_sell = (ma_short < ma_long) & (ma_short.shift(1) >= ma_long.shift(1))
    signals[condition_sell] = 0.0

    # ===== 持续持仓：将前一日信号延续到当前（信号填充）
    signals = signals.ffill().fillna(1)  # 默认开仓
    return signals