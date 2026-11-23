"""
update.py
Controllo aggiornamenti via API GitHub Releases.
"""

import json
import urllib.error
import urllib.request

from version import __version__

APP_NAME = "Netplan"
GITHUB_REPO = "Nsfr750/netplan"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{GITHUB_REPO}/releases"
TIMEOUT = 8


def _version_tuple(tag: str) -> tuple:
    """'v1.2.3' -> (1, 2, 3): componenti mancanti/non numeriche -> 0."""
    parts = []
    for p in tag.lstrip("vV").split("."):
        digits = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def check_for_updates(current: str = __version__) -> dict:
    """Interroga GitHub per l'ultima release pubblicata.

    Returns:
        {"update_available": bool, "latest": str, "current": str,
         "url": str, "name": str, "published_at": str, "error": str|None}
    """
    result = {
        "update_available": False,
        "latest": None,
        "current": current,
        "url": RELEASES_PAGE,
        "name": "",
        "published_at": "",
        "error": None,
    }
    req = urllib.request.Request(
        API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{APP_NAME}/{current}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        result["error"] = str(e)
        return result
    except json.JSONDecodeError as e:
        result["error"] = f"risposta non valida: {e}"
        return result

    latest = data.get("tag_name", "").lstrip("vV")
    result["latest"] = latest or None
    result["url"] = data.get("html_url", RELEASES_PAGE)
    result["name"] = data.get("name", "")
    result["published_at"] = data.get("published_at", "")
    if latest:
        result["update_available"] = _version_tuple(latest) > _version_tuple(current)
    return result
