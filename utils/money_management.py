"""
资金管理模块
包含本金设置、手续费计算、交易记录等功能
"""

import pandas as pd


def calculate_fee(amount: float, fee_rate: float) -> float:
    """
    计算手续费
    :param amount: 交易金额
    :param fee_rate: 手续费率
    :return: 手续费金额
    """
    return amount * fee_rate


def get_default_principal() -> float:
    """
    获取默认本金
    :return: 默认本金金额
    """
    return 100000.0  # 默认10万元


def get_default_fee_rate() -> float:
    """
    获取默认手续费率
    :return: 默认手续费率
    """
    return 0.001  # 默认0.1%


def calculate_return(principal: float, return_rate: float, fee_rate: float) -> dict:
    """
    计算收益情况
    :param principal: 本金
    :param return_rate: 收益率
    :param fee_rate: 手续费率
    :return: 包含收益信息的字典
    """
    gross_return = principal * return_rate  # 毛收益
    fee = principal * fee_rate * 2  # 买入和卖出两次手续费
    net_return = gross_return - fee  # 净收益
    net_return_rate = net_return / principal  # 净收益率
    
    return {
        'gross_return': gross_return,
        'fee': fee,
        'net_return': net_return,
        'net_return_rate': net_return_rate
    }


def validate_principal(principal: str) -> float:
    """
    验证并转换本金输入
    :param principal: 本金字符串
    :return: 验证后的本金金额
    """
    try:
        value = float(principal)
        if value <= 0:
            return get_default_principal()
        return value
    except (ValueError, TypeError):
        return get_default_principal()


def validate_fee_rate(fee_rate: str) -> float:
    """
    验证并转换手续费率输入
    :param fee_rate: 手续费率字符串
    :return: 验证后的手续费率
    """
    try:
        value = float(fee_rate)
        if value < 0:
            return get_default_fee_rate()
        return value
    except (ValueError, TypeError):
        return get_default_fee_rate()


def calculate_buy_and_hold_return(btc_df: pd.DataFrame, principal: float, fee_rate: float) -> dict:
    """
    计算从第一个交易日买入并持有到最后一个交易日的收益情况
    :param btc_df: BTC数据DataFrame
    :param principal: 本金
    :param fee_rate: 手续费率
    :return: 包含收益信息的字典
    """
    if len(btc_df) < 2:
        return {
            'buy_date': None,
            'buy_price': 0.0,
            'sell_date': None,
            'sell_price': 0.0,
            'principal': principal,
            'return': 0.0,
            'return_rate': 0.0,
            'fee': 0.0,
            'buy_fee': 0.0,
            'sell_fee': 0.0,
            'hold_days': 0
        }
    
    # 第一天买入
    buy_date = btc_df.iloc[0]['交易时间']
    buy_price = btc_df.iloc[0]['收盘价']
    buy_amount = principal
    buy_fee = calculate_fee(buy_amount, fee_rate)
    
    # 最后一天卖出
    sell_date = btc_df.iloc[-1]['交易时间']
    sell_price = btc_df.iloc[-1]['收盘价']
    sell_amount = principal * (sell_price / buy_price)
    sell_fee = calculate_fee(sell_amount, fee_rate)
    
    # 计算盈亏
    total_fee = buy_fee + sell_fee
    trade_return = sell_amount - buy_amount - total_fee
    trade_return_rate = trade_return / principal
    
    # 计算持仓天数
    hold_days = len(btc_df) - 1
    
    return {
        'buy_date': buy_date,
        'buy_price': buy_price,
        'sell_date': sell_date,
        'sell_price': sell_price,
        'principal': principal,
        'return': trade_return,
        'return_rate': trade_return_rate * 100,  # 转换为百分比
        'fee': total_fee,
        'buy_fee': buy_fee,
        'sell_fee': sell_fee,
        'hold_days': hold_days
    }


