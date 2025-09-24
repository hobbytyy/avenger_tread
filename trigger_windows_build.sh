#!/bin/bash
# 触发GitHub Actions打包Windows版本的脚本

echo "=== 触发GitHub Actions打包Windows版本 ==="

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "检测到未提交的更改，正在提交..."
    git add .
    git commit -m "Update before triggering Windows build"
    git push origin main
else
    echo "没有未提交的更改"
fi

echo "请访问以下URL手动触发GitHub Actions工作流："
echo "https://github.com/hobbytyy/avenger_tread/actions"
echo ""
echo "操作步骤："
echo "1. 点击页面上的'Build Windows Executable'工作流"
echo "2. 点击右侧的'Run workflow'按钮"
echo "3. 点击绿色的'Run workflow'确认按钮"
echo "4. 等待大约5-10分钟直到工作流完成"
echo "5. 在工作流页面的Artifacts部分下载'windows-executable'"