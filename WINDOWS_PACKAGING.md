# Windows版本打包指南

## 概述
本文档介绍了如何将量化回测系统打包成Windows可执行文件(.exe)。由于PyInstaller不支持跨平台编译，我们需要在Windows环境中进行打包。

## 方案一：使用GitHub Actions（推荐）

### 设置步骤
1. 将代码推送到GitHub仓库
2. GitHub Actions会自动在Windows环境中打包程序
3. 打包完成后，可以在Actions页面下载Windows版本

### 使用方法
1. 提交代码到main分支
2. 访问GitHub仓库的Actions页面
3. 等待工作流执行完成
4. 下载生成的Windows可执行文件

## 方案二：使用Parallels Desktop虚拟机

### 设置步骤
1. 在Parallels Desktop中安装Windows系统
2. 在Windows中安装Python 3.9+
3. 复制项目代码到Windows系统
4. 安装依赖：
   ```cmd
   pip install -r requirements.txt
   pip install pyinstaller
   ```
5. 运行打包脚本：
   ```cmd
   python build_windows.py
   ```

## 方案三：使用在线CI/CD服务

### AppVeyor设置
1. 注册AppVeyor账户
2. 连接GitHub仓库
3. 创建appveyor.yml配置文件：
   ```yaml
   version: 1.0.{build}
   image: Visual Studio 2019
   
   environment:
     matrix:
       - PYTHON: "C:\\Python39-x64"
   
   install:
     - "%PYTHON%\\python.exe -m pip install --upgrade pip"
     - "%PYTHON%\\python.exe -m pip install -r requirements.txt"
     - "%PYTHON%\\python.exe -m pip install pyinstaller"
   
   build_script:
     - "%PYTHON%\\python.exe build_windows.py"
   
   artifacts:
     - path: dist\*
       name: windows-executable
   ```

## Windows打包脚本说明

### build_windows.py
该脚本专门用于Windows环境打包：
- 使用PyInstaller进行打包
- 包含所有必要的数据文件
- 生成窗口化应用程序（无控制台窗口）

### 目录结构适配
Windows版本会自动适配目录分隔符和路径：
- 使用`;`作为数据文件分隔符
- 自动处理路径转换

## 常见问题

### 1. 打包后程序无法运行
确保所有依赖都已正确包含：
```cmd
pip install -r requirements.txt
```

### 2. 缺少DLL文件
在Windows环境中打包时，PyInstaller会自动包含所需的DLL文件。

### 3. 防病毒软件误报
某些防病毒软件可能会将打包的程序识别为潜在威胁，这是误报。

## 分发说明

### 文件结构
打包后的Windows程序包含：
- 主执行文件：量化回测系统.exe
- 依赖库目录：_internal
- 数据文件目录：data, strategy, utils, ui

### 运行要求
用户无需安装Python，程序包含所有必要组件。

## 自动化部署

### GitHub Releases
每次推送到main分支时，GitHub Actions会自动创建Release并上传Windows版本。

### 版本管理
使用GitHub Actions的运行编号作为版本标识。