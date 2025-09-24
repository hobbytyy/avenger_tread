# GitHub推送操作详细步骤

## 1. 初始化Git仓库（如果还没有）
cd /Users/mac/Documents/QT
git init

## 2. 配置Git用户信息（首次使用需要）
git config --global user.name "您的姓名"
git config --global user.email "您的邮箱@example.com"

## 3. 添加所有文件
git add .

## 4. 提交文件
git commit -m "Initial commit of quant backtest system"

## 5. 在GitHub上创建仓库后，将本地仓库与GitHub仓库关联
# 注意：将username替换为您的GitHub用户名，将repository-name替换为您的仓库名
git remote add origin https://github.com/username/repository-name.git

## 6. 推送代码到GitHub
git branch -M main
git push -u origin main

## 7. 如果提示输入用户名和密码
# GitHub现在使用Personal Access Token而不是密码
# 您需要创建一个Personal Access Token：
# 1. 访问 https://github.com/settings/tokens
# 2. 点击"Generate new token"
# 3. 选择适当的权限（repo权限即可）
# 4. 生成token后，复制它
# 5. 当Git提示输入密码时，粘贴您的token

## 8. 验证推送是否成功
# 您可以在GitHub仓库页面刷新查看文件是否已上传