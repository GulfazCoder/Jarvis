import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime

def get_base_dir() -> Path:
    import sys
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
VECTOR_DB_PATH = BASE_DIR / "memory" / "vector_db"

class VectorMemoryManager:
    """
    Advanced Memory Manager using a Vector Database for RAG (Retrieval-Augmented Generation).
    Allows indexing of documents, chat history, and complex personal facts.
    """
    def __init__(self):
        # Use a local persistent client
        self.client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))

        # Use a lightweight local embedding function (Sentence Transformers)
        # This avoids calling the API for every single embedding request
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        # Create or get the main memory collection
        self.collection = self.client.get_or_create_collection(
            name="jarvis_long_term_memory",
            embedding_function=self.embedding_fn
        )

    def add_text(self, text: str, metadata: Dict[str, Any] = None) -> str:
        """Adds a piece of text to the vector memory."""
        if not text or not text.strip():
            return "Empty text, nothing to save."

        # Generate a unique ID based on timestamp
        doc_id = f"doc_{int(datetime.now().timestamp() * 1000)}"

        # Default metadata
        meta = {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "user_interaction"
        }
        if metadata:
            meta.update(metadata)

        self.collection.add(
            documents=[text],
            metadatas=[meta],
            ids=[doc_id]
        )
        return doc_id

    def query(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Retrieves the most relevant snippets from memory."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )

        # Format results for the prompt
        formatted_results = []
        if results['documents']:
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                formatted_results.append({
                    "content": doc,
                    "metadata": meta
                })

        return formatted_results

    def index_file(self, file_path: Path) -> bool:
        """Reads a file and indexes its content in chunks."""
        try:
            if not file_path.exists():
                return False

            # Simple chunking strategy: Split by double newline or length
            content = file_path.read_text(encoding="utf-8")
            chunks = self._chunk_text(content)

            for i, chunk in enumerate(chunks):
                self.add_text(
                    chunk,
                    metadata={"source": str(file_path), "chunk": i}
                )
            return True
        except Exception as e:
            print(f"[VectorMemory] ⚠️ Error indexing file {file_path}: {e}")
            return False

    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Splits text into manageable chunks for better retrieval precision."""
        chunks = []
        # Try to split by paragraphs first
        paragraphs = text.split("\n\n")
        for p in paragraphs:
            if len(p) <= chunk_size:
                chunks.append(p)
            else:
                # Further split long paragraphs
                for i in range(0, len(p), chunk_size):
                    chunks.append(p[i:i + chunk_size])
        return chunks

# Singleton instance
vector_memory = VectorMemoryManager()
