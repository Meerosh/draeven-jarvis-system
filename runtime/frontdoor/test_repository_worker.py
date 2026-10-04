from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from repository_worker import RepositoryWorker, RepositoryWorkerError, parse_repository_request
import server


class RepositoryWorkerTests(unittest.TestCase):
    def test_parser_recognizes_safe_repository_commands(self):
        self.assertEqual(parse_repository_request("repo list"), {"action": "list"})
        self.assertEqual(parse_repository_request("repo inspect demo"), {"action": "inspect", "name": "demo"})
        self.assertEqual(parse_repository_request("repo implement demo: fix tests")["task"], "fix tests")

    def test_url_rejects_credentials_and_non_github_hosts(self):
        worker = RepositoryWorker(Path(tempfile.mkdtemp()))
        for url in ("https://user:token@github.com/a/b", "https://example.com/a/b"):
            with self.assertRaises(RepositoryWorkerError):
                worker._github_url(url)

    def test_repo_path_cannot_escape_managed_root(self):
        worker = RepositoryWorker(Path(tempfile.mkdtemp()))
        with self.assertRaises(RepositoryWorkerError):
            worker._repo("../outside")

    def test_clone_request_creates_confirmation_without_requiring_name(self):
        decision = {"lane": "repository"}
        with patch.object(server, "reflex", return_value=decision):
            result = server.handle("repo clone https://github.com/example/demo")
        self.assertIn("clone https://github.com/example/demo", result[1])
        self.assertIsNotNone(result[3])


if __name__ == "__main__":
    unittest.main()
