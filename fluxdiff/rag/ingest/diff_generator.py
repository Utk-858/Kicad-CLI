# fluxdiff/rag/ingest/diff_generator.py

import os
import tempfile
import subprocess
from typing import Optional

from fluxdiff.rag.config import RAG_CONFIG
from fluxdiff.rag.schemas import DiffSummary


class DiffGenerator:
    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path or RAG_CONFIG["repo_path"]

    # -----------------------------
    # Get file content from commit
    # -----------------------------
    def _get_file_at_commit(self, commit_hash: str, file_path: str) -> Optional[str]:
        try:
            result = subprocess.check_output(
                ["git", "show", f"{commit_hash}:{file_path}"],
                cwd=self.repo_path,
                stderr=subprocess.STDOUT
            )
            return result.decode("utf-8")
        except subprocess.CalledProcessError:
            return None

    # -----------------------------
    # Write content to temp file
    # -----------------------------
    def _write_temp_file(self, content: str) -> str:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".kicad_pcb")
        tmp.write(content.encode("utf-8"))
        tmp.close()
        return tmp.name

    # -----------------------------
    # Run FluxDiff (CLI-based)
    # -----------------------------
    def _run_fluxdiff(self, before_file: str, after_file: str) -> str:
        try:
            result = subprocess.check_output(
                [
                    "python",
                    "-m",
                    "fluxdiff.cli.main",
                    before_file,
                    after_file
                ],
                stderr=subprocess.STDOUT
            )
            return result.decode("utf-8")
        except subprocess.CalledProcessError as e:
            print("FluxDiff failed:", e.output.decode())
            return ""

    # -----------------------------
    # Parse diff_report.txt → DiffSummary
    # -----------------------------
    def _parse_diff_report(self, report_path: str) -> DiffSummary:
        summary = DiffSummary()

        if not os.path.exists(report_path):
            return summary

        with open(report_path, "r") as f:
            lines = f.readlines()

        section = None

        for line in lines:
            line = line.strip()

            if "COMPONENT CHANGES" in line:
                section = "component"
                continue
            elif "NET CHANGES" in line:
                section = "net"
                continue
            elif "ROUTING CHANGES" in line:
                section = "routing"
                continue

            if not line or line.startswith("="):
                continue

            if section == "component":
                summary.component_changes.append(line)
            elif section == "net":
                summary.net_changes.append(line)
            elif section == "routing":
                summary.routing_changes.append(line)

        return summary

    # -----------------------------
    # MAIN FUNCTION
    # -----------------------------
    def generate_diff(
        self,
        commit_a: str,
        commit_b: str,
        pcb_file_path: str
    ) -> DiffSummary:
        """
        Generate diff between two commits for a specific PCB file.
        """

        # 1. Get file contents
        before_content = self._get_file_at_commit(commit_a, pcb_file_path)
        after_content = self._get_file_at_commit(commit_b, pcb_file_path)

        if not before_content or not after_content:
            print("PCB file not found in one of the commits")
            return DiffSummary()

        # 2. Write to temp files
        before_file = self._write_temp_file(before_content)
        after_file = self._write_temp_file(after_content)

        # 3. Run FluxDiff
        self._run_fluxdiff(before_file, after_file)

        # 4. Parse output
        report_path = os.path.join("output", "diff_report.txt")
        summary = self._parse_diff_report(report_path)

        # 5. Cleanup temp files
        try:
            os.remove(before_file)
            os.remove(after_file)
        except Exception:
            pass

        return summary