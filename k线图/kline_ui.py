import sys
import os
import pandas as pd
import finplot as fplt
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFileDialog,
    QFrame, QGraphicsView
)

from indicators import calculate_macd, calculate_ema, calculate_bollinger_bands


class KlineWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('K线图界面')
        self.resize(1200, 800)

        # 状态
        self.df = None
        self.data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '数据', 'btc_data_1d.csv')

        # 主布局：左右分割
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        # 左侧控制面板
        control = QWidget()
        control_layout = QVBoxLayout(control)
        form = QFormLayout()
        control_layout.addLayout(form)

        # 数据源选择
        self.path_label = QLabel(self.data_path)
        btn_choose = QPushButton('选择数据源')
        btn_choose.clicked.connect(self.choose_data)
        hl_path = QHBoxLayout()
        hl_path.addWidget(self.path_label)
        hl_path.addWidget(btn_choose)
        control_layout.addLayout(hl_path)

        # 主图指标下拉
        self.cmb_main = QComboBox()
        self.cmb_main.addItems(['无', 'EMA', '布林带'])
        form.addRow(QLabel('主图指标'), self.cmb_main)

        # 子图1 下拉
        self.cmb_sub1 = QComboBox()
        self.cmb_sub1.addItems(['成交量', '无'])
        form.addRow(QLabel('子图1'), self.cmb_sub1)

        # 子图2 下拉
        self.cmb_sub2 = QComboBox()
        self.cmb_sub2.addItems(['MACD', '无'])
        form.addRow(QLabel('子图2'), self.cmb_sub2)

        # 参数输入
        self.edit_ema = QLineEdit('5,10,20')
        form.addRow(QLabel('EMA周期(逗号分隔)'), self.edit_ema)
        self.edit_bb_period = QLineEdit('20')
        form.addRow(QLabel('布林周期'), self.edit_bb_period)
        self.edit_bb_mult = QLineEdit('2')
        form.addRow(QLabel('布林倍数'), self.edit_bb_mult)
        self.edit_macd = QLineEdit('12,26,9')
        form.addRow(QLabel('MACD参数 fast,slow,signal'), self.edit_macd)

        # 操作按钮
        btn_draw = QPushButton('绘制/刷新')
        btn_reset = QPushButton('重置视图')
        btn_snapshot = QPushButton('截图PNG')
        btn_draw.clicked.connect(self.redraw)
        btn_reset.clicked.connect(self.reset_view)
        btn_snapshot.clicked.connect(self.snapshot)
        hl_ops = QHBoxLayout()
        hl_ops.addWidget(btn_draw)
        hl_ops.addWidget(btn_reset)
        hl_ops.addWidget(btn_snapshot)
        control_layout.addLayout(hl_ops)

        # 右侧绘图区容器
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(0)

        # 使用 QGraphicsView + finplot 嵌入
        self.gv = QGraphicsView()
        self.right_layout = QVBoxLayout()
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)
        self.gv.setLayout(self.right_layout)

        # 分割器加入左右面板
        splitter.addWidget(control)
        # 在右侧放一个边框包裹，避免黑边
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.Shape.StyledPanel)
        rf_layout = QVBoxLayout(right_frame)
        rf_layout.setContentsMargins(0, 0, 0, 0)
        rf_layout.addWidget(self.gv)
        splitter.addWidget(right_frame)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        # 初始尺寸：右侧约 6/7，左侧约 1/7（更窄）
        try:
            total_w = max(self.width(), 700)
            left_w = max(150, int(total_w * 1 / 7))
            right_w = max(500, int(total_w * 6 / 7))
            splitter.setSizes([left_w, right_w])
        except Exception:
            pass

        # 创建并准备初始数据与绘图
        try:
            self.df = self.prepare_df(self.data_path)
        except Exception:
            pass
        self.build_axes()
        if self.df is not None:
            self.redraw()

    # 数据读取与映射
    def prepare_df(self, path: str) -> pd.DataFrame:
        df = pd.read_csv(path)
        # 与现有脚本一致的列重命名
        rename_map = {
            '交易时间': 'time',
            '开盘价': 'open',
            '最高价': 'high',
            '最低价': 'low',
            '收盘价': 'close',
            '成交量': 'volume'
        }
        df = df.rename(columns=rename_map)
        # 时间列转换
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
        return df

    # 构建/重建轴部件
    def build_axes(self):
        # 清空右侧现有轴部件
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        # 创建3行联动的 finplot 轴
        axs = fplt.create_plot_widget(self.gv, rows=3)
        # 兼容返回类型（可能是列表或元组）
        if isinstance(axs, (list, tuple)):
            self.ax0, self.ax1, self.ax2 = axs
            self.gv.axs = [self.ax0, self.ax1, self.ax2]  # finplot要求
            # 堆叠到右侧布局，设置高度权重：主图3，子图各1
            self.right_layout.addWidget(self.ax0.ax_widget, 3)
            self.right_layout.addWidget(self.ax1.ax_widget, 1)
            self.right_layout.addWidget(self.ax2.ax_widget, 1)
            self.right_layout.setStretch(0, 3)
            self.right_layout.setStretch(1, 1)
            self.right_layout.setStretch(2, 1)
        else:
            # 万一只返回一个轴（不期望），也处理
            self.ax0 = axs
            self.ax1 = fplt.add_plot(ax=self.ax0)
            self.ax2 = fplt.add_plot(ax=self.ax0)
            self.gv.axs = [self.ax0, self.ax1, self.ax2]
            self.right_layout.addWidget(self.ax0.ax_widget, 3)
            self.right_layout.addWidget(self.ax1.ax_widget, 1)
            self.right_layout.addWidget(self.ax2.ax_widget, 1)
            self.right_layout.setStretch(0, 3)
            self.right_layout.setStretch(1, 1)
            self.right_layout.setStretch(2, 1)

        # 准备绘图（不启动事件循环）
        fplt.show(qt_exec=False)

    def choose_data(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择CSV数据源', os.path.dirname(self.data_path), 'CSV Files (*.csv *.CSV)')
        if path:
            self.data_path = path
            self.path_label.setText(path)
            try:
                self.df = self.prepare_df(path)
                self.redraw()
            except Exception as e:
                self.statusBar().showMessage(f'读取失败: {e}', 5000)

    def reset_view(self):
        try:
            # 重新创建轴并重绘
            self.build_axes()
            if self.df is not None:
                self.redraw()
        except Exception as e:
            self.statusBar().showMessage(f'重置失败: {e}', 5000)

    def snapshot(self):
        try:
            out = os.path.join(os.path.dirname(__file__), 'kline_snapshot.png')
            fplt.saveplot(out)
            self.statusBar().showMessage(f'已保存截图: {out}', 5000)
        except Exception as e:
            self.statusBar().showMessage(f'截图失败: {e}', 5000)

    def _parse_ints(self, text: str):
        try:
            return [int(x.strip()) for x in text.split(',') if x.strip()]
        except Exception:
            return []

    def _parse_floats(self, text: str):
        try:
            return [float(x.strip()) for x in text.split(',') if x.strip()]
        except Exception:
            return []

    def redraw(self):
        if self.df is None:
            return

        df = self.df.copy()

        # 计算主图指标
        if self.cmb_main.currentText() == 'EMA':
            periods = self._parse_ints(self.edit_ema.text()) or [5, 10, 20]
            df = calculate_ema(df, periods=periods)
        elif self.cmb_main.currentText() == '布林带':
            try:
                period = int(self.edit_bb_period.text())
            except Exception:
                period = 20
            try:
                mult = float(self.edit_bb_mult.text())
            except Exception:
                mult = 2
            df = calculate_bollinger_bands(df, period=period, std_multiplier=mult)

        # 计算子图2（MACD）
        if self.cmb_sub2.currentText() == 'MACD':
            try:
                fast, slow, signal = self._parse_ints(self.edit_macd.text())
            except Exception:
                fast, slow, signal = 12, 26, 9
            df = calculate_macd(df, fast=fast or 12, slow=slow or 26, signal=signal or 9)

        # 清理并绘制主图
        fplt.candlestick_ochl(df[['time', 'open', 'close', 'high', 'low']], ax=self.ax0)

        if self.cmb_main.currentText() == 'EMA':
            periods = self._parse_ints(self.edit_ema.text()) or [5, 10, 20]
            colors = ['#ff0000', '#00ff00', '#0000ff']
            for i, p in enumerate(periods):
                col = colors[i % len(colors)]
                fplt.plot(df['time'], df[f'ema_{p}'], ax=self.ax0, legend=f'EMA{p}', color=col)

        elif self.cmb_main.currentText() == '布林带':
            fplt.plot(df['time'], df['bb_middle'], ax=self.ax0, legend='BB Mid', color='#2ca02c')
            fplt.plot(df['time'], df['bb_upper'], ax=self.ax0, legend='BB Upper', color='#ff7f0e')
            fplt.plot(df['time'], df['bb_lower'], ax=self.ax0, legend='BB Lower', color='#ff7f0e')
            fplt.fill_between(df['time'], df['bb_lower'], df['bb_upper'], ax=self.ax0, color='#ff7f0e22')

        # 子图1：成交量或无
        if self.cmb_sub1.currentText() == '成交量':
            fplt.volume_ocv(df[['time', 'open', 'close', 'volume']], ax=self.ax1)

        # 子图2：MACD或无
        if self.cmb_sub2.currentText() == 'MACD':
            fplt.volume_ocv(df[['time', 'open', 'close', 'hist']], ax=self.ax2, colorfunc=fplt.strength_colorfilter)
            fplt.plot(df['time'], df['macd'], ax=self.ax2, legend='MACD', color='#0000ff')
            fplt.plot(df['time'], df['signal'], ax=self.ax2, legend='Signal', color='#ff0000')

        # 刷新显示
        fplt.refresh()


def main():
    app = QApplication(sys.argv)
    win = KlineWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()