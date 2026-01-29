"""API client for Chemical Equipment backend. Uses Basic Auth."""
import base64
import os
from typing import Optional

import requests

DEFAULT_BASE = os.environ.get("API_BASE", "http://localhost:8000")
API_BASE = f"{DEFAULT_BASE.rstrip('/')}/api"


def _auth_headers(username: str, password: str) -> dict:
    raw = f"{username}:{password}"
    encoded = base64.b64encode(raw.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def _req(
    method: str,
    path: str,
    *,
    username: str,
    password: str,
    json: Optional[dict] = None,
    files: Optional[dict] = None,
    stream: bool = False,
) -> requests.Response:
    url = f"{API_BASE}{path}"
    headers = _auth_headers(username, password)
    kwargs = {"headers": headers, "timeout": 30, "stream": stream}
    if json is not None:
        kwargs["json"] = json
    if files is not None:
        kwargs["files"] = files
        if "json" in kwargs:
            del kwargs["json"]
    r = requests.request(method, url, **kwargs)
    return r


def login(username: str, password: str) -> bool:
    """Verify credentials by calling /api/history/."""
    r = _req("GET", "/history/", username=username, password=password)
    return r.status_code == 200


def upload_file(filepath: str, username: str, password: str) -> dict:
    with open(filepath, "rb") as f:
        name = os.path.basename(filepath)
        files = {"file": (name, f, "text/csv")}
        r = _req("POST", "/upload/", files=files, username=username, password=password)
    r.raise_for_status()
    return r.json()


def get_summary(upload_id: int, username: str, password: str) -> dict:
    r = _req("GET", f"/summary/{upload_id}/", username=username, password=password)
    r.raise_for_status()
    return r.json()


def get_data(upload_id: int, username: str, password: str) -> dict:
    r = _req("GET", f"/data/{upload_id}/", username=username, password=password)
    r.raise_for_status()
    return r.json()


def get_history(username: str, password: str) -> list:
    r = _req("GET", "/history/", username=username, password=password)
    r.raise_for_status()
    return r.json()


def download_pdf(upload_id: int, save_path: str, username: str, password: str) -> None:
    r = _req("GET", f"/report/{upload_id}/pdf/", username=username, password=password, stream=True)
    r.raise_for_status()
    with open(save_path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
