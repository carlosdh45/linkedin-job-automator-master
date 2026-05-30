import os
import re
import sys
import yaml

_ENV_RE = re.compile(r'\$\{([^}]+)\}')


def _interpolate(value):
    if isinstance(value, str):
        def _replace(m):
            var = m.group(1)
            v = os.environ.get(var)
            if v is None:
                print(f"WARNING: ${{{var}}} referenced in config but not set in environment")
                return ""
            return v
        return _ENV_RE.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _interpolate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(v) for v in value]
    return value


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config = _interpolate(config)
    _validate(config)
    return config


def _validate(config: dict) -> None:
    required = [
        ("linkedin", "email"),
        ("linkedin", "password"),
        ("paths", "cv_pdf"),
        ("paths", "jobs_csv"),
        ("paths", "database"),
        ("apis", "anthropic_api_key"),
    ]
    errors = []
    for section, key in required:
        if not config.get(section, {}).get(key):
            errors.append(f"  [{section}][{key}]")
    if errors:
        print("ERROR: missing required config fields (or env vars not set):")
        for e in errors:
            print(e)
        sys.exit(1)
