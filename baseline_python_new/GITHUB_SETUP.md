# GitHub 设置指南

## 📋 步骤1: 在GitHub上创建新仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `rescue-policies-python` (或您喜欢的名称)
   - **Description**: `Python implementation of steady-state calculation for Rescue Policies model`
   - **Visibility**: Public 或 Private（根据您的需要）
   - **不要**勾选 "Initialize this repository with a README"（因为我们已经有了代码）
3. 点击 "Create repository"

## 📋 步骤2: 添加远程仓库并推送

创建仓库后，GitHub会显示仓库URL，格式类似：
- HTTPS: `https://github.com/your-username/rescue-policies-python.git`
- SSH: `git@github.com:your-username/rescue-policies-python.git`

### 使用HTTPS方式（推荐，更简单）：

```bash
cd "c:\Users\Administrator\Desktop\Rescue-Policies-COVID-main"
git remote add origin https://github.com/your-username/rescue-policies-python.git
git push -u origin master
```

### 使用SSH方式（如果已配置SSH密钥）：

```bash
cd "c:\Users\Administrator\Desktop\Rescue-Policies-COVID-main"
git remote add origin git@github.com:your-username/rescue-policies-python.git
git push -u origin master
```

## 📋 步骤3: 验证推送

推送成功后，访问您的GitHub仓库页面，应该能看到所有文件。

## 🔧 如果遇到问题

### 问题1: 认证失败
如果使用HTTPS推送时要求输入用户名和密码：
- 用户名：您的GitHub用户名
- 密码：需要使用Personal Access Token（不是GitHub密码）
  - 创建Token: https://github.com/settings/tokens
  - 选择 "repo" 权限
  - 复制Token作为密码使用

### 问题2: 远程仓库已存在
如果之前已经添加过远程仓库：
```bash
git remote remove origin
git remote add origin <new-repo-url>
git push -u origin master
```

### 问题3: 分支名称不同
如果GitHub使用 `main` 而不是 `master`：
```bash
git branch -M main
git push -u origin main
```

## 📝 推送后的操作

推送成功后，您可以：
1. 在GitHub上查看代码
2. 创建Issues跟踪问题
3. 创建Pull Requests进行协作
4. 添加README.md描述项目

## 🎯 快速命令参考

```bash
# 检查远程仓库
git remote -v

# 查看提交历史
git log --oneline -5

# 查看文件状态
git status

# 推送更新
git push origin master
```

