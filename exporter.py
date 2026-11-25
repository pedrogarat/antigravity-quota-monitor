import os
import sys
import glob
import json
import time
import base64
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from collections import defaultdict

REQUEST_TIMEOUT = 15


def collect_data(brain_dir, device_id):
    now = datetime.now(timezone.utc)
    five_hours_ago = now - timedelta(hours=5)
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)
    twenty_four_hours_ago = now - timedelta(hours=24)

    stats = {
        "device_id": device_id,
        "updated_at": now.isoformat(),
        "last_5h": {"requests": 0, "input_tokens": 0, "output_tokens": 0, "cache_tokens": 0, "models": {}},
        "last_7d": {"requests": 0, "input_tokens": 0, "output_tokens": 0, "cache_tokens": 0, "models": {}},
        "last_24h_by_hour": {},
        "last_14d_by_day": {},
        "total_requests": 0,
        "total_tokens": 0,
    }

    models_5h = defaultdict(lambda: {"requests": 0, "input": 0, "output": 0, "cache": 0})
    models_7d = defaultdict(lambda: {"requests": 0, "input": 0, "output": 0, "cache": 0})
    hours_24 = defaultdict(lambda: {"requests": 0, "input": 0, "output": 0, "cache": 0})
    days_14 = defaultdict(lambda: {"requests": 0, "input": 0, "output": 0, "cache": 0, "models": defaultdict(int)})

    pattern = os.path.join(brain_dir, "*", ".system_generated", "logs", "transcript.jsonl")
    for path in glob.glob(pattern):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except Exception:
                        continue

                    if data.get("source") == "MODEL" and "input_tokens" in data:
                        created_at_str = data.get("created_at")
                        if not created_at_str:
                            continue
                        try:
                            dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        except ValueError:
                            continue
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        dt_utc = dt.astimezone(timezone.utc)
                        dt_local = dt.astimezone()

                        model = data.get("model", "desconocido")
                        inp = int(data.get("input_tokens") or 0)
                        out = int(data.get("output_tokens") or 0)
                        cache = int(data.get("cache_read_tokens") or 0)
                        tot = inp + out

                        stats["total_requests"] += 1
                        stats["total_tokens"] += tot

                        if dt_utc >= five_hours_ago:
                            p = stats["last_5h"]
                            p["requests"] += 1
                            p["input_tokens"] += inp
                            p["output_tokens"] += out
                            p["cache_tokens"] += cache
                            m = models_5h[model]
                            m["requests"] += 1
                            m["input"] += inp
                            m["output"] += out
                            m["cache"] += cache

                        if dt_utc >= seven_days_ago:
                            p = stats["last_7d"]
                            p["requests"] += 1
                            p["input_tokens"] += inp
                            p["output_tokens"] += out
                            p["cache_tokens"] += cache
                            m = models_7d[model]
                            m["requests"] += 1
                            m["input"] += inp
                            m["output"] += out
                            m["cache"] += cache

                        if dt_utc >= twenty_four_hours_ago:
                            # Guardamos la hora en ISO UTC para que el panel la muestre en hora local
                            hour_key = dt_utc.strftime("%Y-%m-%dT%H:00:00Z")
                            h = hours_24[hour_key]
                            h["requests"] += 1
                            h["input"] += inp
                            h["output"] += out
                            h["cache"] += cache

                        if dt_utc >= fourteen_days_ago:
                            # Agrupamos por fecha local del equipo
                            day_key = dt_local.strftime("%Y-%m-%d")
                            d = days_14[day_key]
                            d["requests"] += 1
                            d["input"] += inp
                            d["output"] += out
                            d["cache"] += cache
                            d["models"][model] += 1
        except Exception:
            pass

    stats["last_5h"]["models"] = dict(sorted(models_5h.items()))
    stats["last_7d"]["models"] = dict(sorted(models_7d.items()))
    stats["last_24h_by_hour"] = dict(sorted(hours_24.items()))
    stats["last_14d_by_day"] = {
        k: {
            "requests": v["requests"],
            "input": v["input"],
            "output": v["output"],
            "cache": v["cache"],
            "models": dict(sorted(v["models"].items())),
        }
        for k, v in sorted(days_14.items())
    }

    return stats


def _github_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AntigravityQuotaExporter",
    }


