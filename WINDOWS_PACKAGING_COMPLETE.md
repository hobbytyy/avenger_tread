# Windows版本打包完整指南

## 概述
本文档详细介绍了如何将量化回测系统打包成Windows可执行文件(.exe)，即使您当前使用的是Mac系统。

## 方案一：使用GitHub Actions自动打包（推荐）

### 1. 准备工作
确保您的代码已推送到GitHub仓库。

### 2. 触发打包流程
- 提交代码到main分支，或
- 在GitHub仓库的Actions页面手动触发"Build Windows Executable"工作流

### 3. 下载打包结果
打包完成后，您可以在以下位置找到Windows版本：
1. Actions页面的Artifacts部分
2. GitHub Releases页面

## 方案二：使用Parallels Desktop虚拟机手动打包

### 1. 设置Windows虚拟机
在Parallels Desktop中安装Windows 10或Windows 11系统。

### 2. 安装Python环境
在Windows虚拟机中：
1. 下载并安装Python 3.9或更高版本
2. 确保将Python添加到系统PATH

### 3. 复制项目文件
将项目文件从Mac复制到Windows虚拟机：
```cmd
# 在Windows PowerShell中执行
mkdir quant-backtest
# 将Mac上的项目文件复制到此目录
```

### 4. 安装依赖
在Windows命令提示符中执行：
```cmd
cd quant-backtest
pip install -r requirements.txt
pip install pyinstaller
```

### 5. 运行打包脚本
```cmd
python build_windows.py
```

### 6. 获取打包结果
打包完成后，可执行文件位于`dist`目录中。

## 方案三：使用在线CI/CD服务

### 使用AppVeyor
1. 注册AppVeyor账户
2. 连接您的GitHub仓库
3. 创建`appveyor.yml`配置文件：
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
专门用于Windows环境的打包脚本：
- 自动安装PyInstaller
- 使用Windows兼容的路径分隔符
- 包含所有必要的数据文件

### 目录结构适配
Windows版本使用以下目录结构：
- `data` - 数据文件目录
- `strategy` - 策略文件目录  
- `utils` - 工具文件目录
- `ui` - 界面文件目录

## 常见问题及解决方案

### 1. 打包后程序无法运行
确保所有依赖都已正确包含：
```cmd
pip install -r requirements.txt
```

### 2. 缺少DLL文件
在Windows环境中打包时，PyInstaller会自动包含所需的DLL文件。

### 3. 防病毒软件误报
某些防病毒软件可能会将打包的程序识别为潜在威胁，这是误报。可以将程序添加到白名单。

### 4. 打包文件过大
可以通过排除不必要的模块来减小文件大小。

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

## 技术支持

如遇到问题，请参考以下资源：
1. PyInstaller官方文档
2. GitHub Actions文档
3. 项目README.md文件