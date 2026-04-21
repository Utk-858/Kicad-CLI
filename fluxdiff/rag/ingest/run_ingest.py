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
from fluxdiff.rag.schemas import RAGDocument

def chunk_text(text: str, chunk_size: int = 8000, overlap: int = 500):
    """
    Split large text into smaller chunks for LLM safety.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def generate_project_map(repo_path: str):
    """
    Creates a text-based map of the repository's folder structure.
    """
    structure = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'node_modules', '__pycache__', 'rag_db', '.gemini']]
        level = root.replace(repo_path, '').count(os.sep)
        indent = '  ' * level
        structure.append(f"{indent}{os.path.basename(root) or './'}/")
        
        sub_indent = '  ' * (level + 1)
        for f in files:
            if not f.startswith('.') and not f.endswith(('.index', '.pkl', '.bin')):
                structure.append(f"{sub_indent}{f}")

    content = "PROJECT FOLDER STRUCTURE:\n\n" + "\n".join(structure)
    return RAGDocument(content=content, metadata={"type": "project_structure", "source": "filesystem_scan", "filename": "root"})

def main():
    repo_path = RAG_CONFIG["repo_path"]
    print(f"🚀 Starting Deep Semantic Ingestion for: {repo_path}")

    if not os.path.exists(repo_path):
        print(f"❌ Error: Repo path {repo_path} does not exist!")
        return

    # 1. Setup Modules
    loader = GitLoader(repo_path)
    diff_gen = DiffGenerator(repo_path)
    builder = DocumentBuilder()
    embedder = Embedder()
    vector_store = VectorStore()
    all_documents = []

    # 2. Layer 1: Project Map
    print("📂 Mapping project structure...")
    all_documents.append(generate_project_map(repo_path))

    # 3. Layer 2: File Snapshots (Real Content)
    print("📄 Scanning active file contents...")
    targets = (".kicad_pcb", ".kicad_sch", ".kicad_pro", ".kicad_dru", ".csv", ".txt", ".md")
    
    pcb_files = [] # Keep track for diffing later
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'node_modules', 'rag_db', '.gemini']]
        for f in files:
            if not f.lower().endswith(targets): continue
            path = os.path.join(root, f)
            rel_path = os.path.relpath(path, repo_path)
            if f.endswith(".kicad_pcb"): pcb_files.append(rel_path)
            
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                    if not content.strip(): continue
                    if len(content) > 10000:
                        for i, chk in enumerate(chunk_text(content)):
                            d = builder.build_snapshot_document(rel_path, chk); d.metadata["chunk"] = i
                            all_documents.append(d)
                    else:
                        all_documents.append(builder.build_snapshot_document(rel_path, content))
            except Exception as e: print(f"  ⚠️ Could not read {rel_path}: {e}")

    # 4. Layer 3: Semantic History (Technical Diffs)
    print("🔨 Analyzing technical history for PCB files...")
    try:
        commits = loader.get_commits(max_count=15) # Deep diffs are expensive, stick to recent 15
        for i in range(len(commits) - 1):
            after = commits[i]
            before = commits[i+1]
            print(f"  [{i+1}/{len(commits)-1}] Diffing: {before.commit_hash[:7]} -> {after.commit_hash[:7]}")
            
            # Store the commit summary itself
            all_documents.append(RAGDocument(
                content=f"Commit: {after.commit_hash}\nMessage: {after.message}\nAuthor: {after.author}\nDate: {after.date}",
                metadata={"type": "commit_summary", "commit": after.commit_hash}
            ))

            # Generate technical diffs for each PCB file
            for pcb_file in pcb_files:
                try:
                    summary = diff_gen.generate_diff(before.commit_hash, after.commit_hash, pcb_file)
                    # build_documents generates component/net/routing docs
                    diff_docs = builder.build_documents(after, summary, pcb_file)
                    all_documents.extend(diff_docs)
                except Exception as e:
                    print(f"    ⚠️ Diff failed for {pcb_file}: {e}")
    except Exception as e:
        print(f"  ⚠️ Git history error: {e}")

    # 5. Embed and Index
    if all_documents:
        print(f"✨ Generating embeddings for {len(all_documents)} technical chunks...")
        try:
            batch_size = 30 # Smaller batches for deep ingestion
            for i in range(0, len(all_documents), batch_size):
                batch = all_documents[i:i+batch_size]
                print(f"  - Batch {i//batch_size + 1}/{len(all_documents)//batch_size + 1}...")
                embeddings = embedder.embed_documents(batch)
                vector_store.add_documents(batch, embeddings)
            vector_store.save()
            print("✅ Semantic Ingestion complete! The AI can now explain technical changes.")
        except Exception as e: print(f"❌ Embedding Error: {e}")
    else: print("⚠️ No documents were generated.")

if __name__ == "__main__":
    main()
