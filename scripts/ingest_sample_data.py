"""
Ingest sample documents directly into Qdrant (no API server required).

Used by CI eval gate to seed the vector store before running evaluation.
Also useful for local development when the API server is not running.

Run: uv run python scripts/ingest_sample_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from docustra.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("ingest_sample_data")

# ---------------------------------------------------------------------------
# Synthetic sample corpus (no PDF download needed)
# These passages cover the two golden-dataset domains so that
# eval queries have at least some grounding context to retrieve.
# ---------------------------------------------------------------------------

SAMPLE_PASSAGES = [
    # ── Apple 10-K domain ───────────────────────────────────────────────────
    {
        "text": (
            "Apple Inc. designs, manufactures, and markets smartphones, personal "
            "computers, tablets, wearables, and accessories, and sells a variety of "
            "related services. The Company's fiscal year ends on the last Saturday of "
            "September. Total net sales for fiscal 2023 were $383.3 billion, compared "
            "to $394.3 billion in fiscal 2022."
        ),
        "source": "apple_10k_2023.pdf",
        "page": 1,
    },
    {
        "text": (
            "iPhone net sales were $200.6 billion in fiscal 2023, accounting for the "
            "largest share of total revenue. Mac net sales were $29.4 billion, iPad "
            "net sales were $28.3 billion, and Wearables, Home and Accessories net "
            "sales were $39.8 billion. Services net sales were $85.2 billion."
        ),
        "source": "apple_10k_2023.pdf",
        "page": 5,
    },
    {
        "text": (
            "Apple's net income for fiscal year 2023 was $96.995 billion, or $6.13 "
            "per diluted share. Research and development expenses were $29.9 billion, "
            "representing approximately 7.8% of net sales. The Americas segment "
            "generated $162.1 billion in net sales, representing the largest "
            "geographic region."
        ),
        "source": "apple_10k_2023.pdf",
        "page": 34,
    },
    {
        "text": (
            "Apple faces significant supply chain concentration risks, relying on "
            "single-source suppliers in Asia for many components. Disruptions due to "
            "geopolitical tensions, natural disasters, or pandemics could adversely "
            "impact production. The Company is also subject to cybersecurity risks "
            "including data breaches and ransomware attacks."
        ),
        "source": "apple_10k_2023.pdf",
        "page": 12,
    },
    {
        "text": (
            "Privacy and data protection regulations, including GDPR in Europe and "
            "CCPA in California, expose Apple to compliance costs and litigation risk. "
            "The Company has been subject to regulatory investigations by the European "
            "Commission regarding App Store practices. Apple disclosed stock repurchase "
            "activity of $77.6 billion in fiscal 2023."
        ),
        "source": "apple_10k_2023.pdf",
        "page": 18,
    },
    {
        "text": (
            "Apple is committed to being carbon neutral across its entire supply chain "
            "and product life cycle by 2030. The company describes the market for its "
            "products as highly competitive, with competitors including Samsung, Google, "
            "Microsoft, and Amazon. Apple is headquartered in Cupertino, California."
        ),
        "source": "apple_10k_2023.pdf",
        "page": 3,
    },
    # ── Vector databases domain ─────────────────────────────────────────────
    {
        "text": (
            "A vector database stores high-dimensional embeddings and supports "
            "approximate nearest neighbour (ANN) search. Unlike traditional relational "
            "databases that match exact values, vector databases find semantically "
            "similar items using distance metrics such as cosine similarity, dot "
            "product, or Euclidean distance."
        ),
        "source": "vector-databases-guide.pdf",
        "page": 1,
    },
    {
        "text": (
            "HNSW (Hierarchical Navigable Small World) is the most widely used ANN "
            "algorithm in vector databases. It builds a multi-layer graph where each "
            "node is connected to its nearest neighbours. Search navigates from coarse "
            "upper layers to fine lower layers, achieving sub-linear query time with "
            "high recall. Qdrant, Weaviate, and Milvus all use HNSW as their default index."
        ),
        "source": "vector-databases-guide.pdf",
        "page": 8,
    },
    {
        "text": (
            "Hybrid search combines dense vector search with sparse keyword search "
            "(BM25). BM25 excels at exact term matching for rare words and proper "
            "nouns, while dense search captures semantic similarity. Reciprocal Rank "
            "Fusion (RRF) is the standard algorithm for merging the two ranked lists: "
            "score = sum(weight / (k + rank)) where k=60 is a smoothing constant."
        ),
        "source": "vector-databases-guide.pdf",
        "page": 15,
    },
    {
        "text": (
            "Re-ranking in RAG pipelines uses a cross-encoder model to score "
            "(query, document) pairs jointly. Unlike bi-encoders that embed query and "
            "document independently, cross-encoders attend over both simultaneously, "
            "producing more accurate relevance scores at the cost of higher latency. "
            "A typical pipeline: fast bi-encoder retrieval → precise cross-encoder reranking."
        ),
        "source": "vector-databases-guide.pdf",
        "page": 22,
    },
    {
        "text": (
            "Product quantization (PQ) compresses high-dimensional vectors by dividing "
            "them into sub-vectors and quantising each sub-space independently. This "
            "reduces memory usage by 4-32x with a small accuracy trade-off. IVF "
            "(Inverted File Index) partitions the vector space into clusters; queries "
            "only search the nearest clusters, reducing computation."
        ),
        "source": "vector-databases-guide.pdf",
        "page": 30,
    },
    {
        "text": (
            "Chunking is the process of splitting documents into smaller passages "
            "before embedding. The 500-800 token range is the empirical sweet spot: "
            "too small loses context, too large dilutes relevance. Chunk overlap "
            "(typically 10-15% of chunk size) prevents information loss at boundaries. "
            "Semantic chunking splits on topic changes rather than fixed sizes."
        ),
        "source": "vector-databases-guide.pdf",
        "page": 45,
    },
    {
        "text": (
            "Metadata filtering allows vector search to apply structured predicates "
            "alongside similarity search, for example filtering by date, category, or "
            "document source before running ANN. Maximum Marginal Relevance (MMR) "
            "balances relevance and diversity in retrieval results to reduce redundant "
            "chunks. Cosine similarity is preferred when vector magnitude is not meaningful."
        ),
        "source": "vector-databases-guide.pdf",
        "page": 52,
    },
    {
        "text": (
            "Sparse vector representations such as BM25 and SPLADE encode documents "
            "as high-dimensional sparse vectors where each dimension corresponds to a "
            "vocabulary token. Dense representations use low-dimensional continuous "
            "embeddings from transformer models. Bi-encoders produce dense embeddings "
            "independently for query and document; cross-encoders process both jointly."
        ),
        "source": "vector-databases-guide.pdf",
        "page": 60,
    },
    {
        "text": (
            "Semantic search retrieves documents by meaning rather than exact keyword "
            "match. A query like 'heart attack' finds documents about 'myocardial "
            "infarction' because their embeddings are close in vector space. Vector "
            "dimensionality affects both accuracy and storage: 384-dim models like "
            "all-MiniLM-L6-v2 are fast; 1536-dim models like text-embedding-3-large "
            "are more accurate but slower."
        ),
        "source": "vector-databases-guide.pdf",
        "page": 70,
    },
]


def ingest_directly() -> int:
    """Ingest sample passages directly via the storage layer (no API server needed)."""
    from langchain_core.documents import Document

    from docustra.ingestion.embedder import get_embeddings
    from docustra.storage.vector_store import VectorStore

    embeddings = get_embeddings()
    store = VectorStore(embeddings)

    docs = [
        Document(
            page_content=p["text"],
            metadata={"source": p["source"], "page": p["page"], "type": "text"},
        )
        for p in SAMPLE_PASSAGES
    ]

    ids = store.add_documents(docs)
    logger.info("Sample ingestion complete", chunks=len(ids))
    print(f"✅ Ingested {len(ids)} sample passages into Qdrant")
    return len(ids)


if __name__ == "__main__":
    try:
        count = ingest_directly()
        sys.exit(0 if count > 0 else 1)
    except Exception as e:
        logger.error("Ingestion failed", error=str(e))
        print(f"❌ Ingestion failed: {e}")
        sys.exit(1)
