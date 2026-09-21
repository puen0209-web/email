# 💌 Couple Daily Automation Mailer & Web Admin (情侣每日暖心早报服务)

一个专为情侣打造的、开箱即用、生产级全栈晨报自动化服务。每天清晨在指定时间向情侣邮箱推送排版精美、温暖浪漫的早报邮件，并提供全中文现代化 Web 可视化管理面板，支持配置热生效、邮件实时预览与一键测试发送。

---

## ✨ 核心特性

1. **每日定时自动投递**：
   - 内置 `APScheduler` 定时引擎，在每天指定时刻（如 `07:30`）全自动生成并发送 HTML 早报。
   - 在 Web 界面修改时间后**即时热重载**，无需重启服务进程。
2. **精美暖色调响应式邮件模板**：
   - 采用行内 CSS（Inline CSS）卡片布局，完美适配 iOS Mail、Gmail、QQ 邮箱、Outlook 及各类移动端/桌面邮件客户端。
   - 包含：温馨问候语、相恋天数胶囊徽章（`❤️ 与你相伴的第 520 天`）、城市天气与体感、智能穿衣与防雨出行提示、纪念日倒计时足迹、AI 晨间情话/心语甄选、爱意落款。
3. **城市天气与智能穿衣出行建议**：
   - 采用全球免费开放的 `wttr.in` JSON 接口（无需申请 API Key，支持中英文全球城市）。
   - 智能规则引擎：根据温差 $\Delta T$、降水概率（PoP）、最高/最低温与紫外线，自动生成洋葱穿衣法、带伞提示、防晒补水与保暖防风建议。
   - 内置网络故障平滑降级机制，离线或超时时自动使用备用天气数据，保障邮件 100% 准时发出。
4. **纪念日与倒计时引擎 (CRUD)**：
   - 自动计算恋爱起始日至今的相伴天数。
   - 支持自定义纪念日/生日列表，支持标记“是否每年重复”；算法自动计算距下一次纪念日的剩余天数并按时间顺序智能高亮排序（当天是纪念日时显示“🎉 就是今天！”）。
5. **AI 晨间情话与备用语录库**：
   - 原生支持标准 OpenAI 规范（`/chat/completions`），完美兼容 OpenAI、DeepSeek、阿里通义千问、Kimi、Moonshot、本地 Ollama（`http://localhost:11434/v1`）等任意大模型。
   - 故障自动降级：当未开启 AI、Token 耗尽或请求超时，自动从可编辑的本地备用情话库中随机抽取温馨语录。
6. **全中文 Web 可视化管理后台 (端口 8080)**：
   - 极简卡片式 UI（Tailwind CSS），响应式适配手机与电脑端。
   - 访问密钥（Admin Key）安全保护，支持实时修改。
   - 提供「💾 保存配置」、「✉️ 立即测试发送」、「👁️ 网页实时预览早报真实渲染效果」与「⚡ 测试大模型响应」。

---

## ⚡ VPS 一键极速部署（推荐）

在任何 Ubuntu / Debian / CentOS / Rocky Linux 服务器上，只需粘贴执行如下单行命令，即可自动配置环境、克隆代码、创建虚拟环境、注册并启动 systemd 守护进程：

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/puen0209-web/email/main/install.sh)"
```

> 💡 安装完成后，在浏览器访问 `http://<你的VPS公网IP>:8080` 即可开始使用，默认管理口令为 `admin888`。

---

## 📁 项目完整目录结构

