"""
参数优化策略
通过遍历不同的参数组合，寻找最优的策略参数配置
"""

import pandas as pd
import numpy as np
from itertools import product
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
import time  # 添加时间模块用于性能测试

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 导入资金管理模块
from utils.money_management import calculate_trade_details

# 策略描述
STRATEGY_DESCRIPTION = "参数优化策略：通过遍历不同的参数组合，寻找最优的策略参数配置，适用于各种金融数据类型。支持生成所有可能的短期和长期均线组合（短期 < 长期）。"

# 策略参数描述
STRATEGY_PARAM_DESCRIPTIONS = [
    "优化策略名称(默认: MA双均线择时)",
    "参数范围开始值(如: 5)",
    "参数范围结束值(如: 60)",
    "本金金额(如: 100000)",
    "手续费率(如: 0.001)"
]

def parse_param_range(range_str: str) -> range:
    """
    解析参数范围字符串
    :param range_str: 范围字符串，格式如 "5-20"
    :return: range对象
    """
    if '-' in range_str:
        try:
            start, end = map(int, range_str.split('-'))
            return range(start, end + 1)
        except ValueError:
            pass
    # 如果解析失败，返回默认范围
    return range(1, 11)

def equity_signal(data_df: pd.DataFrame, *args) -> pd.Series:
    """
    参数优化策略信号生成函数
    :param data_df: 包含金融数据的 DataFrame，必须包含 '收盘价' 列
    :param args: 策略参数
    :return: 返回包含信号的 Series（1=做多，0=空仓）
    """
    # 默认返回持有信号
    signals = pd.Series(1.0, index=data_df.index)
    return signals

def calculate_returns(data_df: pd.DataFrame, signals: pd.Series, principal: float = 100000.0, fee_rate: float = 0.001) -> tuple:
    """
    计算策略收益（与手动回测保持一致）
    :param data_df: 包含金融数据的 DataFrame
    :param signals: 交易信号
    :param principal: 本金
    :param fee_rate: 手续费率
    :return: 总收益和夏普比率
    """
    # 使用与手动回测相同的收益计算方式
    from utils.money_management import calculate_trade_details
    trade_details = calculate_trade_details(data_df, signals, principal, fee_rate)
    
    # 总收益（以百分比表示）
    total_return = trade_details['total_return_rate'] / 100.0
    
    # 计算夏普比率（基于每日收益率）
    returns = data_df['收盘价'].pct_change().fillna(0)
    strategy_returns = returns * signals.shift(1).fillna(0)
    
    # 计算夏普比率（年化）
    if strategy_returns.std() > 0:
        sharpe_ratio = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
    else:
        sharpe_ratio = 0
    
    return total_return, sharpe_ratio

def _evaluate_single_combination(args):
    """
    评估单个参数组合的内部函数
    :param args: 包含(data_df, strategy_func, param_combination, principal, fee_rate)的元组
    :return: 评估结果
    """
    data_df, strategy_func, param_combination, principal, fee_rate, params = args
    
    try:
        # 运行策略
        signals = strategy_func(data_df, *param_combination)
        
        # 计算收益（使用与手动回测一致的方式）
        total_return, sharpe_ratio = calculate_returns(data_df, signals, principal, fee_rate)
        
        # 计算交易详情
        trade_details = calculate_trade_details(data_df, signals, principal, fee_rate)
        
        # 记录结果
        result = {
            'params': params,
            'return': total_return,
            'sharpe': sharpe_ratio,
            'trade_details': trade_details
        }
        
        return result
    except Exception as e:
        # 如果某个参数组合出错，记录错误并继续
        print(f"参数组合 {params} 执行出错: {e}")
        result = {
            'params': params,
            'return': -float('inf'),
            'sharpe': -float('inf'),
            'error': str(e)
        }
        return result

