# fluxdiff/rag/ingest/git_loader.py

import subprocess
from typing import List
from fluxdiff.rag.config import RAG_CONFIG
from fluxdiff.rag.schemas import CommitInfo


class GitLoader:
    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path or RAG_CONFIG["repo_path"]

    # -----------------------------
    # Internal helper to run git commands
    # -----------------------------
    def _run_git_command(self, command: List[str]) -> str:
        try:
            result = subprocess.check_output(
                command,
                cwd=self.repo_path,
                stderr=subprocess.STDOUT
            )
            return result.decode("utf-8").strip()
        except subprocess.CalledProcessError as e:
            print("Git command failed:", e.output.decode())
            return ""

    # -----------------------------
    # Get commit list
    # -----------------------------
    def get_commits(self, max_count: int = 20) -> List[CommitInfo]:
        """
        Returns recent commits.
        """
        command = [
            "git",
            "log",
            f"--max-count={max_count}",
            "--pretty=format:%H|%s|%an|%ad"
        ]

        output = self._run_git_command(command)
        commits = []

        if not output:
            return commits

        for line in output.split("\n"):
            parts = line.split("|")
            if len(parts) < 4:
                continue

            commit = CommitInfo(
                commit_hash=parts[0],
                message=parts[1],
                author=parts[2],
                date=parts[3]
            )
            commits.append(commit)

        return commits

    # -----------------------------
    # Get files changed in commit
    # -----------------------------
    def get_changed_files(self, commit_hash: str) -> List[str]:
        command = [
            "git",
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            commit_hash
        ]

        output = self._run_git_command(command)
        if not output:
            return []

        return output.split("\n")

    # -----------------------------
    # Get diff between two commits
    # -----------------------------
    def get_diff_between_commits(self, commit_a: str, commit_b: str) -> str:
        command = [
            "git",
            "diff",
            commit_a,
            commit_b
        ]

        return self._run_git_command(command)

    # -----------------------------
    # Checkout specific commit
    # -----------------------------
    def checkout_commit(self, commit_hash: str):
        command = ["git", "checkout", commit_hash]
        self._run_git_command(command)

    # -----------------------------
    # Checkout back to main (important!)
    # -----------------------------
    def checkout_main(self, branch: str = "main"):
        command = ["git", "checkout", branch]
        self._run_git_command(command)

        # -----------------------------
    # Find all PCB files in repo
    # -----------------------------
    def find_pcb_files(self) -> list:
        """
        Returns all .kicad_pcb files tracked in git.
        """
        command = [
            "git",
            "ls-files",
            "*.kicad_pcb"
        ]

        output = self._run_git_command(command)

        if not output:
            return []

        return output.split("\n")