```text
email/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口、安全鉴权、API 路由与静态托管
│   ├── config.py            # Pydantic V2 配置数据模型与原子写入文件存储
│   ├── scheduler.py         # APScheduler 动态定时调度器与晨报生成主管道
│   ├── mailer.py            # SMTP 邮件投递（支持 SSL 465 / STARTTLS 587 及中文编码）
│   ├── weather.py           # wttr.in 天气数据拉取、中文现象转换与穿衣规则引擎
│   ├── ai_service.py        # OpenAI 兼容大模型客户端与备选名言平滑降级
│   ├── anniversaries.py     # 相恋天数计算与周期性纪念日倒计时算法
│   ├── templates.py         # 暖粉色调精美响应式 HTML 早报邮件模板
│   └── static/
│       └── index.html       # 全中文 Web Admin 仪表盘前端 (Tailwind CSS)
├── data/
│   ├── config.json          # 持久化存储配置文件 (首次启动自动初始化)
│   └── config.example.json  # 配置文件结构参考模板
├── tests/                   # 自动化单元测试集 (100% 通过)
│   ├── __init__.py
│   ├── test_config.py       # 配置加载、原子保存与容错测试
│   ├── test_weather.py      # 天气解析与穿衣规则引擎测试
│   ├── test_anniversaries.py# 相伴天数与闰年跨年重复倒计时测试
│   ├── test_ai_fallback.py  # 大模型调用与语录降级测试
│   ├── test_templates.py    # HTML 模板字段与样式渲染测试
│   └── test_api.py          # Web API 鉴权与端点测试
├── install.sh               # 🚀 VPS 一键全自动生产部署脚本 (支持 systemd/时区/防火墙)
├── docker-compose.yml       # Docker Compose 一键编排文件
├── Dockerfile               # 轻量级 Python 3.12 生产镜像
├── couple-mailer.service    # Linux systemd 系统守护进程配置模板
├── requirements.txt         # 核心生产环境依赖
├── run.py                   # 服务启动脚本 (内置编码适配)
├── .env.example             # 环境变量示例
├── .gitignore               # Git 忽略配置
└── README.md                # 项目全套说明与部署指南
```

---

## 🚀 快速开始（本地运行）

### 1. 环境要求
- Python 3.10 或更高版本
- pip 包管理器

### 2. 安装与启动

```bash
# 1. 克隆或进入项目根目录
cd gmail

# 2. 创建并激活虚拟环境 (推荐)
python -m venv .venv

# Windows 激活:
.venv\Scripts\activate
# Linux / macOS 激活:
source .venv/bin/activate

# 3. 安装轻量依赖
pip install -r requirements.txt

# 4. 启动服务
python run.py
```

终端将输出：
```text
[*] Couple Mailer 服务启动中，访问地址: http://localhost:8080
```

### 3. 访问控制台
用浏览器打开：**`http://localhost:8080`**
- 默认管理口令（Admin Key）为：**`admin888`**
- 首次进入如果弹出输入框，输入 `admin888` 即可获得管理权限。

---

## 🐳 Docker / Docker Compose 部署

Docker 是在云服务器或 NAS 上长期稳定运行的最简方案。配置文件已挂载 `./data` 卷，所有在网页后台修改的内容均会持久化保存在宿主机。

### 使用 Docker Compose（推荐）

1. 在项目目录中直接运行：
   ```bash
   docker compose up -d --build
   ```
2. 查看运行日志：
   ```bash
   docker compose logs -f
   ```
3. 停止或重启：
   ```bash
   docker compose restart
   docker compose down
   ```

### 单独使用 Docker 命令构建运行

```bash
# 构建镜像
docker build -t couple-mailer:latest .

# 启动容器并挂载数据目录
docker run -d \
  --name couple-mailer \
  --restart always \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -e TZ=Asia/Shanghai \
  couple-mailer:latest
```

---

## 🐧 Linux VPS (Ubuntu / Debian) systemd 服务部署

如果希望直接运行在 Linux 云服务器（如腾讯云、阿里云、AWS、华为云等）作为后台系统常驻守护进程：