def optimize_parameters(data_df: pd.DataFrame, strategy_func, param_ranges: dict, principal: float = 100000.0, fee_rate: float = 0.001, max_workers: int = None, progress_callback=None) -> dict:
    """
    优化策略参数（支持多线程加速）
    :param data_df: 包含金融数据的 DataFrame
    :param strategy_func: 策略函数
    :param param_ranges: 参数范围字典，格式如 {'short_ma': range(5, 21), 'long_ma': range(20, 61)}
                         如果只有一个范围，会自动生成合适的短期和长期均线范围
    :param principal: 本金
    :param fee_rate: 手续费率
    :param max_workers: 最大工作线程数，默认为CPU核心数
    :param progress_callback: 进度更新回调函数
    :return: 包含优化结果的字典
    """
    start_time = time.time()  # 记录开始时间
    
    best_params = None
    best_return = -float('inf')
    best_sharpe = -float('inf')
    results = []
    
    # 检查参数范围
    param_names = list(param_ranges.keys())
    param_values = list(param_ranges.values())
    
    # 如果没有参数范围，直接返回默认结果
    if not param_names:
        return {
            'best_params': {},
            'best_return': 0.0,
            'best_sharpe': 0.0,
            'all_results': []
        }
    
    # 如果只有一个参数范围，生成所有可能的短期和长期均线组合
    if len(param_names) == 1 and param_names[0] == 'ma_range':
        # 获取单一范围
        ma_range = param_values[0]
        # 生成所有可能的短期和长期均线组合（短期 < 长期）
        combinations = []
        ma_list = list(ma_range)
        for i in range(len(ma_list)):
            for j in range(i+1, len(ma_list)):
                combinations.append((ma_list[i], ma_list[j]))
        
        # 更新参数名称
        param_names = ['short_ma', 'long_ma']
    else:
        # 如果已经有明确的短期和长期均线范围，使用笛卡尔积
        # 遍历所有参数组合
        combinations = list(product(*param_values))
    
    total_combinations = len(combinations)
    progress_message = f"开始参数优化，总共需要测试 {total_combinations} 种参数组合"
    print(progress_message)
    if progress_callback:
        progress_callback(progress_message)
    
    # 设置最大工作线程数
    if max_workers is None:
        max_workers = min(4, multiprocessing.cpu_count())  # 限制最大线程数以避免系统过载
    progress_message = f"使用 {max_workers} 个线程进行并行计算"
    print(progress_message)
    if progress_callback:
        progress_callback(progress_message)
    
    # 准备参数列表
    evaluation_args = []
    for param_combination in combinations:
        # 构建参数字典
        if len(param_names) == 2 and param_names == ['short_ma', 'long_ma']:
            # 确保短期均线小于长期均线
            if param_combination[0] >= param_combination[1]:
                continue
            params = {param_names[0]: param_combination[0], param_names[1]: param_combination[1]}
        else:
            params = dict(zip(param_names, param_combination))
        
        evaluation_args.append((data_df, strategy_func, param_combination, principal, fee_rate, params))
    
    # 使用线程池并行计算
    completed = 0
    last_progress = 0
    progress_message = f"进度: {completed}/{len(evaluation_args)} (0.00%) 完成"
    print(progress_message)
    if progress_callback:
        progress_callback(progress_message)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_args = {executor.submit(_evaluate_single_combination, args): args for args in evaluation_args}
        
        # 收集结果
        for future in as_completed(future_to_args):
            result = future.result()
            results.append(result)
            
            # 更新最优参数
            if result.get('return', -float('inf')) > best_return:
                best_return = result['return']
                best_params = result['params']
                # 显示找到更好结果的信息
                progress_message = f"  -> 找到更优参数组合: {best_params}, 收益: {best_return*100:.4f}%"
                print(progress_message)
                if progress_callback:
                    progress_callback(progress_message)
            if result.get('sharpe', -float('inf')) > best_sharpe:
                best_sharpe = result['sharpe']
            
            completed += 1
            # 计算进度百分比
            progress_percent = (completed / len(evaluation_args)) * 100
            
            # 每完成5%或每10个任务显示一次进度
            if completed == len(evaluation_args) or progress_percent >= last_progress + 5 or completed % 10 == 0:
                elapsed_time = time.time() - start_time
                progress_message = f"进度: {completed}/{len(evaluation_args)} ({progress_percent:.2f}%) 完成, 耗时: {elapsed_time:.2f} 秒"
                print(progress_message)
                if progress_callback:
                    progress_callback(progress_message)
                last_progress = (progress_percent // 5) * 5  # 更新上次显示的进度
    
    # 按收益排序结果，增加安全检查
    try:
        results.sort(key=lambda x: x.get('return', -float('inf')), reverse=True)
    except Exception as e:
        progress_message = f"排序结果时出错: {e}"
        print(progress_message)
        if progress_callback:
            progress_callback(progress_message)
        # 如果排序失败，至少确保结果列表不为空
        pass
    
    # 安全地获取前50个结果
    top_results = []
    try:
        top_results = results[:50] if len(results) >= 50 else results
    except Exception as e:
        progress_message = f"获取前50个结果时出错: {e}"
        print(progress_message)
        if progress_callback:
            progress_callback(progress_message)
        top_results = results  # 如果出错，返回所有结果
    
    end_time = time.time()  # 记录结束时间
    elapsed_time = end_time - start_time
    progress_message = f"参数优化完成，耗时: {elapsed_time:.2f} 秒"
    print(progress_message)
    if progress_callback:
        progress_callback(progress_message)
    
    return {
        'best_params': best_params,
        'best_return': best_return,
        'best_sharpe': best_sharpe,
        'all_results': top_results,  # 使用安全获取的结果
        'elapsed_time': elapsed_time  # 添加耗时信息
    }

# 示例参数范围（可根据具体策略调整）
DEFAULT_PARAM_RANGES = {
    'short_ma': range(5, 21),    # 短期均线周期 5-20
    'long_ma': range(20, 61),    # 长期均线周期 20-60
}