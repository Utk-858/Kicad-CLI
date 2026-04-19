# fluxdiff/rag/ingest/document_builder.py

from typing import List
from fluxdiff.rag.schemas import (
    RAGDocument,
    CommitInfo,
    DiffSummary
)


class DocumentBuilder:

    # -----------------------------
    # Build all documents for a commit
    # -----------------------------
    def build_documents(
        self,
        commit: CommitInfo,
        diff: DiffSummary,
        file_path: str
    ) -> List[RAGDocument]:

        documents = []

        # 1. Commit Summary Document
        summary_doc = self._build_commit_summary(commit, diff, file_path)
        documents.append(summary_doc)

        # 2. Component Changes
        if diff.component_changes:
            documents.append(
                self._build_component_doc(commit, diff, file_path)
            )

        # 3. Net Changes
        if diff.net_changes:
            documents.append(
                self._build_net_doc(commit, diff, file_path)
            )

        # 4. Routing Changes
        if diff.routing_changes:
            documents.append(
                self._build_routing_doc(commit, diff, file_path)
            )

        return documents

    # -----------------------------
    # Commit Summary
    # -----------------------------
    def _build_commit_summary(
        self,
        commit: CommitInfo,
        diff: DiffSummary,
        file_path: str
    ) -> RAGDocument:

        content = f"""
Commit: {commit.commit_hash}
Message: {commit.message}
Author: {commit.author}
Date: {commit.date}

File: {file_path}

Summary:
- Component changes: {len(diff.component_changes)}
- Net changes: {len(diff.net_changes)}
- Routing changes: {len(diff.routing_changes)}
"""

        metadata = {
            "commit": commit.commit_hash,
            "type": "summary",
            "file": file_path
        }

        return RAGDocument(content=content.strip(), metadata=metadata)

    # -----------------------------
    # Component Changes
    # -----------------------------
    def _build_component_doc(
        self,
        commit: CommitInfo,
        diff: DiffSummary,
        file_path: str
    ) -> RAGDocument:

        changes_text = "\n".join(diff.component_changes)

        content = f"""
Commit: {commit.commit_hash}
Type: Component Changes

File: {file_path}

Changes:
{changes_text}
"""

        metadata = {
            "commit": commit.commit_hash,
            "type": "component",
            "file": file_path
        }

        return RAGDocument(content=content.strip(), metadata=metadata)

    # -----------------------------
    # Net Changes
    # -----------------------------
    def _build_net_doc(
        self,
        commit: CommitInfo,
        diff: DiffSummary,
        file_path: str
    ) -> RAGDocument:

        changes_text = "\n".join(diff.net_changes)

        content = f"""
Commit: {commit.commit_hash}
Type: Net Changes

File: {file_path}

Changes:
{changes_text}
"""

        metadata = {
            "commit": commit.commit_hash,
            "type": "net",
            "file": file_path
        }

        return RAGDocument(content=content.strip(), metadata=metadata)

    # -----------------------------
    # Routing Changes
    # -----------------------------
    def _build_routing_doc(
        self,
        commit: CommitInfo,
        diff: DiffSummary,
        file_path: str
    ) -> RAGDocument:

        changes_text = "\n".join(diff.routing_changes)

        content = f"""
Commit: {commit.commit_hash}
Type: Routing Changes

File: {file_path}

Changes:
{changes_text}
"""

        metadata = {
            "commit": commit.commit_hash,
            "type": "routing",
            "file": file_path
        }

        return RAGDocument(content=content.strip(), metadata=metadata)