"""
TripMind AI — RAG (Retrieval-Augmented Generation) module.

Embeds travel documents with Google's text-embedding-004 model and stores
them in a local ChromaDB collection. At query time, the most relevant
chunks are retrieved to ground the LLM itinerary generation.

**Mock-aware**: When ChromaDB or Google Generative AI is not available
(missing packages or empty/placeholder API key), the module automatically
falls back to deterministic hash-based embeddings and simple in-memory
keyword matching. No configuration required — detection is automatic.
"""

import hashlib
import os
import logging
from functools import lru_cache

logger = logging.getLogger('agent')

# ---------------------------------------------------------------------------
# Mock-mode detection
# ---------------------------------------------------------------------------
MOCK_MODE = False

_PLACEHOLDER_KEYS = {'', 'your-api-key-here', 'CHANGE_ME', 'your_api_key'}

_gemini_api_key = os.environ.get('GEMINI_API_KEY', '')

try:
    import chromadb
    import google.generativeai as genai

    if not _gemini_api_key or _gemini_api_key in _PLACEHOLDER_KEYS:
        MOCK_MODE = True
        logger.warning(
            'RAG: GEMINI_API_KEY is missing or placeholder — '
            'activating MOCK mode (hash-based embeddings + in-memory store).'
        )
    else:
        MOCK_MODE = False
except ImportError as _import_err:
    MOCK_MODE = True
    logger.warning(
        f'RAG: Could not import chromadb / google.generativeai '
        f'({_import_err}) — activating MOCK mode.'
    )

# ---------------------------------------------------------------------------
# Real-mode initialisation (only when NOT mocked)
# ---------------------------------------------------------------------------
_chroma = None
_col = None

if not MOCK_MODE:
    # Safe to use the real imports here — they succeeded above
    genai.configure(api_key=_gemini_api_key)

    _chroma = chromadb.PersistentClient(
        path=os.environ.get('CHROMA_PATH', './chroma_db')
    )
    _col = _chroma.get_or_create_collection(
        name='tripmind',
        metadata={'hnsw:space': 'cosine'},
    )
    logger.info('RAG: Real mode active — using Gemini embeddings + ChromaDB.')

# ---------------------------------------------------------------------------
# Mock-mode in-memory store
# ---------------------------------------------------------------------------
_mock_docs: dict[str, dict] = {}
"""
Schema:  doc_id → {'text': str, 'destination': str, 'category': str}
Used only when MOCK_MODE is True.
"""


# ---------------------------------------------------------------------------
# Embedding helper
# ---------------------------------------------------------------------------
@lru_cache(maxsize=500)
def embed_text(text: str) -> tuple:
    """Embed *text* using Google's text-embedding-004 model.

    Returns a **tuple** (instead of list) so it can be used as a dict /
    lru_cache key.

    In mock mode, returns a deterministic 384-dimension tuple derived from
    the MD5 hash of *text* — the same input always produces the same vector.
    """
    if MOCK_MODE:
        # Deterministic 384-dim vector from hash
        h = hashlib.md5(text.encode('utf-8')).hexdigest()
        # Expand the 32-hex-char hash into 384 floats in [-1, 1]
        vector = []
        for i in range(384):
            # Cycle through the hash characters
            char = h[i % len(h)]
            # Map hex char (0-15) to float in [-1, 1]
            vector.append((int(char, 16) - 7.5) / 7.5)
        return tuple(vector)

    # Real mode — call Gemini embedding API
    result = genai.embed_content(
        model='models/text-embedding-004',
        content=text,
        task_type='retrieval_document',
    )
    return tuple(result['embedding'])


# ---------------------------------------------------------------------------
# Document CRUD
# ---------------------------------------------------------------------------
def add_travel_doc(
    doc_id: str,
    text: str,
    destination: str,
    category: str,
) -> None:
    """Add (or update) a travel document in the ChromaDB collection."""
    if MOCK_MODE:
        _mock_docs[doc_id] = {
            'text': text,
            'destination': destination,
            'category': category,
        }
        logger.debug(f'[MOCK] Stored doc {doc_id} for {destination}')
        return

    # Real mode — ChromaDB upsert
    vector = embed_text(text)
    _col.upsert(
        ids=[doc_id],
        embeddings=[list(vector)],
        documents=[text],
        metadatas=[{'destination': destination, 'category': category}],
    )
    logger.debug(f'Upserted doc {doc_id} for {destination}')


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
def retrieve_travel_context(
    query: str,
    destination: str = '',
    top_k: int = 5,
) -> str:
    """Retrieve the most relevant travel context from ChromaDB.

    Parameters
    ----------
    query : str
        Natural-language query used to find similar documents.
    destination : str, optional
        If provided, only documents tagged with this destination are
        considered.
    top_k : int
        Number of documents to retrieve (default 5).

    Returns
    -------
    str
        Newline-separated block of the top-k matching documents, or an
        empty string if nothing is found / an error occurs.
    """
    if MOCK_MODE:
        # Simple keyword matching against in-memory docs
        query_words = set(query.lower().split())
        scored: list[tuple[int, str]] = []

        for doc_id, doc in _mock_docs.items():
            # Filter by destination if specified
            if destination and doc['destination'].lower() != destination.lower():
                continue

            doc_text = doc['text'].lower()
            score = sum(1 for w in query_words if w in doc_text)
            if score > 0:
                scored.append((score, doc['text']))

        # Sort by score descending, take top_k
        scored.sort(key=lambda x: x[0], reverse=True)
        docs = [text for _, text in scored[:top_k]]
        return '\n\n'.join(docs)

    # Real mode — ChromaDB vector search
    try:
        vector = embed_text(query)
        where = {'destination': destination} if destination else None
        results = _col.query(
            query_embeddings=[list(vector)],
            n_results=top_k,
            where=where,
            include=['documents'],
        )
        docs = results.get('documents', [[]])[0]
        return '\n\n'.join(docs)
    except Exception as e:
        logger.error(f'RAG retrieval error: {e}')
        return ''
