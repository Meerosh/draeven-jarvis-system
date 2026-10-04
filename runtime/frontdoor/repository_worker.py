"""Approval-gated GitHub repository work for Draeven's Front Door."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse


MANAGED_ROOT = Path(r"C:\Users\Arach\Documents\Jarvis\Citadel\repositories")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
SECRET_RE = re.compile(r"sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}")


class RepositoryWorkerError(RuntimeError):
    pass


class RepositoryWorker:
    def __init__(self, root: Path = MANAGED_ROOT):
        self.root = Path(root)

    def _run(self, args: list[str], *, cwd: Path | None = None, timeout: int = 600) -> subprocess.CompletedProcess:
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=timeout)
        if result.returncode:
            raise RepositoryWorkerError((result.stderr or result.stdout or "command failed").strip())
        return result

    def _repo(self, name: str) -> Path:
        if not NAME_RE.fullmatch(name or ""):
            raise RepositoryWorkerError("Repository name contains unsupported characters.")
        root = self.root.resolve()
        path = (root / name).resolve()
        if path.parent != root:
            raise RepositoryWorkerError("Repository path escaped the managed workspace.")
        return path

    @staticmethod
    def _github_url(url: str) -> tuple[str, str]:
        parsed = urlparse(url.strip())
        if parsed.scheme != "https" or parsed.hostname not in {"github.com", "www.github.com"} or parsed.username:
            raise RepositoryWorkerError("Only credential-free HTTPS GitHub repository URLs are accepted.")
        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if len(parts) != 2:
            raise RepositoryWorkerError("Use a GitHub URL shaped like https://github.com/owner/repository.")
        name = parts[1][:-4] if parts[1].endswith(".git") else parts[1]
        if not NAME_RE.fullmatch(name):
            raise RepositoryWorkerError("The GitHub repository name is unsupported.")
        return f"https://github.com/{parts[0]}/{name}.git", name

    def list(self) -> list[dict]:
        if not self.root.exists():
            return []
        return [self.inspect(path.name) for path in sorted(self.root.iterdir()) if (path / ".git").is_dir()]

    def clone(self, url: str) -> dict:
        clean_url, name = self._github_url(url)
        path = self._repo(name)
        if path.exists():
            raise RepositoryWorkerError(f"Managed repository already exists: {name}")
        self.root.mkdir(parents=True, exist_ok=True)
        self._run(["git", "clone", clean_url, str(path)], timeout=900)
        return self.inspect(name)

    def inspect(self, name: str) -> dict:
        path = self._repo(name)
        if not (path / ".git").is_dir():
            raise RepositoryWorkerError(f"Unknown managed repository: {name}")
        branch = self._run(["git", "branch", "--show-current"], cwd=path).stdout.strip()
        status = self._run(["git", "status", "--short"], cwd=path).stdout.splitlines()
        remote = self._run(["git", "remote", "get-url", "origin"], cwd=path).stdout.strip()
        return {"name": name, "path": str(path), "branch": branch, "clean": not status,
                "changes": status[:100], "remote": remote}

    def implement(self, name: str, task: str) -> dict:
        path = self._repo(name)
        if not (path / ".git").is_dir():
            raise RepositoryWorkerError(f"Unknown managed repository: {name}")
        if not task.strip():
            raise RepositoryWorkerError("Implementation request is empty.")
        if self._run(["git", "status", "--porcelain"], cwd=path).stdout.strip():
            raise RepositoryWorkerError("Repository already has changes; review or commit them before another implementation.")
        exe = shutil.which("codex") or shutil.which("codex.exe")
        if not exe:
            raise RepositoryWorkerError("Codex CLI is unavailable.")
        with tempfile.NamedTemporaryFile(prefix="draeven-repo-", suffix=".txt", delete=False) as handle:
            output = Path(handle.name)
        prompt = (
            "Implement the requested change in this repository. Read its instructions, keep the scope narrow, "
            "run appropriate existing tests, and leave all changes uncommitted for human review. "
            "Never display or add credentials.\n\nRequest: " + task.strip()
        )
        try:
            self._run([exe, "exec", "--ephemeral", "--skip-git-repo-check", "--sandbox", "workspace-write",
                       "--cd", str(path), "--output-last-message", str(output), prompt], cwd=path, timeout=1200)
            summary = output.read_text(encoding="utf-8", errors="replace").strip()
        finally:
            output.unlink(missing_ok=True)
        result = self.inspect(name)
        result["summary"] = summary
        result["diff_stat"] = self._run(["git", "diff", "--stat"], cwd=path).stdout.strip()
        return result

    def publish(self, name: str, message: str) -> dict:
        path = self._repo(name)
        if not message.strip():
            raise RepositoryWorkerError("Commit message is empty.")
        tracked = self._run(["git", "status", "--porcelain"], cwd=path).stdout
        if not tracked.strip():
            raise RepositoryWorkerError("There are no changes to publish.")
        for candidate in path.rglob("*"):
            if not candidate.is_file() or ".git" in candidate.parts:
                continue
            if candidate.name == ".env" or candidate.suffix.lower() in {".key", ".pem"}:
                raise RepositoryWorkerError(f"Private credential file blocks publish: {candidate.name}")
            if candidate.stat().st_size <= 2_000_000 and candidate.suffix.lower() not in {".png", ".jpg", ".ico"}:
                try:
                    if SECRET_RE.search(candidate.read_text(encoding="utf-8")):
                        raise RepositoryWorkerError(f"Possible credential blocks publish: {candidate.name}")
                except UnicodeDecodeError:
                    pass
        self._run(["git", "add", "-A"], cwd=path)
        self._run(["git", "commit", "-m", message.strip()], cwd=path)
        self._run(["git", "push"], cwd=path, timeout=900)
        return self.inspect(name)


def parse_repository_request(text: str) -> dict | None:
    raw = text.strip()
    low = raw.lower()
    if low in {"repository list", "repo list", "list repositories", "list repos"}:
        return {"action": "list"}
    match = re.match(r"^(?:repository|repo)\s+(?:add|clone)\s+(https://github\.com/\S+)$", raw, re.I)
    if match:
        return {"action": "clone", "url": match.group(1).rstrip(".,)")}
    match = re.match(r"^(?:repository|repo)\s+(?:inspect|status)\s+([A-Za-z0-9._-]+)$", raw, re.I)
    if match:
        return {"action": "inspect", "name": match.group(1)}
    match = re.match(r"^(?:repository|repo)\s+implement\s+([A-Za-z0-9._-]+)\s*:\s*(.+)$", raw, re.I | re.S)
    if match:
        return {"action": "implement", "name": match.group(1), "task": match.group(2).strip()}
    match = re.match(r"^(?:repository|repo)\s+publish\s+([A-Za-z0-9._-]+)\s*:\s*(.+)$", raw, re.I | re.S)
    if match:
        return {"action": "publish", "name": match.group(1), "message": match.group(2).strip()}
    return None


def format_result(result) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False)
