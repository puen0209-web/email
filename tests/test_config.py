import os
from pathlib import Path
import pytest
from app.config import AppConfig, load_config, save_config, AnniversaryItem


def test_default_config():
    cfg = AppConfig()
    assert cfg.recipient.daily_time == "07:30"
    assert cfg.recipient.smtp_port == 465
    assert cfg.basic.city == "上海"
    assert len(cfg.anniversaries) >= 1
    assert len(cfg.fallback_quotes) >= 5
    assert cfg.security.admin_password == "admin888"


def test_save_and_load_config(tmp_path: Path):
    test_file = tmp_path / "test_config.json"
    cfg = AppConfig()
    cfg.basic.city = "北京"
    cfg.basic.partner_name = "小仙女"
    cfg.anniversaries.append(AnniversaryItem(name="纪念日测试", date="2024-05-20", repeat_annually=True, icon="🌹"))

    save_config(cfg, test_file)
    assert test_file.exists()

    loaded = load_config(test_file)
    assert loaded.basic.city == "北京"
    assert loaded.basic.partner_name == "小仙女"
    assert any(a.name == "纪念日测试" for a in loaded.anniversaries)


def test_corrupted_config_fallback(tmp_path: Path):
    test_file = tmp_path / "corrupted_config.json"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("{ invalid json structure ...")

    loaded = load_config(test_file)
    assert loaded is not None
    assert loaded.basic.city == "上海"
    # 检查是否产生了备份文件
    backup = tmp_path / "corrupted_config.json.bak"
    assert backup.exists()