### 1. 准备代码与依赖
```bash
# 假设部署路径为 /opt/couple-mailer
sudo mkdir -p /opt/couple-mailer
sudo cp -r . /opt/couple-mailer/
cd /opt/couple-mailer

# 创建 Python 虚拟环境并安装依赖
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

### 2. 配置 systemd 服务
复制项目下的 `couple-mailer.service` 到系统服务目录：
```bash
sudo cp couple-mailer.service /etc/systemd/system/couple-mailer.service
```

根据实际路径与用户名检查或修改服务文件：
```ini
[Unit]
Description=Couple Daily Automation Mailer Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/couple-mailer
ExecStart=/opt/couple-mailer/.venv/bin/python run.py
Environment="TZ=Asia/Shanghai"
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

### 3. 启动并启用开机自启
```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start couple-mailer

# 设置开机自启
sudo systemctl enable couple-mailer

# 检查服务状态
sudo systemctl status couple-mailer

# 查看实时日志
journalctl -u couple-mailer -f
```

---

## 📮 常见主流邮箱 SMTP 授权码配置指南

邮件发送依赖发件人的 SMTP 服务。大多数邮箱出于安全考虑，要求使用**专属授权码/应用密码**代替邮箱登录密码。

| 邮箱类型 | SMTP 服务器地址 | 默认端口 | 加密方式 | 授权密码获取方式 |
| :--- | :--- | :--- | :--- | :--- |
| **QQ 邮箱** | `smtp.qq.com` | `465` | SSL (勾选) | 登录 QQ 邮箱网页版 -> 设置 -> 账户 -> 开启 `POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务` -> 生成授权码。 |
| **163 网易邮箱** | `smtp.163.com` | `465` | SSL (勾选) | 登录 163 邮箱网页版 -> 设置 -> POP3/SMTP/IMAP -> 开启 `POP3/SMTP服务` -> 新增授权密码。 |
| **Gmail** | `smtp.gmail.com` | `465` 或 `587` | 465勾选SSL / 587取消勾选(STARTTLS) | 登录 Google 账号 -> 安全性 -> 开启两步验证 -> 在「应用专用密码」中生成 16 位专属密码。 |
| **Outlook / Hotmail** | `smtp.office365.com` | `587` | 取消勾选 SSL (使用 STARTTLS) | 登录 Microsoft 账户安全性 -> 高级安全选项 -> 应用密码。 |

> 💡 **测试小窍门**：在 Web 管理后台配置完成后，点击顶部的「**测试发送**」按钮，填写测试收件箱，即可实时确认发信是否配置正确！

---

## 🤖 大模型 (LLM) API 配置指南

本项目使用标准 OpenAI 规范客户端（异步 `httpx` 实现），无需安装庞大 SDK，支持几乎所有大模型厂商：

### 1. DeepSeek (推荐，性价比与中文表达极高)
- **Base URL**：`https://api.deepseek.com/v1`
- **Model**：`deepseek-chat`
- **API Key**：`sk-...`

### 2. 阿里通义千问 (DashScope)
- **Base URL**：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- **Model**：`qwen-plus` 或 `qwen-turbo`
- **API Key**：`sk-...`

### 3. OpenAI
- **Base URL**：`https://api.openai.com/v1`
- **Model**：`gpt-4o-mini`
- **API Key**：`sk-...`

### 4. 本地 Ollama (零成本私有化运行)
在服务器上安装 Ollama 后，无需 API Key 即可本地生成：
- **Base URL**：`http://localhost:11434/v1`
- **Model**：`qwen2.5:7b` 或 `llama3.2:3b`
- **API Key**：随意填写（如 `ollama`）

> 💡 在后台 AI 配置卡片底部，提供「**⚡ 测试大模型响应**」功能，可即时检验大模型回复速度与文本效果。

---

## 🧪 单元测试

项目内置了完整的测试套件，全面覆盖配置持久化、容错恢复、穿衣出行规则、大模型降级、纪念日倒计时计算、HTML 渲染与 Web 鉴权 API：

```bash
pytest -v
```

所有测试均已在 Python 3.12 环境下验证通过（18 passed）。
