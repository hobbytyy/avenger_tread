#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QCheckBox, 
                             QGroupBox, QMessageBox, QTextEdit, QLineEdit, 
                             QProgressBar, QRadioButton, QButtonGroup, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# 定义常见的现货和合约交易对（移除BUSD交易对）
COMMON_SPOT_SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
    "ADA/USDT", "DOGE/USDT", "DOT/USDT", "AVAX/USDT", "LINK/USDT",
    "MATIC/USDT", "UNI/USDT", "LTC/USDT", "BCH/USDT", "FIL/USDT",
    "TRX/USDT", "ETC/USDT", "XLM/USDT", "VET/USDT", "EOS/USDT",
    "ADA/USDC", "DOGE/USDC", "DOT/USDC", "AVAX/USDC", "LINK/USDC"  # 添加一些USDC交易对作为替代
]

COMMON_FUTURES_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "DOTUSDT", "AVAXUSDT", "LINKUSDT",
    "MATICUSDT", "UNIUSDT", "LTCUSDT", "BCHUSDT", "FILUSDT",
    "TRXUSDT", "ETCUSDT", "XLMUSDT", "VETUSDT", "EOSUSDT",
    "ADAUSDC", "DOGEUSDC", "DOTUSDC", "AVAXUSDC", "LINKUSDC"  # 添加一些USDC交易对作为替代
]

# 获取项目根目录
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

