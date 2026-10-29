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

def load_settings(): return load_yaml('config/settings.yaml')
def load_sources(): return load_yaml('config/sources.yaml').get('sources', [])
