# 量化回测系统

这是一个基于Python的量化回测系统，支持桌面版和Web版两种使用方式。

## 项目结构

```
QT/
├── 界面ui/
│   ├── Data_down.py     # 数据下载模块
│   └── main.py          # 桌面版主程序
├── 数据/
│   └── bian_data.py     # 数据处理模块
├── web_app.py           # Web版主程序
├── requirements.txt     # 依赖包列表
├── build_windows_complete.bat  # Windows打包脚本
├── debug_run.bat        # 桌面版调试脚本
├── fix_and_run.bat      # 桌面版修复运行脚本
├── run_web_app.sh       # Web版启动脚本 (Mac/Linux)
├── run_web_app.bat      # Web版启动脚本 (Windows)
└── .venv/               # Python虚拟环境
```

## 安装依赖

在运行任何版本之前，请确保已安装所有依赖项：

```bash
# 激活虚拟环境
source .venv/bin/activate  # Mac/Linux
# 或
call .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 桌面版使用

### Windows系统
双击运行 `界面ui/main.py` 或使用以下脚本：
- `debug_run.bat` - 调试运行
- `fix_and_run.bat` - 修复并运行

### Mac/Linux系统
```bash
source .venv/bin/activate
python 界面ui/main.py
```

## Web版使用

### Mac/Linux系统
```bash
# 方法1: 直接运行
source .venv/bin/activate
streamlit run web_app.py

# 方法2: 使用启动脚本
./run_web_app.sh
```

### Windows系统
```cmd
REM 方法1: 直接运行
call .venv\Scripts\activate
streamlit run web_app.py

REM 方法2: 使用启动脚本
run_web_app.bat
```

运行后，打开浏览器访问 http://localhost:8501 查看Web应用。

## 打包桌面版

### Windows系统
双击运行 `build_windows_complete.bat` 脚本进行打包。

## 故障排除

1. 如果遇到模块导入错误，请确保在虚拟环境中运行程序
2. 如果Web版无法启动，请检查是否已安装Streamlit:
   ```bash
   pip install streamlit
   ```
3. 如果数据下载失败，请检查网络连接和API密钥设置