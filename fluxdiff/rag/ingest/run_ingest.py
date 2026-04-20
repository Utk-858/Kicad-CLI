# fluxdiff/rag/ingest/run_ingest.py

import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from fluxdiff.rag.ingest.git_loader import GitLoader
from fluxdiff.rag.ingest.diff_generator import DiffGenerator
from fluxdiff.rag.ingest.document_builder import DocumentBuilder
from fluxdiff.rag.embedding.embedder import Embedder
from fluxdiff.rag.embedding.vector_store import VectorStore
from fluxdiff.rag.config import RAG_CONFIG

def main():
    repo_path = RAG_CONFIG["repo_path"]
    print(f"🚀 Starting ingestion for: {repo_path}")

    # 1. Load Commits
    loader = GitLoader(repo_path)
    commits = loader.get_commits(max_count=20) # Change limit as needed
    print(f"Found {len(commits)} commits to process.")

    # 2. Setup Modules
    diff_gen = DiffGenerator(repo_path)
    doc_builder = DocumentBuilder()
    embedder = Embedder()
    store = VectorStore()

    all_docs = []

    # 3. Process each commit
    # For this simple ingestor, we'll look for .kicad_pcb files in the repo
    # In a real scenario, you might want to specify which file to track
    pcb_files = []
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".kicad_pcb"):
                rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                pcb_files.append(rel_path)
    
    if not pcb_files:
        print("❌ No .kicad_pcb files found in the repository!")
        return

    print(f"Tracking files: {pcb_files}")

    for i in range(len(commits) - 1):
        # Compare commit[i+1] (before) with commit[i] (after)
        after_commit = commits[i]
        before_commit = commits[i+1]

        print(f"[{i+1}/{len(commits)-1}] Diffing: {before_commit.commit_hash[:7]} -> {after_commit.commit_hash[:7]}")

        for pcb_file in pcb_files:
            summary = diff_gen.generate_diff(
                before_commit.commit_hash, 
                after_commit.commit_hash, 
                pcb_file
            )

            # Generate RAG documents
            docs = doc_builder.build_documents(after_commit, summary, pcb_file)
            all_docs.extend(docs)

    if not all_docs:
        print("⚠️ No changes found to index.")
        return

    # 4. Embed and Store
    print(f"✨ Generating embeddings for {len(all_docs)} documents...")
    embeddings = embedder.embed_documents(all_docs)
    
    print("💾 Saving to vector database (rag_db/)...")
    store.add_documents(all_docs, embeddings)

    print("✅ Ingestion complete! faiss.index and documents.pkl have been created.")

if __name__ == "__main__":
    main()
