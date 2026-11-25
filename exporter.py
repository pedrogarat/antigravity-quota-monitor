import os
import sys
import glob
import json
import base64
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from collections import defaultdict

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
        "total_tokens": 0
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
                        dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        model = data.get("model", "desconocido")
                        inp = data.get("input_tokens", 0)
                        out = data.get("output_tokens", 0)
                        cache = data.get("cache_read_tokens", 0)
                        tot = inp + out

                        stats["total_requests"] += 1
                        stats["total_tokens"] += tot

                        if dt >= five_hours_ago:
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

                        if dt >= seven_days_ago:
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

                        if dt >= twenty_four_hours_ago:
                            hour_key = dt.strftime("%Y-%m-%d %H:00")
                            h = hours_24[hour_key]
                            h["requests"] += 1
                            h["input"] += inp
                            h["output"] += out
                            h["cache"] += cache

                        if dt >= fourteen_days_ago:
                            day_key = dt.strftime("%Y-%m-%d")
                            d = days_14[day_key]
                            d["requests"] += 1
                            d["input"] += inp
                            d["output"] += out
                            d["cache"] += cache
                            d["models"][model] += 1
        except Exception:
            pass

    stats["last_5h"]["models"] = dict(models_5h)
    stats["last_7d"]["models"] = dict(models_7d)
    stats["last_24h_by_hour"] = dict(hours_24)
    stats["last_14d_by_day"] = {k: {"requests": v["requests"], "input": v["input"], "output": v["output"], "cache": v["cache"], "models": dict(v["models"])} for k, v in days_14.items()}

    return stats

def github_api_put_file(owner, repo, token, file_path, content_dict, commit_message):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AntigravityQuotaExporter"
    }

    # 1. Check if file exists to get its SHA
    sha = None
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            sha = data.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"[!] Error al comprobar archivo {file_path}: {e}")

    # 2. Prepare PUT payload
    json_bytes = json.dumps(content_dict, indent=2).encode("utf-8")
    b64_content = base64.b64encode(json_bytes).decode("utf-8")

    payload = {
        "message": commit_message,
        "content": b64_content
    }
    if sha:
        payload["sha"] = sha

    payload_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=payload_bytes, headers={**headers, "Content-Type": "application/json"}, method="PUT")
    
    with urllib.request.urlopen(req) as resp:
        return resp.status in (200, 201)

def github_api_get_file(owner, repo, token, file_path):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AntigravityQuotaExporter"
    }
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "content" in data:
                raw_json = base64.b64decode(data["content"]).decode("utf-8")
                return json.loads(raw_json)
    except Exception:
        return None
    return None

def main():
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
    device_id = config.get("device_id") or os.environ.get("COMPUTERNAME", "PC-Default")

    home = os.path.expanduser("~")
    brain_dir = os.path.join(home, ".gemini", "antigravity", "brain")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Recopilando métricas locales para dispositivo: {device_id}...")
    stats = collect_data(brain_dir, device_id)

    # 1. Subir telemetría de este dispositivo
    device_file = f"data/devices/{device_id}.json"
    print(f"Subiendo a GitHub: {device_file}...")
    success = github_api_put_file(owner, repo, token, device_file, stats, f"Update quota telemetry from {device_id}")

    if success:
        print("Datos del dispositivo actualizados con éxito en GitHub.")
    else:
        print("[!] No se pudo subir el archivo del dispositivo.")

    # 2. Actualizar el manifiesto de dispositivos
    manifest = github_api_get_file(owner, repo, token, "data/manifest.json") or {"devices": {}}
    manifest["devices"][device_id] = {
        "updated_at": stats["updated_at"],
        "file": device_file
    }
    manifest["last_sync"] = stats["updated_at"]
    github_api_put_file(owner, repo, token, "data/manifest.json", manifest, f"Update manifest with {device_id}")
    print("Manifiesto global de dispositivos actualizado en GitHub.")

if __name__ == "__main__":
    main()
