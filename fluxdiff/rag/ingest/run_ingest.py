# fluxdiff/rag/ingest/run_ingest.py

import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from fluxdiff.rag.ingest.git_loader import GitLoader
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
        # Skip hidden folders and common noise
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'node_modules', '__pycache__', 'rag_db']]
        
        level = root.replace(repo_path, '').count(os.sep)
        indent = '  ' * level
        structure.append(f"{indent}{os.path.basename(root) or './'}/")
        
        sub_indent = '  ' * (level + 1)
        for f in files:
            if not f.startswith('.') and not f.endswith(('.index', '.pkl', '.bin')):
                structure.append(f"{sub_indent}{f}")

    content = "PROJECT FOLDER STRUCTURE:\n\n" + "\n".join(structure)
    
    return RAGDocument(
        content=content,
        metadata={
            "type": "project_structure",
            "source": "filesystem_scan",
            "filename": "root"
        }
    )

def main():
    repo_path = RAG_CONFIG["repo_path"]
    print(f"🚀 Starting Deep Ingestion for: {repo_path}")

    if not os.path.exists(repo_path):
        print(f"❌ Error: Repo path {repo_path} does not exist!")
        return

    # 1. Setup Modules
    builder = DocumentBuilder()
    embedder = Embedder()
    vector_store = VectorStore()
    all_documents = []

    # 2. Layer 1: Project Map (Hierarchy)
    print("📂 Mapping project structure...")
    all_documents.append(generate_project_map(repo_path))

    # 3. Layer 2: File Snapshots (Real Content with Chunking)
    print("📄 Scanning file contents (READMEs, KiCad files, BOMs)...")
    targets = (".kicad_pcb", ".kicad_sch", ".kicad_pro", ".kicad_dru", ".csv", ".txt", ".md")
    
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'node_modules', 'rag_db', '.gemini']]
        
        for f in files:
            if not f.lower().endswith(targets):
                continue
                
            path = os.path.join(root, f)
            rel_path = os.path.relpath(path, repo_path)
            
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                    if not content.strip():
                        continue
                        
                    # CHUNKING: Split large files (like PCBs) into manageable chunks
                    if len(content) > 10000:
                        file_chunks = chunk_text(content)
                        for i, chunk in enumerate(file_chunks):
                            chunk_doc = builder.build_snapshot_document(rel_path, chunk)
                            chunk_doc.metadata["chunk"] = i
                            all_documents.append(chunk_doc)
                    else:
                        all_documents.append(builder.build_snapshot_document(rel_path, content))
            except Exception as e:
                print(f"  ⚠️ Could not read {rel_path}: {e}")

    # 4. Layer 3: Git History
    loader = GitLoader(repo_path)
    try:
        print("🔨 Processing git history...")
        commits = loader.get_commits(max_count=50)
        for commit in commits:
            # Manually build a doc since we use CommitInfo schema
            commit_content = f"Commit: {commit.commit_hash}\nMessage: {commit.message}\nAuthor: {commit.author}\nDate: {commit.date}"
            all_documents.append(RAGDocument(
                content=commit_content,
                metadata={"type": "commit_summary", "commit": commit.commit_hash}
            ))
    except Exception as e:
        print(f"  ⚠️ Git error: {e}")

    # 5. Embed and Index
    if all_documents:
        # We might have MANY chunks now, so we'll process in small batches for OpenAI
        print(f"✨ Generating embeddings for {len(all_documents)} chunks...")
        try:
            batch_size = 50
            for i in range(0, len(all_documents), batch_size):
                batch = all_documents[i:i+batch_size]
                print(f"  - Batch {i//batch_size + 1}/{len(all_documents)//batch_size + 1}...")
                embeddings = embedder.embed_documents(batch)
                vector_store.add_documents(batch, embeddings)
            
            vector_store.save()
            print("✅ Deep Ingestion complete! Every detail is now searchable.")
        except Exception as e:
            print(f"❌ Embedding Error: {e}")
    else:
        print("⚠️ No documents were generated.")

if __name__ == "__main__":
    main()
