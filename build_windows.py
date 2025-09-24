"""
Windows系统打包脚本
使用PyInstaller将QT量化回测系统打包成Windows exe文件
"""

import subprocess
import sys
import os

def install_pyinstaller():
    """安装PyInstaller"""
    try:
        import PyInstaller
        print("PyInstaller已安装")
    except ImportError:
        print("正在安装PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_windows_executable():
    """构建Windows可执行文件"""
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 切换到项目根目录
    os.chdir(project_root)
    
    # 主程序路径
    main_script = os.path.join(project_root, "Qt_main.py")
    
    # 获取Python可执行文件的路径
    python_executable = sys.executable
    
    # 构建命令
    cmd = [
        python_executable,
        "-m",
        "PyInstaller",
        "--noconfirm",  # 不询问确认
        "--onedir",  # 打包到一个目录
        "--windowed",  # 窗口模式（不显示控制台）
        "--name=量化回测系统",  # 可执行文件名称
        # 添加数据文件和目录（Windows使用分号分隔）
        "--add-data=data;data",
        "--add-data=strategy;strategy",
        "--add-data=utils;utils",
        "--add-data=ui;ui",
        # 排除不必要的模块以减小文件大小
        "--exclude-module=tkinter",
        "--exclude-module=unittest",
        "--exclude-module=email",
        "--exclude-module=xml",
        # 指定主脚本
        main_script
    ]
    
    print("正在构建Windows可执行文件...")
    print("命令:", " ".join(cmd))
    
    try:
        subprocess.check_call(cmd)
        print("构建完成！")
        print("可执行文件位于 dist/目录下")
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_pyinstaller()
    build_windows_executable()