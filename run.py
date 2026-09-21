import sys
import os

# 适配 Windows 控制台默认编码，防止由于 Emoji 导致 UnicodeEncodeError
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"[*] Couple Mailer 服务启动中，访问地址: http://localhost:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
