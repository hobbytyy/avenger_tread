# 如何触发Windows版本打包

## 方法一：通过GitHub网站手动触发

1. 访问您的GitHub仓库：
   https://github.com/hobbytyy/avenger_tread

2. 点击顶部的"Actions"选项卡

3. 在左侧边栏中，点击"Build Windows Executable"工作流

4. 点击右侧的"Run workflow"按钮

5. 在弹出的对话框中，再次点击绿色的"Run workflow"按钮确认

6. 等待工作流执行完成（大约需要5-10分钟）

7. 工作流完成后，点击已完成的任务

8. 在"Artifacts"部分，点击"windows-executable"下载打包好的Windows版本

## 方法二：通过命令行触发（需要GitHub CLI）

如果您安装了GitHub CLI，可以运行以下命令：

```bash
gh workflow run "Build Windows Executable"
```

然后检查工作流状态：

```bash
gh run list
```

## 下载Windows版本

打包完成后，您可以从以下位置下载Windows版本：
- GitHub Actions页面的Artifacts部分
- GitHub Releases页面（如果配置了自动发布）

## Windows版本使用说明

下载完成后：
1. 解压zip文件
2. 将整个文件夹复制到Windows电脑上
3. 双击"量化回测系统.exe"运行程序