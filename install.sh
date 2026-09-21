#!/usr/bin/env bash
# ==============================================================================
# Couple Daily Automation Mailer - VPS 一键全自动生产部署脚本
# 仓库地址: https://github.com/puen0209-web/email.git
# 支持系统: Ubuntu / Debian / CentOS / Rocky Linux / AlmaLinux
# ==============================================================================

set -e

# 颜色高亮
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

APP_NAME="couple-mailer"
INSTALL_DIR="/opt/couple-mailer"
REPO_URL="https://github.com/puen0209-web/email.git"
SERVICE_NAME="couple-mailer.service"
PORT=8080

echo -e "${PURPLE}"
cat << "EOF"
  ____                  _         __  __       _ _           
 / ___|___  _   _ _ __ | | ___   |  \/  | __ _(_) | ___ _ __ 
| |   / _ \| | | | '_ \| |/ _ \  | |\/| |/ _` | | |/ _ \ '__|
| |__| (_) | |_| | |_) | |  __/  | |  | | (_| | | |  __/ |   
 \____\___/ \__,_| .__/|_|\___|  |_|  |_|\__,_|_|_|\___|_|   
                 |_|                                          
EOF
echo -e "${CYAN}>>> 情侣每日暖心早报服务 (Couple Daily Mailer) VPS 一键安装脚本 <<<${NC}\n"

# 1. 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[错误] 请使用 root 权限或 sudo 运行此脚本！${NC}"
    echo -e "示例: sudo bash $0"
    exit 1
fi

# 2. 检查并安装系统包管理器依赖
echo -e "${BLUE}[1/6] 正在检查并更新系统基础依赖环境...${NC}"
if [ -f /etc/debian_version ]; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y python3 python3-pip python3-venv git curl tzdata
elif [ -f /etc/redhat-release ]; then
    yum update -y
    yum install -y python3 python3-pip git curl tzdata
    # CentOS 8+ / Rocky 可能需要 python3-devel
    yum install -y python3-devel gcc || true
else
    echo -e "${YELLOW}[警告] 未识别的 Linux 发行版，尝试继续使用现有 python3 与 git 环境...${NC}"
fi

# 设置系统时区为中国标准时间 (Asia/Shanghai)
if [ -f /usr/share/zoneinfo/Asia/Shanghai ]; then
    ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
    echo "Asia/Shanghai" > /etc/timezone || true
    echo -e "${GREEN}✓ 系统时区已同步为 Asia/Shanghai${NC}"
fi

# 3. 准备代码目录
echo -e "\n${BLUE}[2/6] 正在拉取 / 更新项目源代码...${NC}"

# 如果当前目录就是项目目录（已包含 run.py 和 requirements.txt）
if [ -f "run.py" ] && [ -f "requirements.txt" ]; then
    echo -e "${GREEN}✓ 检测到当前已在项目目录中，将以当前目录作为部署目标${NC}"
    INSTALL_DIR="$(pwd)"
else
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo -e "${YELLOW}检测到已存在 $INSTALL_DIR，正在拉取最新代码...${NC}"
        cd "$INSTALL_DIR"
        git pull origin main || git pull origin master || true
    else
        echo -e "正在克隆仓库 $REPO_URL 到 $INSTALL_DIR ..."
        mkdir -p "$INSTALL_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
fi

# 4. 创建并配置 Python 虚拟环境
echo -e "\n${BLUE}[3/6] 正在配置 Python 独立虚拟环境并安装生产依赖...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

./.venv/bin/pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple --extra-index-url https://pypi.org/simple || ./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --extra-index-url https://pypi.org/simple || ./.venv/bin/pip install -r requirements.txt

echo -e "${GREEN}✓ 依赖安装完毕！${NC}"

# 5. 配置文件初始化
echo -e "\n${BLUE}[4/6] 初始化持久化数据文件...${NC}"
mkdir -p data
if [ ! -f "data/config.json" ]; then
    if [ -f "data/config.example.json" ]; then
        cp data/config.example.json data/config.json
    fi
fi

# 6. 配置 systemd 服务单元
echo -e "\n${BLUE}[5/6] 正在配置 systemd 守护进程与开机自启动...${NC}"

cat > /etc/systemd/system/${SERVICE_NAME} << EOF
[Unit]
Description=Couple Daily Automation Mailer Service
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/.venv/bin/python run.py
Environment="PYTHONUNBUFFERED=1"
Environment="TZ=Asia/Shanghai"
Environment="HOST=0.0.0.0"
Environment="PORT=${PORT}"
Restart=always
RestartSec=5s
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl restart ${SERVICE_NAME}

# 7. 开放防火墙端口 (如果启用了 ufw 或 firewalld)
echo -e "\n${BLUE}[6/6] 检查系统防火墙策略...${NC}"
if command -v ufw >/dev/null 2>&1; then
    if ufw status | grep -q "Status: active"; then
        ufw allow ${PORT}/tcp || true
        echo -e "${GREEN}✓ 已在 ufw 防火墙开放端口 ${PORT}/tcp${NC}"
    fi
fi

if command -v firewall-cmd >/dev/null 2>&1; then
    if systemctl is-active --quiet firewalld; then
        firewall-cmd --zone=public --add-port=${PORT}/tcp --permanent || true
        firewall-cmd --reload || true
        echo -e "${GREEN}✓ 已在 firewalld 防火墙开放端口 ${PORT}/tcp${NC}"
    fi
fi

# 8. 检查运行状态与公网 IP
sleep 2
IS_ACTIVE=$(systemctl is-active ${SERVICE_NAME} || true)

PUBLIC_IP=$(curl -s4 -m 5 https://api.ipify.org || curl -s4 -m 5 https://ifconfig.me || echo "你的VPS公网IP")

echo -e "\n=================================================================="
if [ "$IS_ACTIVE" = "active" ]; then
    echo -e "${GREEN}🎉 恭喜！Couple Mailer 服务已在后台成功启动并配置开机自启！${NC}"
else
    echo -e "${YELLOW}⚠️ 服务已创建，当前状态为: ${IS_ACTIVE}。可通过 journalctl -u ${SERVICE_NAME} -f 排查原因${NC}"
fi
echo -e "=================================================================="
echo -e "🌐 Web 可视化控制台地址: ${CYAN}http://${PUBLIC_IP}:${PORT}${NC}"
echo -e "🔐 默认管理访问口令:    ${YELLOW}admin888${NC}"
echo -e "📂 项目代码安装路径:    ${BLUE}${INSTALL_DIR}${NC}"
echo -e "💾 配置文件存放路径:    ${BLUE}${INSTALL_DIR}/data/config.json${NC}"
echo -e "------------------------------------------------------------------"
echo -e "常用运维指令："
echo -e "  查看实时日志:   ${CYAN}journalctl -u ${SERVICE_NAME} -f${NC}"
echo -e "  查看运行状态:   ${CYAN}systemctl status ${SERVICE_NAME}${NC}"
echo -e "  重启服务进程:   ${CYAN}systemctl restart ${SERVICE_NAME}${NC}"
echo -e "  停止服务进程:   ${CYAN}systemctl stop ${SERVICE_NAME}${NC}"
echo -e "==================================================================\n"
