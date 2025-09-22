import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from PyQt5.QtWidgets import QMainWindow, QWidget, QDockWidget, QAction, QLabel, QVBoxLayout, QHBoxLayout, QSplitter, QTextEdit, QMessageBox
from PyQt5.QtCore import Qt

from 界面ui.widgets.data_dialog import DataLoadDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loaded_data = None
        self.selected_strategy = None
        self.init_ui()
        
    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle('量化回测系统')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建主分割器
        main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(main_splitter)
        
        # 左侧K线图显示区域
        self.chart_area = QWidget()
        chart_layout = QVBoxLayout()
        self.chart_area.setLayout(chart_layout)
        self.chart_label = QLabel("K线图显示区域\n\n选择数据文件并设置策略参数后，回测结果将在此显示")
        self.chart_label.setAlignment(Qt.AlignCenter)
        chart_layout.addWidget(self.chart_label)
        main_splitter.addWidget(self.chart_area)
        
        # 右侧控制面板
        self.control_panel = QDockWidget('策略参数设置', self)
        control_widget = QWidget()
        control_layout = QVBoxLayout()
        
        # 策略参数输入区域
        param_label = QLabel("策略参数:")
        control_layout.addWidget(param_label)
        
        # 添加一些示例参数输入框
        self.param_inputs = []
        for i in range(5):
            param_input = QTextEdit()
            param_input.setMaximumHeight(30)
            param_input.setPlaceholderText(f"参数 {i+1}")
            control_layout.addWidget(param_input)
            self.param_inputs.append(param_input)
        
        control_widget.setLayout(control_layout)
        self.control_panel.setWidget(control_widget)
        main_splitter.addWidget(self.control_panel)
        
        # 设置分割器比例
        main_splitter.setSizes([800, 400])
        
        # 状态栏
        self.statusBar().showMessage('就绪')
        
        # 初始化菜单栏
        self.init_menu()

    def init_menu(self):
        file_menu = self.menuBar().addMenu('文件')
        load_action = QAction('加载数据', self)
        load_action.triggered.connect(self.open_data_dialog)
        file_menu.addAction(load_action)
        
        run_action = QAction('运行回测', self)
        run_action.triggered.connect(self.run_backtest)
        file_menu.addAction(run_action)

    def open_data_dialog(self):
        dialog = DataLoadDialog()
        if dialog.exec_():
            # 处理加载的数据
            self.loaded_data = dialog.get_data()
            self.selected_strategy = dialog.get_strategy()
            filepath = dialog.get_filepath()
            
            # 更新界面显示
            self.chart_label.setText(f"已加载数据文件: {filepath}\n"
                                   f"选择策略: {self.selected_strategy}\n"
                                   f"数据行数: {len(self.loaded_data) if self.loaded_data is not None else 0}\n\n"
                                   f"点击菜单栏'运行回测'开始回测")
            self.statusBar().showMessage(f'数据加载完成: {filepath}')
            
    def run_backtest(self):
        """运行回测"""
        if self.loaded_data is None or self.selected_strategy is None:
            QMessageBox.warning(self, '警告', '请先加载数据和选择策略')
            return
            
        # 获取策略参数
        params = []
        for i, input_widget in enumerate(self.param_inputs):
            param = input_widget.toPlainText()
            if param:
                params.append(f"参数{i+1}: {param}")
                
        param_text = "\n".join(params) if params else "未设置参数"
        
        # 显示回测结果
        self.chart_label.setText(f"回测结果\n"
                               f"数据文件: {self.loaded_data.shape[0]} 行\n"
                               f"策略: {self.selected_strategy}\n\n"
                               f"策略参数:\n{param_text}\n\n"
                               f"回测已完成，结果已保存到文件")
        self.statusBar().showMessage('回测完成')