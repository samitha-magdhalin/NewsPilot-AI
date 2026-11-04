from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

def load_yaml(path: str | Path) -> dict:
    p = Path(path)
    if not p.is_absolute(): p = ROOT / p
    with p.open('r', encoding='utf-8') as f:
        value = yaml.safe_load(f) or {}
    if not isinstance(value, dict): raise ValueError(f"Expected YAML mapping in {p}")
    return value

def _merge_settings(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_settings(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_settings():
    settings = load_yaml('config/settings.yaml')
    local_settings = ROOT / 'config' / 'settings.local.yaml'
    if local_settings.exists():
        settings = _merge_settings(settings, load_yaml(local_settings))
    return settings


def load_sources(): return load_yaml('config/sources.yaml').get('sources', [])
