import sys
import os
import pandas as pd
import finplot as fplt
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QComboBox, QLineEdit, QPushButton, QFileDialog,
    QFrame, QGraphicsView, QGroupBox, QScrollArea, QButtonGroup
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

        # 左侧控制面板（四个分组 + 滚动容器）
        control = QWidget()
        control_layout = QVBoxLayout(control)

        # 基本设置
        basic_group = QGroupBox('基本设置')
        basic_layout = QVBoxLayout(basic_group)
        self.path_label = QLabel(self.data_path)
        try:
            self.path_label.setWordWrap(True)
        except Exception:
            pass
        btn_choose = QPushButton('选择数据源')
        btn_choose.clicked.connect(self.choose_data)
        basic_layout.addWidget(btn_choose)
        basic_layout.addWidget(self.path_label)
        btn_draw = QPushButton('绘制/刷新')
        btn_reset = QPushButton('重置视图')
        btn_draw.clicked.connect(self.redraw)
        btn_reset.clicked.connect(self.reset_view)
        hl_ops = QHBoxLayout()
        hl_ops.addWidget(btn_draw)
        hl_ops.addWidget(btn_reset)
        basic_layout.addLayout(hl_ops)

        # 工具栏
        tools_group = QGroupBox('工具栏')
        tools_layout = QHBoxLayout(tools_group)
        self.btn_line = QPushButton('画线')
        self.btn_rect = QPushButton('矩形')
        self.btn_del = QPushButton('删除选中')
        self.btn_clear = QPushButton('清空标注')
        # 可选中互斥（工具模式）
        self.btn_line.setCheckable(True)
        self.btn_rect.setCheckable(True)
        tool_group = QButtonGroup(self)
        tool_group.setExclusive(True)
        tool_group.addButton(self.btn_line)
        tool_group.addButton(self.btn_rect)
        # 连接功能
        self.btn_line.clicked.connect(self.add_line_roi)
        self.btn_rect.clicked.connect(self.add_rect_roi)
        self.btn_del.clicked.connect(self.delete_selected_roi)
        self.btn_clear.clicked.connect(self.clear_rois)
        tools_layout.addWidget(self.btn_line)
        tools_layout.addWidget(self.btn_rect)
        tools_layout.addWidget(self.btn_del)
        tools_layout.addWidget(self.btn_clear)

        # 主图指标
        main_group = QGroupBox('主图指标')
        main_form = QFormLayout(main_group)
        self.cmb_main = QComboBox()
        self.cmb_main.addItems(['无', 'EMA', '布林带'])
        main_form.addRow(QLabel('主图指标'), self.cmb_main)
        self.edit_ema = QLineEdit('5,10,20')
        self.lbl_ema = QLabel('EMA周期(逗号分隔)')
        main_form.addRow(self.lbl_ema, self.edit_ema)
        self.edit_bb_period = QLineEdit('20')
        self.lbl_bb_period = QLabel('布林周期')
        main_form.addRow(self.lbl_bb_period, self.edit_bb_period)
        self.edit_bb_mult = QLineEdit('2')
        self.lbl_bb_mult = QLabel('布林倍数')
        main_form.addRow(self.lbl_bb_mult, self.edit_bb_mult)

        # 子图指标
        sub_group = QGroupBox('子图指标')
        sub_form = QFormLayout(sub_group)
        self.cmb_sub1 = QComboBox()
        self.cmb_sub1.addItems(['成交量', '无'])
        sub_form.addRow(QLabel('子图1'), self.cmb_sub1)
        self.cmb_sub2 = QComboBox()
        self.cmb_sub2.addItems(['MACD', '无'])
        sub_form.addRow(QLabel('子图2'), self.cmb_sub2)
        self.edit_macd = QLineEdit('12,26,9')
        self.lbl_macd = QLabel('MACD参数 fast,slow,signal')
        sub_form.addRow(self.lbl_macd, self.edit_macd)

        # 加入控制面板
        control_layout.addWidget(basic_group)
        control_layout.addWidget(tools_group)
        control_layout.addWidget(main_group)
        control_layout.addWidget(sub_group)

        # 左侧使用滚动区域，避免高度溢出
        scroll = QScrollArea()
        scroll.setWidget(control)
        scroll.setWidgetResizable(True)

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
        splitter.addWidget(scroll)
        # 在右侧放一个边框包裹，避免黑边
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.Shape.StyledPanel)
        rf_layout = QVBoxLayout(right_frame)
        rf_layout.setContentsMargins(0, 0, 0, 0)
        rf_layout.addWidget(self.gv)
        splitter.addWidget(right_frame)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        # 初始尺寸：右侧约 4/5，左侧约 1/5
        try:
            total_w = max(self.width(), 700)
            left_w = max(200, int(total_w * 1 / 5))
            right_w = max(500, int(total_w * 4 / 5))
            splitter.setSizes([left_w, right_w])
        except Exception:
            pass

        # 创建并准备初始数据与绘图
        try:
            self.df = self.prepare_df(self.data_path)
        except Exception:
            pass
        self.build_axes()
        # 初始参数区可见性
        try:
            self.cmb_main.currentTextChanged.connect(self._update_main_params_visibility)
            self.cmb_sub1.currentTextChanged.connect(self._update_sub_params_visibility)
            self.cmb_sub2.currentTextChanged.connect(self._update_sub_params_visibility)
            self._update_main_params_visibility()
            self._update_sub_params_visibility()
        except Exception:
            pass
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

        # 使用finplot默认配色

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

        # 保持默认网格设置

        # 在主图添加一个可更新的悬停图例标签（显示OHLC）
        try:
            self.hover_label = fplt.add_legend('', ax=self.ax0)
            # 仅调整图例样式，提高可读性（不改变整图背景）
            try:
                self.hover_label.setStyleSheet(
                    "background-color: rgba(255,255,255,0.92);"
                    "color: #111; padding: 3px 6px; border-radius: 3px;"
                )
            except Exception:
                pass
        except Exception:
            self.hover_label = None

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

    # 工具栏：ROI绘制与管理
    def _get_viewbox(self):
        try:
            return self.ax0.vb
        except Exception:
            try:
                return self.ax0.ax_widget.plotItem.vb
            except Exception:
                return None

    def add_line_roi(self):
        vb = self._get_viewbox()
        if vb is None:
            self.statusBar().showMessage('未获取到ViewBox，无法画线', 5000)
            return
        xr, yr = vb.viewRange()
        xmid = (xr[0] + xr[1]) / 2
        ymid = (yr[0] + yr[1]) / 2
        roi = pg.LineSegmentROI([[xmid - (xr[1]-xr[0])*0.1, ymid], [xmid + (xr[1]-xr[0])*0.1, ymid]], pen='r')
        vb.addItem(roi)
        if not hasattr(self, 'rois'):
            self.rois = []
        self.rois.append(roi)
        self.statusBar().showMessage('已添加线段，拖动端点可调整', 3000)

    def add_rect_roi(self):
        vb = self._get_viewbox()
        if vb is None:
            self.statusBar().showMessage('未获取到ViewBox，无法绘制矩形', 5000)
            return
        xr, yr = vb.viewRange()
        w = (xr[1] - xr[0]) * 0.2
        h = (yr[1] - yr[0]) * 0.2
        x = xr[0] + (xr[1] - xr[0]) * 0.4
        y = yr[0] + (yr[1] - yr[0]) * 0.4
        roi = pg.RectROI([x, y], [w, h], pen='y')
        vb.addItem(roi)
        if not hasattr(self, 'rois'):
            self.rois = []
        self.rois.append(roi)
        self.statusBar().showMessage('已添加矩形，拖动可调整大小与位置', 3000)

    def delete_selected_roi(self):
        removed = False
        if hasattr(self, 'rois'):
            for roi in list(self.rois):
                try:
                    if hasattr(roi, 'isSelected') and roi.isSelected():
                        vb = self._get_viewbox()
                        if vb:
                            vb.removeItem(roi)
                        self.rois.remove(roi)
                        removed = True
                except Exception:
                    pass
            if not removed and self.rois:
                roi = self.rois.pop()
                vb = self._get_viewbox()
                if vb:
                    try:
                        vb.removeItem(roi)
                    except Exception:
                        pass
                removed = True
        self.statusBar().showMessage('已删除选中标注' if removed else '无选中标注', 3000)

    def clear_rois(self):
        vb = self._get_viewbox()
        cnt = 0
        if hasattr(self, 'rois'):
            for roi in list(self.rois):
                try:
                    if vb:
                        vb.removeItem(roi)
                    cnt += 1
                except Exception:
                    pass
            self.rois.clear()
        self.statusBar().showMessage(f'已清空标注 {cnt} 个', 3000)

    # 参数区显示/隐藏逻辑
    def _update_main_params_visibility(self):
        t = self.cmb_main.currentText() if hasattr(self, 'cmb_main') else '无'
        ema = (t == 'EMA')
        bb = (t == '布林带')
        for w in [self.lbl_ema, self.edit_ema]:
            try:
                w.setVisible(ema)
            except Exception:
                pass
        for w in [self.lbl_bb_period, self.edit_bb_period, self.lbl_bb_mult, self.edit_bb_mult]:
            try:
                w.setVisible(bb)
            except Exception:
                pass

    def _update_sub_params_visibility(self):
        # 子图1当前无参数；子图2：仅在MACD时显示
        t2 = self.cmb_sub2.currentText() if hasattr(self, 'cmb_sub2') else '无'
        macd = (t2 == 'MACD')
        for w in [self.lbl_macd, self.edit_macd]:
            try:
                w.setVisible(macd)
            except Exception:
                pass

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

        # 绑定悬停事件以更新顶部图例显示OHLC
        try:
            def _update_hover_legend(x, y):
                if self.hover_label is None or self.df is None:
                    return
                try:
                    ts = pd.Timestamp(x)
                except Exception:
                    ts = x
                row = None
                try:
                    row = self.df.loc[self.df['time'] == ts]
                except Exception:
                    row = None
                if row is None or row.empty:
                    # 取最近时间索引作为兜底
                    try:
                        idx = self.df['time'].searchsorted(ts)
                        idx = max(0, min(len(self.df) - 1, int(idx)))
                        row = self.df.iloc[[idx]]
                    except Exception:
                        return
                o = float(row['open'].iloc[0])
                h = float(row['high'].iloc[0])
                l = float(row['low'].iloc[0])
                c = float(row['close'].iloc[0])
                # 收盘高于开盘为多头绿色，否则为空头红色
                # 涨红、跌黄
                color = 'f00' if c >= o else 'ff0'
                txt = (
                    f"<span style='font-size:13px; color:#111'>"
                    f"开:<span style='color:#{color}'>{o:.4f}</span> "
                    f"高:<span style='color:#222'>{h:.4f}</span> "
                    f"低:<span style='color:#222'>{l:.4f}</span> "
                    f"收:<span style='color:#{color}'>{c:.4f}</span>"
                    f"</span>"
                )
                try:
                    self.hover_label.setText(txt)
                except Exception:
                    pass

            # when='hover' 表示随鼠标移动更新（新版API推荐）
            try:
                fplt.set_mouse_callback(_update_hover_legend, ax=self.ax0, when='hover')
            except Exception:
                # 兼容旧版本
                fplt.set_time_inspector(_update_hover_legend, ax=self.ax0, when='hover')
        except Exception:
            # 忽略绑定失败，不影响其他功能
            pass


def main():
    app = QApplication(sys.argv)
    win = KlineWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()