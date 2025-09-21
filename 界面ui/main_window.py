from PyQt5.QtWidgets import QMainWindow, QWidget, QDockWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # 包含中央K线图区域和右侧控制面板
        # 已实现基础菜单栏功能
        self.setWindowTitle('量化回测系统')
        self.setGeometry(300, 300, 1200, 800)
        
        # 创建核心组件区域
        self.chart_area = QWidget()
        self.setCentralWidget(self.chart_area)
        
        # 右侧控制面板
        self.control_panel = QDockWidget('控制面板', self)
        self.addDockWidget(2, self.control_panel)
        
        # 初始化菜单栏
        self.init_menu()

    def init_menu(self):
        file_menu = self.menuBar().addMenu('文件')
        file_menu.addAction('加载数据', self.open_data_dialog)

    def open_data_dialog(self):
        pass