class DownloadWorker(QThread):
    """下载工作线程"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, symbol, intervals, start_date, end_date, is_futures=False):
        super().__init__()
        self.symbol = symbol
        self.intervals = intervals
        self.start_date = start_date
        self.end_date = end_date
        self.is_futures = is_futures  # 是否为合约数据
        self._is_running = True
        
    def run(self):
        try:
            # 在线程中导入，避免阻塞UI
            # 修复导入路径问题
            import importlib.util
            import sys
            
            # 获取当前文件的绝对路径
            current_file = os.path.abspath(__file__)
            # 获取项目根目录
            project_root = os.path.dirname(os.path.dirname(current_file))
            # 构建数据模块路径
            data_module_path = os.path.join(project_root, '数据', 'bian_data.py')
            
            # 检查文件是否存在
            if not os.path.exists(data_module_path):
                raise FileNotFoundError(f"数据模块文件不存在: {data_module_path}")
            
            # 动态导入模块
            spec = importlib.util.spec_from_file_location("bian_data", data_module_path)
            bian_data_module = importlib.util.module_from_spec(spec)
            sys.modules["bian_data"] = bian_data_module
            spec.loader.exec_module(bian_data_module)
            
            for interval in self.intervals:
                if not self._is_running:
                    break
                self.progress.emit(f"开始下载 {self.symbol} 的 {interval} 数据...")
                # 添加异常处理
                try:
                    bian_data_module.download_full_klines(
                        symbol=self.symbol,
                        interval=interval,
                        start=self.start_date,
                        end=self.end_date,
                        is_futures=self.is_futures  # 传递合约标记
                    )
                    self.progress.emit(f"{interval} 数据下载完成")
                except Exception as e:
                    self.progress.emit(f"{interval} 数据下载失败: {str(e)}")
                    raise e
            
            if self._is_running:
                self.finished.emit(True, "所有数据下载完成")
            else:
                self.finished.emit(False, "下载已取消")
        except Exception as e:
            self.finished.emit(False, f"下载失败: {str(e)}")
            
    def stop(self):
        self._is_running = False


class DataIntervalSelector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.download_thread = None
        self.init_ui()
        
    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle('币安数据下载工具')
        self.setGeometry(100, 100, 500, 650)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel('币安数据下载工具')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # 数据类型选择
        type_group = QGroupBox("数据类型选择")
        type_layout = QHBoxLayout()
        self.spot_radio = QRadioButton("现货数据")
        self.futures_radio = QRadioButton("合约数据")
        self.spot_radio.setChecked(True)  # 默认选择现货数据
        
        # 创建按钮组管理单选按钮
        self.type_group = QButtonGroup()
        self.type_group.addButton(self.spot_radio)
        self.type_group.addButton(self.futures_radio)
        
        type_layout.addWidget(self.spot_radio)
        type_layout.addWidget(self.futures_radio)
        type_layout.addStretch()
        type_group.setLayout(type_layout)
        main_layout.addWidget(type_group)
        
        # 交易对选择
        symbol_layout = QHBoxLayout()
        symbol_label = QLabel('交易对:')
        
        # 添加交易对下拉选择框
        self.symbol_combo = QComboBox()
        self.symbol_combo.setEditable(True)  # 允许用户手动输入
        self.symbol_combo.setInsertPolicy(QComboBox.NoInsert)  # 不自动添加新项
        self.populate_symbol_combo()  # 填充初始交易对列表
        
        # 设置下拉框的尺寸策略，确保能完整显示交易对
        self.symbol_combo.setMinimumWidth(500)
        self.symbol_combo.setSizeAdjustPolicy(QComboBox.AdjustToContentsOnFirstShow)
        
        # 交易对输入框（保持兼容性）
        self.symbol_input = self.symbol_combo  # 使用组合框作为输入控件
        
        symbol_layout.addWidget(symbol_label)
        symbol_layout.addWidget(self.symbol_combo)
        main_layout.addLayout(symbol_layout)
        
        # 添加数据类型切换时的提示更新
        self.spot_radio.toggled.connect(self.update_symbol_placeholder)
        self.futures_radio.toggled.connect(self.update_symbol_placeholder)
        
        # 时间范围输入
        date_layout = QHBoxLayout()
        start_label = QLabel('开始日期:')
        self.start_input = QLineEdit()
        self.start_input.setText("2023-01-01")
        self.start_input.setPlaceholderText("YYYY-MM-DD")
        
        end_label = QLabel('结束日期:')
        self.end_input = QLineEdit()
        self.end_input.setText("2023-12-31")
        self.end_input.setPlaceholderText("YYYY-MM-DD")
        
        date_layout.addWidget(start_label)
        date_layout.addWidget(self.start_input)
        date_layout.addWidget(end_label)
        date_layout.addWidget(self.end_input)
        main_layout.addLayout(date_layout)
        
        # 时间周期选择
        interval_group = QGroupBox("可下载的时间周期")
        interval_layout = QVBoxLayout()
        
        # 分钟线
        minute_group = QGroupBox("分钟线")
        minute_layout = QHBoxLayout()
        self.minute_checks = {}
        minute_intervals = ["1m", "3m", "5m", "15m", "30m"]
        for interval in minute_intervals:
            checkbox = QCheckBox(interval)
            self.minute_checks[interval] = checkbox
            minute_layout.addWidget(checkbox)
        minute_group.setLayout(minute_layout)
        
        # 小时线
        hour_group = QGroupBox("小时线")
        hour_layout = QHBoxLayout()
        self.hour_checks = {}
        hour_intervals = ["1h", "2h", "4h", "6h", "8h", "12h"]
        for interval in hour_intervals:
            checkbox = QCheckBox(interval)
            self.hour_checks[interval] = checkbox
            hour_layout.addWidget(checkbox)
        hour_group.setLayout(hour_layout)
        
        # 日线、周线、月线
        other_layout = QHBoxLayout()
        self.day_check = QCheckBox("日线 (1d)")
        self.week_check = QCheckBox("周线 (1w)")
        self.month_check = QCheckBox("月线 (1M)")
        other_layout.addWidget(self.day_check)
        other_layout.addWidget(self.week_check)
        other_layout.addWidget(self.month_check)
        
        interval_layout.addWidget(minute_group)
        interval_layout.addWidget(hour_group)
        interval_layout.addLayout(other_layout)
        interval_group.setLayout(interval_layout)
        main_layout.addWidget(interval_group)
        
        # 全选/取消全选按钮
        select_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all)
        self.deselect_all_btn = QPushButton("取消全选")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        select_layout.addWidget(self.select_all_btn)
        select_layout.addWidget(self.deselect_all_btn)
        select_layout.addStretch()
        main_layout.addLayout(select_layout)
        
        # 下载按钮
        self.download_btn = QPushButton("开始下载")
        self.download_btn.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        self.download_btn.clicked.connect(self.start_download)
        main_layout.addWidget(self.download_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 日志显示区域
        log_label = QLabel('下载日志:')
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        main_layout.addWidget(log_label)
        main_layout.addWidget(self.log_text)
        
        # 状态栏
        self.statusBar().showMessage('就绪')
        
    def populate_symbol_combo(self):
        """填充交易对下拉列表"""
        # 清空现有项
        self.symbol_combo.clear()
        
        # 根据当前选择的数据类型填充交易对
        if self.futures_radio.isChecked():
            self.symbol_combo.addItems(COMMON_FUTURES_SYMBOLS)
            self.symbol_combo.setCurrentText("BTCUSDT")  # 默认选择
        else:
            self.symbol_combo.addItems(COMMON_SPOT_SYMBOLS)
            self.symbol_combo.setCurrentText("BTC/USDT")  # 默认选择
    
    def update_symbol_placeholder(self):
        """根据数据类型更新交易对输入框的占位符提示和默认值"""
        # 重新填充交易对列表
        self.populate_symbol_combo()
        
        if self.futures_radio.isChecked():
            self.symbol_combo.setPlaceholderText("合约示例: BTCUSDT, ETHUSDT (注意：合约交易对不使用斜杠)")
        else:
            self.symbol_combo.setPlaceholderText("现货示例: BTC/USDT, ETH/USDT (注意：现货交易对使用斜杠分隔)")
        
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        if hasattr(self, 'download_thread') and self.download_thread and self.download_thread.isRunning():
            # 停止下载线程
            self.download_thread.stop()
            self.download_thread.quit()
            self.download_thread.wait()
        # 清除线程引用
        self.download_thread = None
        event.accept()
        
    def select_all(self):
        """全选所有复选框"""
        for checkbox in self.minute_checks.values():
            checkbox.setChecked(True)
        for checkbox in self.hour_checks.values():
            checkbox.setChecked(True)
        self.day_check.setChecked(True)
        self.week_check.setChecked(True)
        self.month_check.setChecked(True)
        self.statusBar().showMessage('已全选所有周期')
        
    def deselect_all(self):
        """取消全选所有复选框"""
        for checkbox in self.minute_checks.values():
            checkbox.setChecked(False)
        for checkbox in self.hour_checks.values():
            checkbox.setChecked(False)
        self.day_check.setChecked(False)
        self.week_check.setChecked(False)
        self.month_check.setChecked(False)
        self.statusBar().showMessage('已取消全选')
        
    def get_selected_intervals(self):
        """获取选中的时间周期"""
        selected = []
        
        # 分钟线
        for interval, checkbox in self.minute_checks.items():
            if checkbox.isChecked():
                selected.append(interval)
                
        # 小时线
        for interval, checkbox in self.hour_checks.items():
            if checkbox.isChecked():
                selected.append(interval)
                
        # 日线、周线、月线
        if self.day_check.isChecked():
            selected.append("1d")
        if self.week_check.isChecked():
            selected.append("1w")
        if self.month_check.isChecked():
            selected.append("1M")
            
        return selected
        
    def start_download(self):
        """开始下载数据"""
        # 获取用户输入
        symbol = self.symbol_combo.currentText().strip()  # 从组合框获取交易对
        start_date = self.start_input.text().strip()
        end_date = self.end_input.text().strip()
        
        # 获取数据类型选择
        is_futures = self.futures_radio.isChecked()  # True表示合约数据，False表示现货数据
        
        if not symbol:
            QMessageBox.warning(self, '警告', '请输入交易对')
            return
            
        if not start_date or not end_date:
            QMessageBox.warning(self, '警告', '请输入完整的日期范围')
            return
            
        # 获取选中的时间周期
        selected_intervals = self.get_selected_intervals()
        if not selected_intervals:
            QMessageBox.warning(self, '警告', '请至少选择一个时间周期')
            return
            
        # 禁用下载按钮，显示进度条
        self.download_btn.setEnabled(False)
        self.download_btn.setText("下载中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(selected_intervals))
        self.progress_bar.setValue(0)
        
        # 清空日志
        data_type = "合约" if is_futures else "现货"
        self.log_text.clear()
        self.log_text.append(f"开始下载 {symbol} {data_type}数据...")
        self.log_text.append(f"时间范围: {start_date} 到 {end_date}")
        self.log_text.append(f"选中的时间周期: {', '.join(selected_intervals)}")
        self.log_text.append("-" * 50)
        
        # 启动下载线程
        self.download_thread = DownloadWorker(symbol, selected_intervals, start_date, end_date, is_futures)
        self.download_thread.progress.connect(self.update_log)
        self.download_thread.finished.connect(self.download_finished)
        # 移除自动删除连接，改为在download_finished中手动处理
        # self.download_thread.finished.connect(self.download_thread.deleteLater)  
        self.download_thread.start()
        
    def update_log(self, message):
        """更新日志显示"""
        self.log_text.append(message)
        # 自动滚动到最新日志
        self.log_text.moveCursor(self.log_text.textCursor().End)
        
        # 更新进度条
        current_value = self.progress_bar.value()
        self.progress_bar.setValue(current_value + 1)
        
    def download_finished(self, success, message):
        """下载完成回调"""
        # 启用下载按钮，隐藏进度条
        self.download_btn.setEnabled(True)
        self.download_btn.setText("开始下载")
        self.progress_bar.setVisible(False)
        
        # 删除线程对象
        if self.download_thread:
            self.download_thread.deleteLater()
            self.download_thread = None
        
        if success:
            self.statusBar().showMessage("数据下载完成")
            self.log_text.append("-" * 50)
            self.log_text.append("所有数据下载完成！")
            QMessageBox.information(self, '成功', '数据下载完成')
        else:
            self.statusBar().showMessage("数据下载失败")
            self.log_text.append("-" * 50)
            self.log_text.append(f"下载失败: {message}")
            if "已取消" not in message:
                QMessageBox.critical(self, '错误', f'数据下载失败:\n{message}')
                

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DataIntervalSelector()
    window.show()
    
    # 使用try-finally确保程序正确退出
    try:
        exit_code = app.exec_()
    finally:
        # 确保所有线程都已正确关闭
        if hasattr(window, 'download_thread') and window.download_thread and window.download_thread.isRunning():
            window.download_thread.stop()
            window.download_thread.quit()
            window.download_thread.wait()
    
    sys.exit(exit_code)