import asyncio
import logging
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import List, Optional, Tuple
from app.config import RecipientConfig

logger = logging.getLogger(__name__)


def send_email_sync(
    recipient_cfg: RecipientConfig,
    subject: str,
    html_content: str,
    override_to: Optional[str] = None
) -> Tuple[bool, str]:
    """
    同步发送 HTML 邮件，支持 SSL (465) / STARTTLS (587) 及自适应加密。
    返回 (是否成功, 详细结果提示)。
    """
    sender_email = recipient_cfg.sender_email.strip()
    sender_pwd = recipient_cfg.sender_password.strip()
    smtp_host = recipient_cfg.smtp_host.strip()
    smtp_port = recipient_cfg.smtp_port

    if not sender_email or not sender_pwd:
        return False, "发件人邮箱或授权码未配置，无法发送"

    to_email = override_to.strip() if override_to else recipient_cfg.partner_email.strip()
    if not to_email:
        return False, "收件人邮箱未配置"

    recipients_list = [to_email]
    cc_email = recipient_cfg.cc_email.strip() if recipient_cfg.cc_email else ""
    if cc_email and not override_to:
        recipients_list.append(cc_email)

    # 构造 MIME 邮件
    msg = MIMEMultipart("alternative")
    sender_name = recipient_cfg.sender_name.strip() or "Couple Mailer"
    
    msg["From"] = formataddr((str(Header(sender_name, "utf-8")), sender_email))
    msg["To"] = to_email
    if cc_email and not override_to:
        msg["Cc"] = cc_email
    msg["Subject"] = Header(subject, "utf-8")

    # 附加上 HTML 内容
    part_html = MIMEText(html_content, "html", "utf-8")
    msg.attach(part_html)

    server = None
    try:
        # 判断连接协议
        is_ssl = recipient_cfg.smtp_ssl or (smtp_port == 465)
        
        if is_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.ehlo()
            if smtp_port == 587 or server.has_extn("starttls"):
                server.starttls()
                server.ehlo()

        server.login(sender_email, sender_pwd)
        server.sendmail(sender_email, recipients_list, msg.as_string())
        server.quit()
        
        return True, f"邮件成功发送至 {to_email}" + (f" (抄送: {cc_email})" if (cc_email and not override_to) else "")
    except smtplib.SMTPAuthenticationError as e:
        err_msg = f"SMTP 认证授权失败：发件人邮箱或授权密码不正确 ({e})"
        logger.error(err_msg)
        return False, err_msg
    except smtplib.SMTPConnectError as e:
        err_msg = f"SMTP 服务器连接失败：请检查服务器地址与端口 ({e})"
        logger.error(err_msg)
        return False, err_msg
    except Exception as e:
        err_msg = f"发送邮件遇到异常：{str(e)}"
        logger.error(err_msg)
        return False, err_msg
    finally:
        if server:
            try:
                server.close()
            except Exception:
                pass


async def send_email_async(
    recipient_cfg: RecipientConfig,
    subject: str,
    html_content: str,
    override_to: Optional[str] = None
) -> Tuple[bool, str]:
    """在异步线程池中执行邮件发送，不阻塞 FastAPI 事件循环"""
    return await asyncio.to_thread(
        send_email_sync,
        recipient_cfg,
        subject,
        html_content,
        override_to
    )
