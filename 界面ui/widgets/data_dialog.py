from PyQt5.QtWidgets import QDialog, QFileDialog, QTableView, QVBoxLayout

class DataLoadDialog(QDialog):
    # 包含CSV文件选择器和预览表格
    # 采用垂直布局管理组件排列
    def __init__(self):
        super().__init__()
        self.setWindowTitle('加载回测数据')
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # 文件选择组件
        self.file_selector = QFileDialog(self)
        self.file_selector.setNameFilter('CSV文件 (*.csv)')
        
        # 数据预览表格
        self.preview_table = QTableView()
        
        layout.addWidget(self.file_selector)
        layout.addWidget(self.preview_table)
        self.setLayout(layout)