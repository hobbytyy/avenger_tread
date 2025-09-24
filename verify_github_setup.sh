#!/bin/bash
# GitHub仓库设置验证脚本

echo "=== GitHub仓库设置验证 ==="

# 检查当前目录
echo "当前目录: $(pwd)"

# 检查是否是Git仓库
if [ -d ".git" ]; then
    echo "✅ 当前目录是Git仓库"
else
    echo "❌ 当前目录不是Git仓库"
    echo "请先运行: git init"
    exit 1
fi

# 检查是否有远程仓库
remote_url=$(git remote get-url origin 2>/dev/null)
if [ -n "$remote_url" ]; then
    echo "✅ 远程仓库已设置: $remote_url"
else
    echo "❌ 未设置远程仓库"
    echo "请运行: git remote add origin hhttps://github.com/hobbytyy/avenger_tread.git"
    exit 1
fi

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  有未提交的更改"
    echo "请运行: git add . && git commit -m 'commit message'"
else
    echo "✅ 所有更改已提交"
fi

# 检查是否已推送到远程仓库
local_commit=$(git rev-parse HEAD)
remote_commit=$(git ls-remote origin main | cut -f1)

if [ "$local_commit" = "$remote_commit" ]; then
    echo "✅ 本地与远程仓库同步"
else
    echo "⚠️  本地与远程仓库不同步"
    echo "请运行: git push origin main"
fi

echo "=== 验证完成 ==="
echo "如果所有检查都通过，您就可以在GitHub上触发Actions工作流了"