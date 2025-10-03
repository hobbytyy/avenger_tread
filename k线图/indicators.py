import pandas as pd
import numpy as np

def calculate_macd(df, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    df['macd'] = df['close'].ewm(span=fast).mean() - df['close'].ewm(span=slow).mean()
    df['signal'] = df['macd'].ewm(span=signal).mean()
    df['hist'] = df['macd'] - df['signal']
    return df

def calculate_ema(df, periods=[5, 10, 20]):
    """计算多个周期的EMA均线"""
    for period in periods:
        df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
    return df

def calculate_bollinger_bands(df, period=20, std_multiplier=2):
    """
    计算布林带指标
    
    参数:
    df: DataFrame, 必须包含'close'列
    period: int, 移动平均的周期，默认20
    std_multiplier: float, 标准差的倍数，默认2
    
    返回:
    添加了布林带指标的DataFrame，包含：
    - bb_middle: 中轨（简单移动平均线）
    - bb_upper: 上轨
    - bb_lower: 下轨
    """
    # 计算中轨（简单移动平均线）
    df['bb_middle'] = df['close'].rolling(window=period).mean()
    
    # 计算标准差
    rolling_std = df['close'].rolling(window=period).std()
    
    # 计算上轨和下轨
    df['bb_upper'] = df['bb_middle'] + (rolling_std * std_multiplier)
    df['bb_lower'] = df['bb_middle'] - (rolling_std * std_multiplier)
    
    return df