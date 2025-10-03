import finplot as fplt
import pandas as pd
from indicators import calculate_macd  # 导入MACD计算函数

#可用
df = pd.read_csv('/Users/mac/Documents/QT/数据/btc_data_1d.csv')
df = df.rename(columns={'交易时间': 'time', '开盘价': 'open', '最高价': 'high', '最低价': 'low', '收盘价': 'close', '成交量': 'volume'})
df['time'] = pd.to_datetime(df['time'])
df = df.set_index('time')

# 计算MACD指标
df = calculate_macd(df)

# 创建图表
ax, ax2, ax3 = fplt.create_plot('BTC Daily K-Line', rows=3)
fplt.candlestick_ochl(df[['open', 'close', 'high', 'low']], ax=ax)
fplt.volume_ocv(df[['open', 'close', 'volume']], ax=ax2)

# 绘制MACD
fplt.plot(df['macd'], ax=ax3, legend='MACD')
fplt.plot(df['signal'], ax=ax3, legend='Signal')
fplt.volume_ocv(df[['open','close','hist']], ax=ax3, colorfunc=fplt.strength_colorfilter)

fplt.show()