def calculate_trade_details(btc_df: pd.DataFrame, signals: pd.Series, principal: float, fee_rate: float) -> dict:
    """
    计算每一笔交易的详细信息
    :param btc_df: BTC数据DataFrame
    :param signals: 交易信号Series
    :param principal: 本金
    :param fee_rate: 手续费率
    :return: 包含交易详情和总体盈亏的字典
    """
    trades = []
    total_return = 0.0
    total_fee = 0.0
    position = 0  # 0表示空仓，1表示持仓
    buy_price = 0.0
    buy_date = None
    buy_index = 0  # 记录买入时的索引位置
    
    for i in range(len(signals)):
        signal = signals.iloc[i]
        date = btc_df.iloc[i]['交易时间']
        price = btc_df.iloc[i]['收盘价']
        
        # 买入信号且当前空仓
        if signal == 1.0 and position == 0:
            buy_price = price
            buy_date = date
            buy_index = i  # 记录买入时的索引位置
            buy_amount = principal
            buy_fee = calculate_fee(buy_amount, fee_rate)
            total_fee += buy_fee
            position = 1
            
        # 卖出信号且当前持仓
        elif signal == 0.0 and position == 1:
            sell_price = price
            sell_date = date
            sell_amount = principal * (sell_price / buy_price)
            sell_fee = calculate_fee(sell_amount, fee_rate)
            total_fee += sell_fee
            
            # 计算盈亏
            trade_return = sell_amount - buy_amount - buy_fee - sell_fee
            trade_return_rate = trade_return / principal
            
            # 计算持仓天数
            hold_days = i - buy_index
            
            # 记录交易详情
            trades.append({
                'buy_date': buy_date,
                'buy_price': buy_price,
                'sell_date': sell_date,
                'sell_price': sell_price,
                'principal': principal,
                'return': trade_return,
                'return_rate': trade_return_rate * 100,  # 转换为百分比
                'fee': buy_fee + sell_fee,
                'buy_fee': buy_fee,
                'sell_fee': sell_fee,
                'hold_days': hold_days  # 持仓天数
            })
            
            total_return += trade_return
            position = 0
    
    # 如果最后还有持仓，计算到最后一日的收益
    if position == 1 and len(btc_df) > 0:
        last_price = btc_df.iloc[-1]['收盘价']
        last_date = btc_df.iloc[-1]['交易时间']
        sell_amount = principal * (last_price / buy_price)
        sell_fee = calculate_fee(sell_amount, fee_rate)
        total_fee += sell_fee
        
        # 计算盈亏
        trade_return = sell_amount - principal - buy_fee - sell_fee
        trade_return_rate = trade_return / principal
        
        # 计算持仓天数
        hold_days = len(btc_df) - 1 - buy_index
        
        # 记录交易详情
        trades.append({
            'buy_date': buy_date,
            'buy_price': buy_price,
            'sell_date': last_date,
            'sell_price': last_price,
            'principal': principal,
            'return': trade_return,
            'return_rate': trade_return_rate * 100,  # 转换为百分比
            'fee': buy_fee + sell_fee,
            'buy_fee': buy_fee,
            'sell_fee': sell_fee,
            'hold_days': hold_days  # 持房天数
        })
        
        total_return += trade_return
    
    # 计算总体盈亏
    total_return_rate = total_return / principal if principal > 0 else 0
    
    # 计算胜率和盈亏比
    winning_trades = 0  # 盈利交易数
    total_winning = 0.0  # 总盈利
    total_losing = 0.0  # 总亏损
    
    for trade in trades:
        if trade['return'] > 0:
            winning_trades += 1
            total_winning += trade['return']
        else:
            total_losing += abs(trade['return'])
    
    # 胜率
    win_rate = winning_trades / len(trades) if trades else 0
    
    # 盈亏比（总盈利/总亏损）
    profit_loss_ratio = total_winning / total_losing if total_losing > 0 else float('inf')
    
    return {
        'trades': trades,
        'total_return': total_return,
        'total_return_rate': total_return_rate * 100,  # 转换为百分比
        'total_fee': total_fee,
        'trade_count': len(trades),
        'win_rate': win_rate,  # 胜率
        'profit_loss_ratio': profit_loss_ratio  # 盈亏比
    }