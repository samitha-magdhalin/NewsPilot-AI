from src import config_loader


def test_local_settings_override_is_merged_without_replacing_defaults(tmp_path, monkeypatch):
    root = tmp_path
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "settings.yaml").write_text(
        "news:\n  freshness_hours: 168\nllm:\n  enabled: false\n  model: qwen2.5:3b\n",
        encoding="utf-8",
    )
    (config_dir / "settings.local.yaml").write_text(
        "llm:\n  enabled: true\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config_loader, "ROOT", root)

    settings = config_loader.load_settings()

    assert settings["news"]["freshness_hours"] == 168
    assert settings["llm"] == {"enabled": True, "model": "qwen2.5:3b"}


def test_checked_in_settings_are_used_without_local_override(tmp_path, monkeypatch):
    root = tmp_path
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "settings.yaml").write_text(
        "llm:\n  enabled: false\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config_loader, "ROOT", root)

    assert config_loader.load_settings()["llm"]["enabled"] is False
