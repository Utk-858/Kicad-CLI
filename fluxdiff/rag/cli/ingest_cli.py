# fluxdiff/rag/cli/ingest_cli.py

from fluxdiff.rag.ingest.git_loader import GitLoader
from fluxdiff.rag.ingest.diff_generator import DiffGenerator
from fluxdiff.rag.ingest.document_builder import DocumentBuilder
from fluxdiff.rag.embedding.embedder import Embedder
from fluxdiff.rag.embedding.vector_store import VectorStore
from fluxdiff.rag.schemas import RAGDocument

import os


def run_ingestion():
    print("🚀 Starting ingestion pipeline...")

    loader = GitLoader()
    diff_gen = DiffGenerator()
    builder = DocumentBuilder()
    embedder = Embedder()
    store = VectorStore()

    # -----------------------------
    # STEP 1: Get PCB files
    # -----------------------------
    pcb_files = loader.find_pcb_files()

    if not pcb_files:
        print("❌ No .kicad_pcb files found")
        return

    pcb_file = pcb_files[0]  # MVP: pick first
    print(f"📦 Using PCB file: {pcb_file}")

    # -----------------------------
    # STEP 2: Get commits
    # -----------------------------
    commits = loader.get_commits(10)

    if len(commits) < 2:
        print("❌ Not enough commits")
        return

    all_docs = []

    # -----------------------------
    # STEP 3: Loop through commits
    # -----------------------------
    for i in range(len(commits) - 1):
        c_old = commits[i + 1]
        c_new = commits[i]

        print(f"🔍 Processing {c_old.commit_hash} → {c_new.commit_hash}")

        # -------------------------
        # STEP 3A: Generate diff
        # -------------------------
        diff = diff_gen.generate_diff(
            c_old.commit_hash,
            c_new.commit_hash,
            pcb_file
        )

        # -------------------------
        # STEP 3B: Build documents
        # -------------------------
        docs = builder.build_documents(c_new, diff, pcb_file)

        all_docs.extend(docs)

    # -----------------------------
    # STEP 4: Add repo files (IMPORTANT)
    # -----------------------------
    print("📂 Loading repo files...")

    for root, _, files in os.walk(loader.repo_path):
        for file in files:
            if file.endswith((".md", ".txt", ".py", ".json")):
                full_path = os.path.join(root, file)

                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    doc = RAGDocument(
                        content=f"File: {full_path}\n\n{content}",
                        metadata={
                            "type": "repo_file",
                            "file": full_path
                        }
                    )

                    all_docs.append(doc)

                except:
                    pass

    print(f"📊 Total documents: {len(all_docs)}")

    if not all_docs:
        print("❌ No documents generated")
        return

    # -----------------------------
    # STEP 5: Embed
    # -----------------------------
    print("🧠 Generating embeddings...")
    embeddings = embedder.embed_documents(all_docs)

    # -----------------------------
    # STEP 6: Store
    # -----------------------------
    print("💾 Storing in vector DB...")
    store.add_documents(all_docs, embeddings)

    print("✅ Ingestion complete!")

if __name__ == "__main__":
    run_ingestion()