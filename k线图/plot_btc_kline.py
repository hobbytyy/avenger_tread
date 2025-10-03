import finplot as fplt
import pandas as pd
from indicators import calculate_macd, calculate_ema

# 读取数据
df = pd.read_csv('/Users/mac/Documents/QT/数据/btc_data_1d.csv')

# 重命名列以适配finplot
df = df.rename(columns={
    '交易时间': 'time',
    '开盘价': 'open',
    '最高价': 'high',
    '最低价': 'low',
    '收盘价': 'close',
    '成交量': 'volume'
})

# 转换时间格式
df['time'] = pd.to_datetime(df['time'])

# 计算技术指标
df = calculate_macd(df)  # 计算MACD
df = calculate_ema(df)   # 计算EMA均线

# 创建三个子图：K线图、成交量图和MACD图
ax0, ax1, ax2 = fplt.create_plot('BTC/USDT 日K线', rows=3)

# 绘制K线图和EMA均线
fplt.candlestick_ochl(df[['time', 'open', 'close', 'high', 'low']], ax=ax0)
fplt.plot(df['time'], df['ema_5'], ax=ax0, legend='EMA5', color='#ff0000')
fplt.plot(df['time'], df['ema_10'], ax=ax0, legend='EMA10', color='#00ff00')
fplt.plot(df['time'], df['ema_20'], ax=ax0, legend='EMA20', color='#0000ff')

# 绘制成交量图
fplt.volume_ocv(df[['time', 'open', 'close', 'volume']], ax=ax1)

# 绘制MACD图
fplt.volume_ocv(df[['time', 'open', 'close', 'hist']], ax=ax2, colorfunc=fplt.strength_colorfilter)
fplt.plot(df['time'], df['macd'], ax=ax2, legend='MACD', color='#0000ff')
fplt.plot(df['time'], df['signal'], ax=ax2, legend='Signal', color='#ff0000')

fplt.show()