def github_api_get_file_with_sha(owner, repo, token, file_path):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    req = urllib.request.Request(url, headers=_github_headers(token), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            sha = data.get("sha")
            content = None
            if "content" in data:
                raw_json = base64.b64decode(data["content"]).decode("utf-8")
                content = json.loads(raw_json)
            return content, sha
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, None
        raise


def github_api_put_file(owner, repo, token, file_path, content_dict, commit_message, sha=None):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    headers = {**_github_headers(token), "Content-Type": "application/json"}

    json_bytes = json.dumps(content_dict, indent=2, ensure_ascii=False).encode("utf-8")
    b64_content = base64.b64encode(json_bytes).decode("utf-8")

    payload = {
        "message": commit_message,
        "content": b64_content,
    }
    if sha:
        payload["sha"] = sha

    payload_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=payload_bytes, headers=headers, method="PUT")

    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return resp.status in (200, 201)


def stats_without_timestamp(stats):
    if not isinstance(stats, dict):
        return None
    copy = dict(stats)
    copy.pop("updated_at", None)
    return copy


def update_manifest_with_retry(owner, repo, token, device_id, device_file, updated_at, max_retries=3):
    for attempt in range(max_retries):
        manifest, sha = github_api_get_file_with_sha(owner, repo, token, "data/manifest.json")
        if not isinstance(manifest, dict):
            manifest = {"devices": {}}
        if "devices" not in manifest or not isinstance(manifest["devices"], dict):
            manifest["devices"] = {}

        manifest["devices"][device_id] = {
            "updated_at": updated_at,
            "file": device_file,
        }
        manifest["last_sync"] = updated_at

        try:
            if github_api_put_file(
                owner,
                repo,
                token,
                "data/manifest.json",
                manifest,
                f"Update manifest with {device_id}",
                sha=sha,
            ):
                return True
        except urllib.error.HTTPError as e:
            if e.code in (409, 422) and attempt < max_retries - 1:
                wait_s = 1.5 * (attempt + 1)
                print(f"[!] Conflicto al actualizar manifest.json (HTTP {e.code}), reintentando en {wait_s:.1f}s...")
                time.sleep(wait_s)
                continue
            raise
    return False


def main():
    force_upload = "--force" in sys.argv
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")

    if not os.path.exists(config_path):
        print(f"[ERROR] No se encontró 'config.json' en {script_dir}.")
        print("Por favor, copia 'config.example.json' a 'config.json' y añade tu token de GitHub.")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    owner = config["repo_owner"]
    repo = config["repo_name"]
    token = config["github_token"]
    device_id = (config.get("device_id") or os.environ.get("COMPUTERNAME") or "PC-Default").strip()

    home = os.path.expanduser("~")
    brain_dir = os.path.join(home, ".gemini", "antigravity", "brain")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Recopilando métricas locales para dispositivo: {device_id}...")
    stats = collect_data(brain_dir, device_id)
    device_file = f"data/devices/{device_id}.json"

    try:
        remote_stats, remote_sha = github_api_get_file_with_sha(owner, repo, token, device_file)
    except Exception as e:
        print(f"[ERROR] No se pudo conectar con GitHub para leer {device_file}: {e}")
        sys.exit(1)

    if not force_upload and stats_without_timestamp(stats) == stats_without_timestamp(remote_stats):
        print("Sin cambios en las métricas desde la última sincronización; se omite la subida.")
        return

    print(f"Subiendo a GitHub: {device_file}...")
    try:
        success = github_api_put_file(
            owner,
            repo,
            token,
            device_file,
            stats,
            f"Update quota telemetry from {device_id}",
            sha=remote_sha,
        )
    except Exception as e:
        print(f"[ERROR] No se pudo subir {device_file}: {e}")
        sys.exit(1)

    if not success:
        print("[ERROR] GitHub no confirmó la actualización del archivo del dispositivo.")
        sys.exit(1)

    print("Datos del dispositivo actualizados con éxito en GitHub.")

    try:
        update_manifest_with_retry(owner, repo, token, device_id, device_file, stats["updated_at"])
        print("Manifiesto global de dispositivos actualizado en GitHub.")
    except Exception as e:
        print(f"[ERROR] No se pudo actualizar data/manifest.json: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
