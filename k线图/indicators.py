import pandas as pd

def calculate_macd(df, fast=12, slow=26, signal=9):
    df['macd'] = df['close'].ewm(span=fast).mean() - df['close'].ewm(span=slow).mean()
    df['signal'] = df['macd'].ewm(span=signal).mean()
    df['hist'] = df['macd'] - df['signal']
    return df

def calculate_ema(df, periods=[5, 10, 20]):
    """
    计算多个周期的EMA均线
    
    参数:
    df: DataFrame, 必须包含'close'列
    periods: list, EMA的周期列表，默认为[5, 10, 20]
    
    返回:
    添加了EMA列的DataFrame
    """
    for period in periods:
        df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
    return df