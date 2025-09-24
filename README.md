# 量化回测系统

这是一个基于Python和PyQt5的量化回测系统桌面版应用程序。

## 项目结构

```
QT/
├── Qt_main.py           # 桌面版主程序入口
├── utils/               # 工具模块
│   ├── auto_logger.py   # 日志模块
│   └── money_management.py  # 资金管理模块
├── 界面ui/              # 界面相关模块
│   ├── Data_down.py     # 数据下载模块
│   └── main_window.py   # 主窗口模块
├── 数据/                # 数据相关模块
│   └── bian_data.py     # 数据处理模块
├── 策略/                # 策略模块
│   ├── MA双均线择时.py   # 双均线策略
│   └── 参数优化策略.py   # 参数优化策略
├── requirements.txt     # 依赖包列表
└── .venv/              # Python虚拟环境
```

## 程序界面截图

### 主界面
![主界面](截屏2025-09-23%2023.18.52.png)

### 策略选择界面
![策略选择界面](截屏2025-09-23%2023.19.15.png)

### 回测结果界面
![回测结果界面](截屏2025-09-23%2023.20.09.png)

## 安装依赖

在运行程序之前，请确保已安装所有依赖项：

```bash
# 激活虚拟环境
source .venv/bin/activate  # Mac/Linux
# 或
call .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 运行程序

### Mac/Linux系统
```bash
source .venv/bin/activate
python Qt_main.py
```

### Windows系统
```cmd
call .venv\Scripts\activate
python Qt_main.py
```

## 打包程序

### 使用PyInstaller打包为可执行文件

1. 安装PyInstaller:
```bash
pip install pyinstaller
```

2. 打包为Windows exe文件:
```bash
pyinstaller --onefile --windowed --name "量化回测系统" Qt_main.py
```

3. 打包为Mac应用程序:
```bash
pyinstaller --onefile --windowed --name "量化回测系统" Qt_main.py
```

生成的可执行文件将位于 `dist/` 目录中。

## 使用GitHub Actions自动打包

本项目配置了GitHub Actions工作流，可自动打包Windows和macOS版本：

- Windows版本: `.github/workflows/build-windows-exe.yml`
- macOS版本: `.github/workflows/build-macos-app.yml`

## 项目特点

1. 图形化界面操作，易于使用
2. 支持多种量化策略回测
3. 支持参数优化功能
4. 支持数据下载和管理
5. 跨平台支持（Windows、macOS）

## 依赖说明

主要依赖包包括：
- PyQt5: 图形界面库
- pandas: 数据处理
- numpy: 数值计算
- matplotlib: 图表绘制
- pyinstaller: 程序打包

## 注意事项

1. 确保在虚拟环境中运行程序以避免依赖冲突
2. 首次运行前请确保已安装所有依赖包
3. 如遇到中文显示问题，请检查系统字体设置