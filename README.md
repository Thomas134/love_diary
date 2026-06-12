# 恋爱日记 · Love Diary

一个简洁优美的私人恋爱日记网站，支持密码保护、日记撰写、照片上传，部署于 Railway 云平台。

## ✨ 功能

- 🔐 **密码保护** - 只有知道密码的人才能进入
- 📖 **日记管理** - 写日记、编辑、删除，支持心情标签和封面图
- 📸 **照片墙** - 上传、浏览、删除照片，支持拖拽上传和灯箱预览
- ☁️ **云端存储** - 文字存 PostgreSQL，图片存 Cloudinary，数据永不丢失
- 📱 **响应式设计** - 手机/电脑都好看

## 🚀 Railway 部署步骤

### 第一步：准备 Cloudinary 账号

1. 访问 [cloudinary.com](https://cloudinary.com) 注册免费账号
2. 登录后打开 Dashboard，记录右侧的：
   - **Cloud Name**
   - **API Key**
   - **API Secret**

### 第二步：部署到 Railway

1. 将本项目推送到 GitHub（新建一个私有仓库）
   ```bash
   git init
   git add .
   git commit -m "初始化恋爱日记网站"
   git remote add origin https://github.com/你的用户名/love-diary.git
   git push -u origin main
   ```

2. 访问 [railway.app](https://railway.app)，用 GitHub 账号登录

3. 点击 **New Project** → **Deploy from GitHub repo** → 选择你的仓库

4. 添加 PostgreSQL 数据库：
   - 在项目内点击 **+ New** → **Database** → **Add PostgreSQL**
   - Railway 会自动将 `DATABASE_URL` 注入到你的应用

5. 配置环境变量（点击你的 Web Service → **Variables**）：

   | 变量名 | 值 |
   |--------|-----|
   | `SITE_PASSWORD` | 你们的专属密码（自定义） |
   | `SECRET_KEY` | 随机长字符串（见下方生成方式） |
   | `CLOUDINARY_CLOUD_NAME` | Cloudinary Dashboard 里的值 |
   | `CLOUDINARY_API_KEY` | Cloudinary Dashboard 里的值 |
   | `CLOUDINARY_API_SECRET` | Cloudinary Dashboard 里的值 |

   生成 SECRET_KEY：
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

6. Railway 会自动构建并部署，稍等 1-2 分钟，访问分配的域名即可！

### 第三步：绑定自定义域名（可选）

在 Railway 项目的 **Settings → Domains** 里可以绑定自己买的域名。

## 🛠️ 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 复制环境变量文件
cp .env.example .env
# 编辑 .env，填入你的配置

# 启动
python app.py
```

访问 http://localhost:5000

## 📁 项目结构

```
love_diary/
├── app.py              # 后端主程序
├── requirements.txt    # Python 依赖
├── Procfile            # Railway/Heroku 启动命令
├── railway.toml        # Railway 配置
├── .env.example        # 环境变量示例
└── templates/
    ├── base.html       # 基础模板
    ├── login.html      # 登录页
    ├── diary_list.html # 日记列表
    ├── diary_form.html # 写/编辑日记
    ├── diary_detail.html # 日记详情
    └── photo_wall.html # 照片墙
```
