from pathlib import Path
from typing import Optional


def find_env_path(start: Optional[Path] = None, name: str = ".env", max_ancestors: int = 5) -> Optional[Path]:
    """Search upward from `start` (or cwd / script dir) for `name` and return its Path."""
    search_starts = []
    if start is not None:
        search_starts.append(start.resolve() if start.is_dir() else start.resolve().parent)
    search_starts.append(Path.cwd())
    search_starts.append(Path(__file__).resolve().parent)

    for s in search_starts:
        cur = s
        for _ in range(max_ancestors + 1):
            candidate = cur / name
            if candidate.exists():
                return candidate
            if cur.parent == cur:
                break
            cur = cur.parent
    return None


def read_env(path: Optional[Path] = None) -> dict:
    """Read a simple KEY=VALUE .env file into a dict. If `path` is None, attempt to find it upward."""
    if path is None:
        path = find_env_path()
    env = {}
    if path is None:
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env
