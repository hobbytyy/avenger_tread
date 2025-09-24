"""
Windows目录结构适配脚本
将项目文件结构调整为Windows兼容格式
"""

import os
import shutil

def create_windows_structure():
    """创建Windows兼容的目录结构"""
    print("正在创建Windows兼容的目录结构...")
    
    # 创建Windows版本的目录
    dirs_to_create = [
        "data",
        "strategy", 
        "utils",
        "ui"
    ]
    
    for dir_name in dirs_to_create:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"创建目录: {dir_name}")
    
    # 复制文件到Windows目录结构
    try:
        # 复制数据文件
        if os.path.exists("数据"):
            shutil.copytree("数据", "data", dirs_exist_ok=True)
            print("复制数据文件到data目录")
            
        # 复制策略文件
        if os.path.exists("策略"):
            shutil.copytree("策略", "strategy", dirs_exist_ok=True)
            print("复制策略文件到strategy目录")
            
        # 复制工具文件
        if os.path.exists("utils"):
            shutil.copytree("utils", "utils", dirs_exist_ok=True)
            print("复制工具文件到utils目录")
            
        # 复制界面文件
        if os.path.exists("界面ui"):
            shutil.copytree("界面ui", "ui", dirs_exist_ok=True)
            print("复制界面文件到ui目录")
            
        print("Windows目录结构创建完成！")
        
    except Exception as e:
        print(f"创建目录结构时出错: {e}")

def create_windows_requirements():
    """创建Windows版本的requirements.txt"""
    windows_requirements = """PyQt5>=5.15.0
pandas>=1.3.0
numpy>=1.21.0
matplotlib>=3.4.0
pyinstaller>=5.0.0
requests>=2.25.0
"""
    
    with open("windows_requirements.txt", "w", encoding="utf-8") as f:
        f.write(windows_requirements)
    
    print("创建Windows版本的requirements.txt文件")

if __name__ == "__main__":
    create_windows_structure()
    create_windows_requirements()
    print("Windows适配完成！")