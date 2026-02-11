"""
Zentrale Secrets-Konfiguration für ha-german-voice Scripts.

Liest Secrets aus Environment-Variablen oder /config/secrets.yaml.
NIEMALS Secrets direkt in dieses File schreiben!

Auf dem HA-Server: Environment-Variablen im Docker-Container setzen,
oder /config/secrets.yaml nutzen (wird von .gitignore ignoriert).
"""

import os
import sys


def _read_secrets_yaml():
    """Liest /config/secrets.yaml falls vorhanden."""
    secrets_path = "/config/secrets.yaml"
    if not os.path.exists(secrets_path):
        return {}

    secrets = {}
    try:
        with open(secrets_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, _, value = line.partition(":")
                    value = value.strip().strip("'\"")
                    secrets[key.strip()] = value
    except Exception:
        pass
    return secrets


_secrets = _read_secrets_yaml()


def get_secret(key, env_key=None, required=True):
    """Secret aus Environment oder secrets.yaml lesen.

    Priorität: ENV > secrets.yaml

    Args:
        key: Schlüssel in secrets.yaml
        env_key: Environment-Variable (default: key in UPPER_CASE)
        required: Wenn True, wird bei fehlendem Secret sys.exit(1) aufgerufen
    """
    env_key = env_key or key.upper()

    # 1. Environment-Variable
    value = os.environ.get(env_key)
    if value:
        return value

    # 2. secrets.yaml
    value = _secrets.get(key)
    if value:
        return value

    if required:
        print(f"ERROR: Secret '{key}' nicht gefunden. "
              f"Setze ENV '{env_key}' oder füge '{key}' zu /config/secrets.yaml hinzu.",
              file=sys.stderr)
        sys.exit(1)

    return None


# ============================================================================
# Exportierte Secrets
# ============================================================================

HA_TOKEN = get_secret("ha_token", "HA_TOKEN")
SPOTIFY_CLIENT_ID = get_secret("spotify_client_id", "SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = get_secret("spotify_client_secret", "SPOTIFY_CLIENT_SECRET")
