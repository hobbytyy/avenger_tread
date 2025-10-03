import pandas as pd

def calculate_macd(df, fast=12, slow=26, signal=9):
    df['macd'] = df['close'].ewm(span=fast).mean() - df['close'].ewm(span=slow).mean()
    df['signal'] = df['macd'].ewm(span=signal).mean()
    df['hist'] = df['macd'] - df['signal']
    return df