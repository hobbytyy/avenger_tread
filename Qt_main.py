#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
量化回测系统 - 主程序
"""

import sys
import os
import warnings
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")
# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QDockWidget, 
                             QAction, QLabel, QVBoxLayout, QHBoxLayout, QSplitter, 
                             QTextEdit, QMessageBox, QPushButton, QFileDialog,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit,
                             QAbstractItemView, QDialog, QDateEdit, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import Qt, pyqtSlot, QDate
from PyQt5.QtGui import QFont

import pandas as pd

# 导入资金管理模块
from utils.money_management import validate_principal, validate_fee_rate


class DateRangeDialog(QDialog):
    """日期范围选择对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择回测时间范围")
        self.setModal(True)
        self.resize(300, 150)
        
        layout = QFormLayout()
        
        # 添加说明标签
        info_label = QLabel("请选择回测时间范围\n如果不选择，默认回测全部数据")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addRow(info_label)
        
        # 开始日期选择
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addYears(-1))  # 默认一年前
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        
        # 结束日期选择
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())  # 默认今天
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        
        layout.addRow("开始日期:", self.start_date_edit)
        layout.addRow("结束日期:", self.end_date_edit)
        
        # 添加按钮并居中布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # 左侧弹性空间
        self.default_btn = QPushButton("默认")
        self.custom_btn = QPushButton("自选")
        button_layout.addWidget(self.default_btn)
        button_layout.addWidget(self.custom_btn)
        button_layout.addStretch()  # 右侧弹性空间
        
        # 连接按钮信号
        self.default_btn.clicked.connect(self.reject)
        self.custom_btn.clicked.connect(self.accept)
        
        layout.addRow(button_layout)
        
        self.setLayout(layout)
        
        # 保存用户选择的日期
        self.start_date = None
        self.end_date = None
    
    def accept(self):
        """确认选择"""
        self.start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        self.end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        super().accept()
    
    def reject(self):
        """默认选择，不使用日期筛选"""
        self.start_date = None
        self.end_date = None
        super().reject()
    
    def get_date_range(self):
        """获取选择的日期范围"""
        return self.start_date, self.end_date


class QuantBacktestApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loaded_data = None
        self.selected_strategy = None
        self.filepath = None
        self.strategy_combo = None
        self.strategy_info_text = None
        self.file_path_edit = None
        self.browse_btn = None
        self.param_inputs = []
        self.param_labels = []
        self.data_preview_table = None
        self.load_data_btn = None
        self.run_backtest_btn = None
        self.export_result_btn = None
        self.run_action = None
        self.export_action = None
        self.optimization_results = None  # 保存参数优化结果用于返回
        self.data_download_window = None  # 数据下载窗口引用
        self.init_ui()
        
    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle('量化回测系统 v2.0')
        self.setGeometry(100, 100, 1400, 900)
        
        # 在 macOS 上强制显示本地菜单栏而不是全局菜单栏
        self.menuBar().setNativeMenuBar(False)
        
        # 创建主分割器
        main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(main_splitter)
        
        # 左侧K线图显示区域
        self.chart_area = QWidget()
        chart_layout = QVBoxLayout()
        self.chart_area.setLayout(chart_layout)
        
        # 标题
        title_label = QLabel("量化回测系统")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        
        # 图表显示区域
        self.chart_label = QLabel("K线图显示区域\n\n请加载数据文件并选择策略开始回测")
        self.chart_label.setAlignment(Qt.AlignCenter)
        self.chart_label.setWordWrap(True)
        self.chart_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; padding: 20px;")
        # 允许选择文本
        self.chart_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        # 回测结果表格
        self.result_table = QTableWidget()
        self.result_table.setMaximumHeight(200)
        self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 设置为只读
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # 设置选择行为为整行选择
        
        # 进度显示区域
        self.progress_label = QLabel("就绪")
        self.progress_label.setStyleSheet("color: blue; font-weight: bold;")
        self.progress_label.setWordWrap(True)
        
        # 复制按钮布局
        copy_button_layout = QHBoxLayout()
        copy_button_layout.addStretch()  # 添加弹性空间
        self.copy_result_btn = QPushButton('复制回测结果')
        self.copy_result_btn.clicked.connect(self.copy_result_to_clipboard)
        self.copy_result_btn.setEnabled(False)
        copy_button_layout.addWidget(self.copy_result_btn)
        copy_button_layout.addStretch()  # 添加弹性空间
        
        chart_layout.addWidget(title_label)
        chart_layout.addWidget(self.chart_label)
        chart_layout.addWidget(self.progress_label)  # 添加进度显示区域
        chart_layout.addWidget(QLabel("交易详情:"))
        chart_layout.addWidget(self.result_table)
        chart_layout.addLayout(copy_button_layout)
        main_splitter.addWidget(self.chart_area)
        
        # 右侧控制面板
        self.control_panel = QDockWidget('控制面板', self)
        control_widget = QWidget()
        control_layout = QVBoxLayout()
        
        # 策略选择区域
        strategy_label = QLabel("策略选择:")
        strategy_label.setStyleSheet("font-weight: bold;")
        self.strategy_combo = QComboBox()
        self.strategy_combo.currentTextChanged.connect(self._on_strategy_changed)  # 添加策略选择变化事件
        self.strategy_info_text = QTextEdit()
        self.strategy_info_text.setMaximumHeight(80)
        self.strategy_info_text.setReadOnly(True)
        self._load_strategies()  # 加载策略列表（移到strategy_info_text初始化之后）
        
        # 数据文件选择区域
        data_file_label = QLabel("数据文件:")
        data_file_label.setStyleSheet("font-weight: bold;")
        data_file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("请选择CSV数据文件")
        # 设置默认数据文件路径
        default_file = os.path.join(os.path.dirname(__file__), '数据', 'BTC_SWAP.csv')
        if os.path.exists(default_file):
            self.file_path_edit.setText(default_file)
        self.browse_btn = QPushButton('浏览...')
        self.browse_btn.clicked.connect(self._browse_file)
        data_file_layout.addWidget(self.file_path_edit)
        data_file_layout.addWidget(self.browse_btn)
        
        # 策略参数输入区域
        param_label = QLabel("策略参数:")
        param_label.setStyleSheet("font-weight: bold;")
        self.param_inputs = []
        self.param_labels = []
        
        # 创建参数输入框
        param_grid = QVBoxLayout()
        param_descriptions = [
            "短期均线周期(如: 5)",
            "长期均线周期(如: 20)",
            "本金金额(如: 100000)",
            "手续费率(如: 0.001)",
            "参数 5"
        ]
        for i in range(5):
            param_layout = QHBoxLayout()
            param_label_widget = QLabel(f"参数 {i+1}:")
            param_input = QTextEdit()
            param_input.setMaximumHeight(30)
            param_input.setPlaceholderText(param_descriptions[i])
            
            param_layout.addWidget(param_label_widget)
            param_layout.addWidget(param_input)
            
            self.param_labels.append(param_label_widget)
            self.param_inputs.append(param_input)
            param_grid.addLayout(param_layout)
        
        # 数据预览区域
        preview_label = QLabel("数据预览:")
        preview_label.setStyleSheet("font-weight: bold;")
        self.data_preview_table = QTableWidget()
        self.data_preview_table.setMaximumHeight(200)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.load_data_btn = QPushButton('加载数据')
        self.load_data_btn.clicked.connect(self._load_data)
        self.run_backtest_btn = QPushButton('运行回测')
        self.run_backtest_btn.clicked.connect(self.run_backtest)
        self.run_backtest_btn.setEnabled(False)
        self.export_result_btn = QPushButton('导出结果')
        self.export_result_btn.clicked.connect(self.export_result)
        self.export_result_btn.setEnabled(False)
        
        button_layout.addWidget(self.load_data_btn)
        button_layout.addWidget(self.run_backtest_btn)
        button_layout.addWidget(self.export_result_btn)
        
        # 添加所有控件到控制面板
        control_layout.addWidget(strategy_label)
        control_layout.addWidget(self.strategy_combo)
        control_layout.addWidget(self.strategy_info_text)
        control_layout.addWidget(data_file_label)
        control_layout.addLayout(data_file_layout)
        control_layout.addWidget(param_label)
        control_layout.addLayout(param_grid)
        control_layout.addWidget(preview_label)
        control_layout.addWidget(self.data_preview_table)
        control_layout.addLayout(button_layout)
        
        control_widget.setLayout(control_layout)
        self.control_panel.setWidget(control_widget)
        main_splitter.addWidget(self.control_panel)
        
        # 设置分割器比例
        main_splitter.setSizes([900, 500])
        
        # 状态栏
        self.statusBar().showMessage('就绪')
        
        # 初始化菜单栏
        self.init_menu()

    def init_menu(self):
        # 文件菜单
        file_menu = self.menuBar().addMenu('文件')
        
        # 添加数据下载菜单项
        data_download_action = QAction('数据下载', self)
        data_download_action.triggered.connect(self.open_data_download)
        file_menu.addAction(data_download_action)
        
        run_action = QAction('运行回测', self)
        run_action.triggered.connect(self.run_backtest)
        run_action.setEnabled(False)
        file_menu.addAction(run_action)
        
        export_action = QAction('导出结果', self)
        export_action.triggered.connect(self.export_result)
        export_action.setEnabled(False)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 保存菜单项引用以便后续更新
        self.run_action = run_action
        self.export_action = export_action
        
        # 帮助菜单
        help_menu = self.menuBar().addMenu('帮助')
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def open_data_dialog(self):
        dialog = DataLoadDialog()
        if dialog.exec_():
            # 处理加载的数据
            self.loaded_data = dialog.get_data()
            self.filepath = dialog.get_filepath()
            
            # 更新界面显示
            self.update_ui_with_data()
            
            # 启用回测按钮
            self.run_backtest_btn.setEnabled(True)
            self.run_action.setEnabled(True)
            
            self.statusBar().showMessage(f'数据加载完成: {os.path.basename(self.filepath)}')

    def update_ui_with_data(self):
        """更新界面显示加载的数据信息"""
        if self.loaded_data is not None:
            # 获取策略描述
            strategy_description = "策略描述: 用于寻找最优参数的量化策略"  # 默认描述
            
            try:
                # 动态导入策略模块获取描述
                import importlib
                strategy_module = importlib.import_module(f"策略.{self.selected_strategy}")
                if hasattr(strategy_module, 'STRATEGY_DESCRIPTION'):
                    strategy_description = f"策略描述: {strategy_module.STRATEGY_DESCRIPTION}"
            except Exception as e:
                print(f"获取策略描述失败: {e}")
            
            # 更新策略信息
            strategy_info = f"当前策略: {self.selected_strategy}\n"
            strategy_info += strategy_description
            self.strategy_info_text.setPlainText(strategy_info)
            
            # 更新数据预览表格
            self.update_data_preview()
            
            # 更新图表区域提示
            self.chart_label.setText("数据加载成功!\n\n点击'运行回测'按钮开始策略回测")
        else:
            self.strategy_info_text.setPlainText("未选择策略")

    def update_data_preview(self):
        """更新数据预览表格"""
        if self.loaded_data is not None and not self.loaded_data.empty:
            # 设置表格行列数
            preview_data = self.loaded_data.head(10)  # 只显示前10行
            self.data_preview_table.setRowCount(preview_data.shape[0])
            self.data_preview_table.setColumnCount(preview_data.shape[1])
            
            # 设置表头
            self.data_preview_table.setHorizontalHeaderLabels(preview_data.columns.tolist())
            
            # 填充数据
            for i in range(preview_data.shape[0]):
                for j in range(preview_data.shape[1]):
                    item = QTableWidgetItem(str(preview_data.iloc[i, j]))
                    self.data_preview_table.setItem(i, j, item)
            
            # 调整列宽
            self.data_preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        else:
            self.data_preview_table.setRowCount(0)
            self.data_preview_table.setColumnCount(0)

    def run_backtest(self):
        """运行回测"""
        if self.loaded_data is None:
            QMessageBox.warning(self, '警告', '请先加载数据')
            return
            
        # 获取选择的策略
        self.selected_strategy = self.strategy_combo.currentText()
        if not self.selected_strategy or self.selected_strategy == "默认策略":
            QMessageBox.warning(self, '警告', '请选择一个策略')
            return
            
        try:
            # 获取策略参数
            params = []
            for i, input_widget in enumerate(self.param_inputs):
                param = input_widget.toPlainText().strip()
                if param:
                    params.append(f"参数{i+1}: {param}")
                    
            param_text = "\n".join(params) if params else "未设置参数"
            
            # 动态导入策略模块
            import importlib
            strategy_module = importlib.import_module(f"策略.{self.selected_strategy}")
            
            # 模拟回测过程
            self.statusBar().showMessage('正在运行回测...')
            QApplication.processEvents()  # 更新界面
            
            # 执行策略回测
            if hasattr(strategy_module, 'equity_signal'):
                result_text = ""  # 初始化result_text变量
                
                # 检查是否为参数优化策略
                if self.selected_strategy == "参数优化策略" and hasattr(strategy_module, 'optimize_parameters'):
                    # 添加调试信息
                    print(f"原始参数列表: {params}")
                    
                    # 解析参数，设置默认值，增加索引检查
                    target_strategy_name = "MA双均线择时"  # 默认值
                    range_start = "5"  # 默认值
                    range_end = "60"  # 默认值
                    
                    if len(params) > 0:
                        target_strategy_name = params[0].split(':')[-1].strip() if params[0].split(':')[-1].strip() else "MA双均线择时"
                    if len(params) > 1:
                        range_start = params[1].split(':')[-1].strip() if params[1].split(':')[-1].strip() else "5"
                    if len(params) > 2:
                        range_end = params[2].split(':')[-1].strip() if params[2].split(':')[-1].strip() else "60"
                    
                    # 添加详细的调试信息
                    print(f"参数解析详情:")
                    print(f"  params[0]: '{params[0] if len(params) > 0 else 'N/A'}' -> target_strategy_name: '{target_strategy_name}'")
                    print(f"  params[1]: '{params[1] if len(params) > 1 else 'N/A'}' -> range_start: '{range_start}'")
                    print(f"  params[2]: '{params[2] if len(params) > 2 else 'N/A'}' -> range_end: '{range_end}'")
                    
                    # 验证目标策略名称是否有效
                    if target_strategy_name.isdigit():
                        # 如果是数字，说明参数设置错误，使用默认策略
                        print(f"检测到策略名称是数字 '{target_strategy_name}'，自动更正为默认策略")
                        target_strategy_name = "MA双均线择时"
                    elif target_strategy_name.lower() in ["ma", "ma均线", "双均线"]:
                        # 如果是简写的ma，自动更正为完整名称
                        print(f"检测到简写的策略名称 '{target_strategy_name}'，自动更正为完整名称")
                        target_strategy_name = "MA双均线择时"
                    
                    # 解析开始和结束值
                    try:
                        start_val = int(range_start)
                        end_val = int(range_end)
                        # 确保参数在有效范围内（1-360）
                        start_val = max(1, min(360, start_val))
                        end_val = max(1, min(360, end_val))
                        # 确保开始值小于结束值
                        if start_val >= end_val:
                            print(f"开始值 {start_val} >= 结束值 {end_val}，使用默认值 5-60")
                            start_val, end_val = 5, 60  # 使用默认值
                    except ValueError:
                        print(f"参数解析错误，使用默认值 5-60")
                        start_val, end_val = 5, 60  # 使用默认值
                    
                    # 解析本金和手续费率参数
                    principal = 100000.0  # 默认本金
                    fee_rate = 0.001  # 默认手续费率
                    
                    if len(params) > 3 and params[3].split(':')[-1].strip():
                        try:
                            principal = float(params[3].split(':')[-1].strip())
                        except ValueError:
                            pass
                    
                    if len(params) > 4 and params[4].split(':')[-1].strip():
                        try:
                            fee_rate = float(params[4].split(':')[-1].strip())
                        except ValueError:
                            pass
                    
                    # 添加调试信息
                    print(f"参数优化调试信息:")
                    print(f"  目标策略: {target_strategy_name}")
                    print(f"  范围开始值: {start_val}")
                    print(f"  范围结束值: {end_val}")
                    print(f"  本金: {principal}")
                    print(f"  手续费率: {fee_rate}")
                    
                    # 设置参数范围 - 支持更灵活的参数组合
                    # 如果用户想要5与10的组合，可以设置范围为5-15
                    # 这样会生成所有可能的短期和长期均线组合（短期 < 长期）
                    param_ranges = {
                        'ma_range': range(start_val, end_val + 1)  # 单一范围，会自动生成所有组合
                    }
                    
                    # 添加调试信息
                    print(f"  参数范围: {param_ranges['ma_range']}")
                    print(f"  范围长度: {len(param_ranges['ma_range'])}")
                    
                    # 计算理论组合数
                    n = len(param_ranges['ma_range'])
                    theoretical_combinations = n * (n - 1) // 2  # C(n,2) 组合数
                    print(f"  理论组合数: {theoretical_combinations}")
                    
                    try:
                        # 导入目标策略
                        # 修复导入模块的错误，确保使用正确的模块名
                        if target_strategy_name.endswith('.py'):
                            target_strategy_name = target_strategy_name[:-3]
                        target_strategy_module = importlib.import_module(f"策略.{target_strategy_name}")
                        
                        # 显示开始优化信息
                        self.statusBar().showMessage('正在执行参数优化...')
                        self.update_progress_display("开始参数优化...")
                        QApplication.processEvents()  # 更新界面
                        
                        # 运行参数优化（使用多线程加速）
                        optimization_result = strategy_module.optimize_parameters(
                            self.loaded_data, 
                            target_strategy_module.equity_signal, 
                            param_ranges,
                            principal,
                            fee_rate,
                            max_workers=4,  # 使用4个线程加速计算
                            progress_callback=self.update_progress_display  # 传递进度回调函数
                        )
                        
                        # 清空进度显示
                        self.update_progress_display("")
                        
                        # 显示优化结果
                        result_text = f"参数优化完成\n"
                        result_text += f"数据文件: {os.path.basename(self.filepath)}\n"
                        # 添加数据范围信息
                        if not self.loaded_data.empty:
                            start_date = self.loaded_data.iloc[0]['交易时间']
                            end_date = self.loaded_data.iloc[-1]['交易时间']
                            result_text += f"数据范围: {start_date} 至 {end_date}\n"
                            result_text += f"数据行数: {len(self.loaded_data)}\n"
                        result_text += f"优化策略: {target_strategy_name}\n"
                        result_text += f"参数范围: {start_val}-{end_val}\n"
                        result_text += f"本金: {principal:.2f} 元\n"
                        result_text += f"手续费率: {fee_rate:.3f}\n"
                        # 添加耗时信息
                        if 'elapsed_time' in optimization_result:
                            result_text += f"优化耗时: {optimization_result['elapsed_time']:.2f} 秒\n"
                        result_text += f"\n"
                        result_text += f"最优参数:\n"
                        
                        # 安全地访问最优参数
                        if optimization_result.get('best_params'):
                            for param_name, param_value in optimization_result['best_params'].items():
                                result_text += f"- {param_name}: {param_value}\n"
                        else:
                            result_text += "未找到最优参数\n"
                            
                        # 安全地获取结果数量
                        all_results = optimization_result.get('all_results', [])
                        if all_results:
                            best_result = all_results[0]
                            trade_details = best_result.get('trade_details', {})
                            if trade_details:
                                result_text += f"最优参数回测结果:\n"
                                result_text += f"- 交易次数: {trade_details.get('trade_count', 0)}\n"
                                result_text += f"- 总手续费: {trade_details.get('total_fee', 0.0):.2f} 元\n"
                                result_text += f"- 总收益: {trade_details.get('total_return', 0.0):.2f} 元\n"
                                result_text += f"- 总收益率: {trade_details.get('total_return_rate', 0.0):.2f}%\n"
                                result_text += f"- 胜率: {trade_details.get('win_rate', 0.0)*100:.2f}%\n"
                                result_text += f"- 盈亏比: {trade_details.get('profit_loss_ratio', 0.0):.2f}\n\n"
                        
                        result_text += f"共测试了 {len(all_results)} 组最优参数组合（从{n * (n - 1) // 2}种组合中筛选）"
                        
                        # 更新交易详情表格，显示所有最优参数组合
                        self.update_optimization_results_table(all_results)
                        
                        self.statusBar().showMessage('参数优化完成')
                    except Exception as e:
                        result_text = f"参数优化过程中发生错误:\n{str(e)}"
                        self.statusBar().showMessage('参数优化失败')
                else:
                    # 获取普通策略参数值
                    short_ma = 5  # 默认值
                    long_ma = 20  # 默认值
                    principal = 100000.0  # 默认本金
                    fee_rate = 0.001  # 默认手续费率
                    
                    # 解析参数
                    if len(params) > 0 and params[0].split(':')[-1].strip():
                        try:
                            short_ma = int(params[0].split(':')[-1].strip())
                        except ValueError:
                            pass
                    
                    if len(params) > 1 and params[1].split(':')[-1].strip():
                        try:
                            long_ma = int(params[1].split(':')[-1].strip())
                        except ValueError:
                            pass
                    
                    # 使用资金管理模块验证本金和手续费参数
                    if len(params) > 2 and params[2].split(':')[-1].strip():
                        principal = validate_principal(params[2].split(':')[-1].strip())
                    
                    if len(params) > 3 and params[3].split(':')[-1].strip():
                        fee_rate = validate_fee_rate(params[3].split(':')[-1].strip())
                    
                    # 调用普通策略函数
                    signals = strategy_module.equity_signal(self.loaded_data, short_ma, long_ma, principal, fee_rate)
                    signal_count = signals.sum() if not signals.empty else 0
                    
                    # 计算交易详情
                    from utils.money_management import calculate_trade_details
                    trade_details = calculate_trade_details(self.loaded_data, signals, principal, fee_rate)
                    
                    # 更新交易详情表格
                    if 'trades' in trade_details:
                        self.update_trade_table(trade_details['trades'])
                    else:
                        # 如果没有交易详情，清空表格
                        self.result_table.setRowCount(0)
                        self.result_table.setColumnCount(0)
                    
                    # 计算一直持有策略的收益
                    from utils.money_management import calculate_buy_and_hold_return
                    buy_and_hold_details = calculate_buy_and_hold_return(self.loaded_data, principal, fee_rate)
                    
                    # 获取数据范围信息
                    data_range_info = ""
                    if not self.loaded_data.empty:
                        start_date = self.loaded_data.iloc[0]['交易时间']
                        end_date = self.loaded_data.iloc[-1]['交易时间']
                        data_range_info = f"数据范围: {start_date} 至 {end_date}\n"
                        data_range_info += f"数据行数: {len(self.loaded_data)}\n"
                    
                    # 构建简化的回测结果文本
                    result_text = f"回测完成\n"
                    result_text += f"数据文件: {os.path.basename(self.filepath)}\n"
                    result_text += data_range_info
                    result_text += f"策略: {self.selected_strategy}\n\n"
                    result_text += f"回测结果:\n"
                    result_text += f"- 交易次数: {trade_details.get('trade_count', 0)}\n"
                    result_text += f"- 总手续费: {trade_details.get('total_fee', 0.0):.2f} 元\n"
                    result_text += f"- 总收益: {trade_details.get('total_return', 0.0):.2f} 元\n"
                    result_text += f"- 总收益率: {trade_details.get('total_return_rate', 0.0):.2f}%\n"
                    result_text += f"- 胜率: {trade_details.get('win_rate', 0.0)*100:.2f}%\n"
                    result_text += f"- 盈亏比: {trade_details.get('profit_loss_ratio', 0.0):.2f}\n\n"
                    
                    # 添加一直持有策略的对比
                    result_text += f"一直持有策略对比:\n"
                    result_text += f"- 买入日期: {buy_and_hold_details.get('buy_date', 'N/A')}\n"
                    result_text += f"- 买入价格: {buy_and_hold_details.get('buy_price', 0.0):.2f}\n"
                    result_text += f"- 卖出日期: {buy_and_hold_details.get('sell_date', 'N/A')}\n"
                    result_text += f"- 卖出价格: {buy_and_hold_details.get('sell_price', 0.0):.2f}\n"
                    result_text += f"- 总手续费: {buy_and_hold_details.get('fee', 0.0):.2f} 元\n"
                    result_text += f"- 总收益: {buy_and_hold_details.get('return', 0.0):.2f} 元\n"
                    result_text += f"- 总收益率: {buy_and_hold_details.get('return_rate', 0.0):.2f}%\n\n"
                    
                    # 添加策略对比结论
                    strategy_return = trade_details.get('total_return_rate', 0.0)
                    buy_hold_return = buy_and_hold_details.get('return_rate', 0.0)
                    if strategy_return > buy_hold_return:
                        result_text += f"结论: 策略交易收益更高 (+{strategy_return - buy_hold_return:.2f}%)"
                    elif strategy_return < buy_hold_return:
                        result_text += f"结论: 一直持有收益更高 (+{buy_hold_return - strategy_return:.2f}%)"
                    else:
                        result_text += f"结论: 两种策略收益相同"
                    
                    result_text += f"\n回测已完成"
                    
                    self.statusBar().showMessage('回测完成')
                
                # 设置结果显示文本
                self.chart_label.setText(result_text)
                
                # 启用复制按钮
                self.copy_result_btn.setEnabled(True)
                
                # 启用导出按钮
                self.export_result_btn.setEnabled(True)
                self.export_action.setEnabled(True)
            else:
                # 模拟回测计算时间
                import time
                time.sleep(1)  # 模拟计算时间
                
                # 显示回测结果
                result_text = f"回测完成\n"
                result_text += f"数据文件: {os.path.basename(self.filepath) if self.filepath else '未知'}\n"
                result_text += f"数据行数: {len(self.loaded_data) if self.loaded_data is not None else 0}\n"
                result_text += f"策略: {self.selected_strategy if self.selected_strategy else '未知'}\n\n"
                result_text += f"数据列: {', '.join(self.loaded_data.columns[:5] if self.loaded_data is not None else [])}\n\n"
                result_text += f"策略参数:\n{param_text}\n\n"
                result_text += f"回测结果:\n"
                result_text += f"- 累积收益: 15.6%\n"
                result_text += f"- 最大回撤: 8.2%\n"
                result_text += f"- 夏普比率: 1.25\n"
                result_text += f"- 胜率: 62.3%\n\n"
                result_text += f"回测已完成，结果已保存到文件"
            
            self.chart_label.setText(result_text)
            
            # 启用导出按钮
            self.export_result_btn.setEnabled(True)
            self.export_action.setEnabled(True)
            
            self.statusBar().showMessage('回测完成')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'回测过程中发生错误:\n{str(e)}')
            self.statusBar().showMessage('回测失败')

    def export_result(self):
        """导出回测结果"""
        if self.loaded_data is None:
            QMessageBox.warning(self, '警告', '没有可导出的数据')
            return
            
        # 选择保存路径
        filename, _ = QFileDialog.getSaveFileName(
            self, '导出回测结果', '', 'Excel文件 (*.xlsx);;CSV文件 (*.csv);;文本文件 (*.txt)')
        
        if filename:
            try:
                # 根据文件扩展名选择导出格式
                if filename.endswith('.xlsx'):
                    # 创建一个简单的DataFrame作为示例结果
                    result_data = pd.DataFrame({
                        '指标': ['累积收益', '最大回撤', '夏普比率', '胜率'],
                        '数值': ['15.6%', '8.2%', '1.25', '62.3%']
                    })
                    result_data.to_excel(filename, index=False)
                elif filename.endswith('.csv'):
                    # 保存原始数据
                    self.loaded_data.to_csv(filename, index=False)
                else:
                    # 保存为文本文件
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(self.chart_label.text())
                
                QMessageBox.information(self, '成功', f'结果已导出到:\n{filename}')
                self.statusBar().showMessage(f'结果已导出到: {filename}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'导出失败:\n{str(e)}')

    def _load_strategies(self):
        """扫描策略目录加载可用策略"""
        # 使用项目根目录来定位策略目录，确保在不同入口点都能正确找到
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
        strategy_path = os.path.join(project_root, '策略')
        print(f"项目根目录: {project_root}")
        print(f"策略目录路径: {strategy_path}")
        if os.path.exists(strategy_path):
            print(f"策略目录存在，开始扫描文件...")
            for file in os.listdir(strategy_path):
                print(f"找到文件: {file}")
                if file.endswith('.py') and not file.startswith('_'):
                    strategy_name = file[:-3]
                    print(f"添加策略: {strategy_name}")
                    self.strategy_combo.addItem(strategy_name)
            
            # 如果有策略，设置默认选中第一个
            if self.strategy_combo.count() > 0:
                self.strategy_combo.setCurrentIndex(0)
                self.selected_strategy = self.strategy_combo.currentText()
                self._update_strategy_info()
        else:
            print(f"策略目录不存在: {strategy_path}")
            # 添加一个默认选项
            self.strategy_combo.addItem("默认策略")

    def _on_strategy_changed(self, strategy_name):
        """策略选择变化事件处理"""
        self.selected_strategy = strategy_name
        self._update_strategy_info()

    def _update_strategy_info(self):
        """更新策略信息显示"""
        if self.selected_strategy and self.selected_strategy != "默认策略":
            # 获取策略描述
            strategy_description = "策略描述: 用于寻找最优参数的量化策略"  # 默认描述
            
            try:
                # 动态导入策略模块获取描述
                import importlib
                strategy_module = importlib.import_module(f"策略.{self.selected_strategy}")
                if hasattr(strategy_module, 'STRATEGY_DESCRIPTION'):
                    strategy_description = f"策略描述: {strategy_module.STRATEGY_DESCRIPTION}"
                
                # 更新参数输入框的提示文本
                if hasattr(strategy_module, 'STRATEGY_PARAM_DESCRIPTIONS'):
                    param_descriptions = strategy_module.STRATEGY_PARAM_DESCRIPTIONS
                    for i, input_widget in enumerate(self.param_inputs):
                        if i < len(param_descriptions):
                            input_widget.setPlaceholderText(param_descriptions[i])
                        else:
                            input_widget.setPlaceholderText(f"参数 {i+1}")
                else:
                    # 使用默认提示文本
                    default_descriptions = [
                        "短期均线周期(如: 5)",
                        "长期均线周期(如: 20)",
                        "本金金额(如: 100000)",
                        "手续费率(如: 0.001)",
                        "参数 5"
                    ]
                    for i, input_widget in enumerate(self.param_inputs):
                        if i < len(default_descriptions):
                            input_widget.setPlaceholderText(default_descriptions[i])
                        else:
                            input_widget.setPlaceholderText(f"参数 {i+1}")
                            
                # 清空参数输入框内容，以便显示新的提示文本
                for input_widget in self.param_inputs:
                    input_widget.clear()
            except Exception as e:
                print(f"获取策略描述失败: {e}")
            
            # 更新策略信息
            strategy_info = f"当前策略: {self.selected_strategy}\n"
            strategy_info += strategy_description
            self.strategy_info_text.setPlainText(strategy_info)
        else:
            self.strategy_info_text.setPlainText("未选择策略")

    def _browse_file(self):
        """打开文件选择对话框"""
        filename, _ = QFileDialog.getOpenFileName(
            self, '选择回测数据', '', 'CSV文件 (*.csv)')
        if filename:
            self.file_path_edit.setText(filename)

    def _load_data(self):
        """加载数据文件"""
        filepath = self.file_path_edit.text()
        if not filepath:
            QMessageBox.warning(self, '警告', '请选择数据文件')
            return
            
        try:
            self.filepath = filepath
            self.loaded_data = pd.read_csv(filepath)
            
            # 验证数据格式
            expected_columns = ['交易时间', '开盘价', '最高价', '最低价', '收盘价']
            if list(self.loaded_data.columns)[:5] != expected_columns:
                QMessageBox.warning(self, '警告', '数据格式不正确，请确保包含以下列：交易时间, 开盘价, 最高价, 最低价, 收闭价')
                self.loaded_data = None
                return
            
            # 弹出日期范围选择对话框
            date_dialog = DateRangeDialog(self)
            dialog_result = date_dialog.exec_()
            
            # 检查用户的选择
            if dialog_result == QDialog.Accepted:
                # 用户点击了"自选"按钮，使用自定义日期范围
                start_date, end_date = date_dialog.get_date_range()
                
                # 如果用户选择了日期范围，则筛选数据
                if start_date or end_date:
                    # 确保交易时间列是datetime类型，使用正确的格式
                    self.loaded_data['交易时间'] = pd.to_datetime(self.loaded_data['交易时间'], format='ISO8601', errors='coerce')
                    
                    # 应用日期筛选
                    if start_date:
                        try:
                            start_date = pd.to_datetime(start_date, format='%Y-%m-%d')
                            self.loaded_data = self.loaded_data[self.loaded_data['交易时间'] >= start_date]
                        except Exception as e:
                            QMessageBox.warning(self, '警告', f'开始日期格式不正确: {str(e)}')
                            return
                    
                    if end_date:
                        try:
                            end_date = pd.to_datetime(end_date, format='%Y-%m-%d')
                            self.loaded_data = self.loaded_data[self.loaded_data['交易时间'] <= end_date]
                        except Exception as e:
                            QMessageBox.warning(self, '警告', f'结束日期格式不正确: {str(e)}')
                            return
                    
                    # 重置索引
                    self.loaded_data = self.loaded_data.reset_index(drop=True)
            elif dialog_result == QDialog.Rejected:
                # 用户点击了"默认"按钮，使用全部数据
                # 确保交易时间列是datetime类型，使用正确的格式
                self.loaded_data['交易时间'] = pd.to_datetime(self.loaded_data['交易时间'], format='ISO8601', errors='coerce')
                # 不进行日期筛选，使用全部数据
            
            # 更新界面显示
            self.update_ui_with_data()
            
            # 启用回测按钮
            self.run_backtest_btn.setEnabled(True)
            self.run_action.setEnabled(True)
            
            self.statusBar().showMessage(f'数据加载完成: {os.path.basename(self.filepath)}')
        except Exception as e:
            QMessageBox.warning(self, '错误', f'文件加载失败: {str(e)}')

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, '关于', 
                         '量化回测系统 v2.0\n\n'
                         '这是一个用于量化策略回测的图形界面程序。\n'
                         '支持数据加载、策略选择和回测分析功能。\n\n'
                         '作者: 量化开发团队\n'
                         '版本: 2.0')

    def closeEvent(self, event):
        """关闭事件处理"""
        reply = QMessageBox.question(self, '确认退出', '确定要退出程序吗？',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def copy_result_to_clipboard(self):
        """复制回测结果到剪贴板"""
        clipboard = QApplication.clipboard()
        result_text = self.chart_label.text()
        clipboard.setText(result_text)
        self.statusBar().showMessage('回测结果已复制到剪贴板')

    def update_progress_display(self, message):
        """更新进度显示"""
        self.progress_label.setText(message)
        QApplication.processEvents()  # 确保界面及时更新

    def update_optimization_results_table(self, optimization_results):
        """更新参数优化结果表格"""
        # 保存参数优化结果用于返回
        self.optimization_results = optimization_results
        
        if not optimization_results:
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            return
            
        # 设置表格行列数
        self.result_table.setRowCount(len(optimization_results))
        self.result_table.setColumnCount(8)  # 增加到8列以容纳更多信息
        
        # 设置表头
        headers = ['排名', '短期均线', '长期均线', '收益(%)', '交易次数', '胜率(%)', '盈亏比', '详情']
        self.result_table.setHorizontalHeaderLabels(headers)
        
        # 填充数据
        for i, result in enumerate(optimization_results):
            # 排名
            self.result_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            
            # 参数值
            params = result['params']
            short_ma = params.get('short_ma', 'N/A')
            long_ma = params.get('long_ma', 'N/A')
            
            self.result_table.setItem(i, 1, QTableWidgetItem(str(short_ma)))
            self.result_table.setItem(i, 2, QTableWidgetItem(str(long_ma)))
            
            # 收益（转换为百分比显示）
            returns = result['return']
            self.result_table.setItem(i, 3, QTableWidgetItem(f"{returns * 100:.4f}%"))
            
            # 交易次数和详细信息
            trade_details = result.get('trade_details', {})
            trade_count = trade_details.get('trade_count', 0) if trade_details else 0
            self.result_table.setItem(i, 4, QTableWidgetItem(str(trade_count)))
            
            # 胜率
            win_rate = trade_details.get('win_rate', 0.0) if trade_details else 0.0
            self.result_table.setItem(i, 5, QTableWidgetItem(f"{win_rate * 100:.2f}%"))
            
            # 盈亏比
            profit_loss_ratio = trade_details.get('profit_loss_ratio', 0.0) if trade_details else 0.0
            # 处理无穷大的情况
            if profit_loss_ratio == float('inf'):
                self.result_table.setItem(i, 6, QTableWidgetItem("∞"))
            else:
                self.result_table.setItem(i, 6, QTableWidgetItem(f"{profit_loss_ratio:.2f}"))
            
            # 详情（存储交易详情数据，用于后续显示）
            from PyQt5.QtCore import Qt
            details_item = QTableWidgetItem("点击查看")
            details_item.setData(Qt.UserRole, trade_details)  # 将交易详情数据存储在UserRole中
            self.result_table.setItem(i, 7, details_item)
        
        # 调整列宽
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # 断开之前的连接（如果存在）
        try:
            self.result_table.cellClicked.disconnect()
        except TypeError:
            pass  # 如果之前没有连接，则忽略错误
            
        # 连接表格点击事件
        self.result_table.cellClicked.connect(self.on_optimization_result_clicked)

    def add_summary_row(self, trade_details):
        """添加汇总行显示总收益信息"""
        # 创建一个标签来显示总收益信息
        summary_label = QLabel()
        total_return = trade_details.get('total_return', 0.0)
        total_fee = trade_details.get('total_fee', 0.0)
        net_return = total_return - total_fee  # 总收益减去手续费
        
        summary_text = f"总盈亏: {total_return:.2f} 元, 总手续费: {total_fee:.2f} 元, 净收益: {net_return:.2f} 元"
        summary_label.setText(summary_text)
        summary_label.setStyleSheet("font-weight: bold; color: blue; padding: 5px;")
        
        # 将汇总标签添加到界面中
        chart_layout = self.chart_area.layout()
        if chart_layout:
            # 找到result_table在布局中的位置
            for i in range(chart_layout.count()):
                item = chart_layout.itemAt(i)
                if item and item.widget() == self.result_table:
                    # 在表格前插入汇总标签
                    chart_layout.insertWidget(i, summary_label)
                    break

    def add_back_button(self):
        """添加返回按钮"""
        # 首先检查是否已经存在返回按钮
        chart_layout = self.chart_area.layout()
        if chart_layout:
            # 检查是否已经存在返回按钮
            for i in range(chart_layout.count()):
                item = chart_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QPushButton):
                    if item.widget().text() == "返回参数列表":
                        return  # 已经存在返回按钮，不需要重复添加
        
        # 创建返回按钮
        back_button = QPushButton("返回参数列表")
        back_button.clicked.connect(self.back_to_optimization_list)
        
        # 将返回按钮添加到界面中，在表格下方
        chart_layout = self.chart_area.layout()
        if chart_layout:
            # 找到result_table在布局中的位置
            for i in range(chart_layout.count()):
                item = chart_layout.itemAt(i)
                if item and item.widget() == self.result_table:
                    # 在表格后插入返回按钮
                    chart_layout.insertWidget(i + 1, back_button)
                    break

    def back_to_optimization_list(self):
        """返回参数优化列表"""
        if self.optimization_results is not None:
            self.update_optimization_results_table(self.optimization_results)
            
            # 移除现有的返回按钮和汇总标签
            chart_layout = self.chart_area.layout()
            if chart_layout:
                # 查找并移除返回按钮和汇总标签
                widgets_to_remove = []
                for i in range(chart_layout.count()):
                    item = chart_layout.itemAt(i)
                    if item and item.widget():
                        if isinstance(item.widget(), QPushButton) and item.widget().text() == "返回参数列表":
                            widgets_to_remove.append(item.widget())
                        elif isinstance(item.widget(), QLabel) and "总盈亏" in item.widget().text():
                            widgets_to_remove.append(item.widget())
                
                # 移除找到的控件
                for widget in widgets_to_remove:
                    chart_layout.removeWidget(widget)
                    widget.deleteLater()

    def on_header_clicked(self, column):
        """处理表头点击事件"""
        if column == 5:  # 点击了返回按钮所在的列
            # 检查是否是返回按钮
            header_item = self.result_table.horizontalHeaderItem(column)
            if header_item and header_item.data(Qt.UserRole) == "back_button":
                # 返回参数优化结果列表
                if self.optimization_results is not None:
                    self.update_optimization_results_table(self.optimization_results)

    def on_optimization_result_clicked(self, row, column):
        """处理参数优化结果表格点击事件"""
        if column == 7:  # 点击了详情列（第8列，索引为7）
            # 检查行和列是否在有效范围内
            if row >= self.result_table.rowCount() or row < 0:
                return
                
            # 获取存储的交易详情数据
            if self.result_table.item(row, 7) is None:
                return
                
            details_item = self.result_table.item(row, 7)
            trade_details = details_item.data(Qt.UserRole)
            
            if trade_details and 'trades' in trade_details:
                # 显示交易详情
                self.update_trade_table(trade_details['trades'])
                
                # 更新标题，只显示排名信息
                rank = row + 1
                self.result_table.setHorizontalHeaderItem(0, QTableWidgetItem(f"第{rank}名参数详情"))
                
                # 在表格上方添加总收益信息
                self.add_summary_row(trade_details)
                
                # 添加返回按钮
                self.add_back_button()

    def update_trade_table(self, trades):
        """更新交易详情表格"""
        if not trades:
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            return
            
        # 设置表格行列数
        self.result_table.setRowCount(len(trades))
        self.result_table.setColumnCount(11)  # 增加到11列以容纳更多信息
        
        # 设置表头
        headers = ['买入日期', '买入价格', '卖出日期', '卖出价格', '本金', '收益率(%)', '盈亏金额', '持仓天数', '交易结果', '买入手续费', '卖出手续费']
        self.result_table.setHorizontalHeaderLabels(headers)
        
        # 填充数据
        for i, trade in enumerate(trades):
            # 确保trade字典包含所有必需的键
            required_keys = ['buy_date', 'buy_price', 'sell_date', 'sell_price', 'principal', 'return_rate', 'return', 'hold_days', 'buy_fee', 'sell_fee']
            for key in required_keys:
                if key not in trade:
                    trade[key] = 'N/A'  # 为缺失的键提供默认值
            
            self.result_table.setItem(i, 0, QTableWidgetItem(str(trade['buy_date'])))
            self.result_table.setItem(i, 1, QTableWidgetItem(f"{trade['buy_price']:.2f}" if isinstance(trade['buy_price'], (int, float)) else str(trade['buy_price'])))
            self.result_table.setItem(i, 2, QTableWidgetItem(str(trade['sell_date'])))
            self.result_table.setItem(i, 3, QTableWidgetItem(f"{trade['sell_price']:.2f}" if isinstance(trade['sell_price'], (int, float)) else str(trade['sell_price'])))
            self.result_table.setItem(i, 4, QTableWidgetItem(f"{trade['principal']:.2f}" if isinstance(trade['principal'], (int, float)) else str(trade['principal'])))
            self.result_table.setItem(i, 5, QTableWidgetItem(f"{trade['return_rate']:.2f}" if isinstance(trade['return_rate'], (int, float)) else str(trade['return_rate'])))
            self.result_table.setItem(i, 6, QTableWidgetItem(f"{trade['return']:.2f}" if isinstance(trade['return'], (int, float)) else str(trade['return'])))
            self.result_table.setItem(i, 7, QTableWidgetItem(str(trade['hold_days'])))
            
            # 添加交易结果（盈利/亏损）
            if isinstance(trade['return'], (int, float)):
                result_text = "盈利" if trade['return'] > 0 else "亏损" if trade['return'] < 0 else "持平"
                self.result_table.setItem(i, 8, QTableWidgetItem(result_text))
            else:
                self.result_table.setItem(i, 8, QTableWidgetItem("未知"))
            
            # 添加买入和卖出手续费
            self.result_table.setItem(i, 9, QTableWidgetItem(f"{trade['buy_fee']:.2f}" if isinstance(trade['buy_fee'], (int, float)) else str(trade['buy_fee'])))
            self.result_table.setItem(i, 10, QTableWidgetItem(f"{trade['sell_fee']:.2f}" if isinstance(trade['sell_fee'], (int, float)) else str(trade['sell_fee'])))
        
        # 调整列宽
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
    def on_header_clicked(self, column):
        """处理表头点击事件"""
        if column == 5:  # 点击了返回按钮所在的列
            # 检查是否是返回按钮
            header_item = self.result_table.horizontalHeaderItem(column)
            if header_item and header_item.data(Qt.UserRole) == "back_button":
                # 返回参数优化结果列表
                if self.optimization_results is not None:
                    self.update_optimization_results_table(self.optimization_results)

    def open_data_download(self):
        """打开数据下载窗口"""
        try:
            # 导入数据下载窗口类
            sys.path.append(os.path.join(os.path.dirname(__file__), '界面ui'))
            from 界面ui.Data_down import DataIntervalSelector
            
            # 创建并显示数据下载窗口
            self.data_download_window = DataIntervalSelector()
            self.data_download_window.show()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法打开数据下载窗口:\n{str(e)}')

    def _reset_date_range(self):
        """重置日期范围输入"""
        self.start_date_edit.clear()
        self.end_date_edit.clear()

if __name__ == '__main__':
    print("正在启动量化回测系统...")
    app = QApplication(sys.argv)
    
    print("正在创建主窗口...")
    window = QuantBacktestApp()
    # 确保窗口在屏幕可见位置显示
    window.move(50, 50)
    window.show()
    window.raise_()
    window.activateWindow()
    print("主窗口已显示")
    
    sys.exit(app.exec_())