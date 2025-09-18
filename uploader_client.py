# backend/uploader_client.py
"""
Helpers used by backend/app.py to:
- query discovery for peers
- measure RTT to peers
- pick nearest peers
- upload chunk files to chosen peers
- fetch chunk bytes from peers (for download/reassemble)
"""
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# change this if needed or set DISCOVERY_URL env var in app.py and pass it
# DISCOVERY_URL = "http://127.0.0.1:4000"

DEFAULT_REPLICATION = 3
CANDIDATE_LIMIT = 40
HEAD_TIMEOUT = 1.5


def get_peers(discovery_url: str, limit: int = CANDIDATE_LIMIT):
    r = requests.get(f"{discovery_url.rstrip('/')}/peers", params={"limit": limit}, timeout=4)
    r.raise_for_status()
    return r.json().get("peers", [])


def measure_rtt(peer: dict) -> float:
    """Return measured RTT (seconds) or inf on failure."""
    url = f"http://{peer['ip']}:{peer['port']}/store"
    start = time.time()
    try:
        # many small servers accept HEAD; if not, this may 405 — handle gracefully
        r = requests.head(url, timeout=HEAD_TIMEOUT)
        # treat 405 as success for RTT measurement
        if r.status_code >= 400 and r.status_code != 405:
            # still accept as measurement
            pass
        return time.time() - start
    except Exception:
        return float("inf")


def pick_nearest(peers: list, r: int = DEFAULT_REPLICATION, max_workers: int = 16) -> list:
    if not peers:
        return []
    with ThreadPoolExecutor(max_workers=min(max_workers, len(peers))) as ex:
        futures = {ex.submit(measure_rtt, p): p for p in peers}
        results = []
        for f in as_completed(futures, timeout=6):
            p = futures[f]
            try:
                rtt = f.result()
            except Exception:
                rtt = float("inf")
            results.append((rtt, p))
    results.sort(key=lambda x: x[0])
    chosen = [p for (lat, p) in results if lat < float("inf")][:r]
    if len(chosen) < r:
        chosen = [p for (_, p) in results][:r]
    return chosen


def upload_chunk_to_peer(peer: dict, chunk_path: str, chunk_hash: str, timeout: int = 10) -> dict:
    url = f"http://{peer['ip']}:{peer['port']}/store"
    with open(chunk_path, "rb") as fh:
        files = {"file": (chunk_hash, fh)}
        data = {"file_hash": chunk_hash}
        resp = requests.post(url, files=files, data=data, timeout=timeout)
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status": "ok"}


def distribute_chunk(discovery_url: str, chunk_path: str, chunk_hash: str, replication: int = DEFAULT_REPLICATION) -> list:
    """
    Return a list of assignment dicts: [{"node_id":..., "ip":..., "port":..., "status": "ok"|"fail", "error": ...}, ...]
    """
    peers = get_peers(discovery_url)
    chosen = pick_nearest(peers, r=replication)
    results = []
    for p in chosen:
        rec = {"node_id": p["node_id"], "ip": p["ip"], "port": p["port"]}
        try:
            upload_chunk_to_peer(p, chunk_path, chunk_hash)
            rec["status"] = "ok"
        except Exception as e:
            rec["status"] = "fail"
            rec["error"] = str(e)
        results.append(rec)
    return results


def fetch_chunk_from_peer(peer: dict, chunk_hash: str, timeout: int = 10) -> bytes:
    url = f"http://{peer['ip']}:{peer['port']}/retrieve/{chunk_hash}"
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.content
