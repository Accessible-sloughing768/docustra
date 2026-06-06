# Parent-Child Chunker

**Strategy ID:** `parent_child` | **LLM Required:** No

## What It Does

Implements a **two-level chunking hierarchy** that optimises retrieval precision while preserving rich context for the LLM:

- **Child chunks** (small, ~256 chars): indexed as vectors in Qdrant for precise similarity search
- **Parent chunks** (large, ~1024 chars): stored in child metadata, returned to the LLM as context

The key insight: **search with small, retrieve large**.

---

## The Problem It Solves

**Standard chunking dilemma:**

```
Large chunks (1024 chars):
  + LLM gets enough context to answer well
  - Vector is a blend of many topics → imprecise retrieval
  - Query about one specific fact returns a chunk mixing 5 topics

Small chunks (256 chars):
  + Precise retrieval — exactly the relevant sentence
  - LLM gets only 1-2 sentences → not enough context to answer

Parent-Child: best of both worlds
  Child (256 chars) → precise vector retrieval
  Parent (1024 chars) → rich LLM context
```

---

## How It Works

```
Document section (2000 chars):
┌─────────────────────────────────────────────────────┐
│           PARENT CHUNK P1 (1024 chars)               │
│                                                     │
│  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │  Child C1 (256) │  │  Child C2 (256)         │  │
│  │  "HNSW builds   │  │  "Each layer in HNSW    │  │
│  │   a graph..."   │  │   connects to fewer..." │  │
│  └─────────────────┘  └─────────────────────────┘  │
│                                                     │
│  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │  Child C3 (256) │  │  Child C4 (220)         │  │
│  │  "Search starts │  │  "This layered approach  │  │
│  │   at top layer" │  │   enables logarithmic..." │  │
│  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────┘

Qdrant stores: 4 child vectors (C1, C2, C3, C4)
Each child metadata contains: parent_content = full P1 text (1024 chars)

Query: "How does HNSW graph search work?"
  → Vector similarity finds C3: "Search starts at top layer" (0.87 score)
  → LLM receives: C3.metadata["parent_content"] = full P1 (1024 chars)
  → Answer covers the full HNSW explanation, not just one sentence
```

---

## Configuration

```json
{
  "chunking_strategy": "parent_child",
  "chunking_params": {
    "parent_chunk_size": 1024,
    "child_chunk_size": 256,
    "chunk_overlap": 32
  }
}
```

**Tuning guidelines:**

| Document type | parent_chunk_size | child_chunk_size |
|---|---|---|
| Technical docs, APIs | 1024 | 256 |
| Legal/regulatory | 2048 | 512 |
| News articles | 512 | 128 |
| Dense research papers | 1536 | 384 |

**Rule of thumb:** parent should be 4× the child size.

---

## Metadata Produced

```python
# Child chunk stored in Qdrant:
{
  "source": "vector-databases-guide.pdf",
  "page": 20,
  "type": "text",
  "parent_content": "HNSW builds a hierarchical graph where... [1024 chars]",
  "parent_index": 12,
  "child_index": 2,
  "chunking": "parent_child"
}
```

`parent_content` is used by the retrieval layer to give the LLM full context.

---

## Chunk Count vs Recursive

```
Document: vector-databases-guide.pdf (73 pages)

Recursive (512 chars):        73 chunks in Qdrant
Parent-Child (1024/256):
  Parent chunks: ~37
  Child chunks:  ~148  ← 4× more vectors, but 4× more precise retrieval
```

---

## Demo Example

**Query:** "What is the time complexity of HNSW search?"

**Recursive (512-char chunk retrieved):**
```
Retrieved: "HNSW builds a hierarchical graph. Each layer connects to fewer nodes
than the layer below. Search starts at the top sparse layer... IVF divides
the space into Voronoi cells. The number of clusters..."
```
HNSW answer + IVF information mixed together. LLM answer may blend both.

**Parent-Child retrieved:**
```
Child found: "This layered approach enables logarithmic O(log n) search complexity."
                                               ↑ exact fact located

Parent returned to LLM: "HNSW builds a hierarchical graph where each node connects
to M neighbours at each layer. Search starts at the top sparse layer and greedily
navigates to the query point. Each descent reduces candidates exponentially.
This layered approach enables logarithmic O(log n) search complexity, making
HNSW practical for billion-scale vector collections."
```

The LLM gets the full HNSW explanation, not just the O(log n) fragment.

---

## Using Parent Context in Retrieval

The retrieval strategies in Docustra automatically use `parent_content` when available:

```python
# In retrieval/base.py — format_sources uses parent_content if present
def _format_sources(self, docs) -> list[dict]:
    return [
        {
            "content": doc.metadata.get("parent_content", doc.page_content)[:300],
            "source": doc.metadata.get("source", "unknown"),
            "page": doc.metadata.get("page"),
        }
        for doc in docs
    ]
```

---

## When to Use

✅ **Best for:**
- Long technical documents (API docs, research papers, 10-K filings)
- When you consistently get answers that feel "incomplete"
- Production systems where retrieval accuracy directly impacts user trust
- Documents where facts are clustered in sections (not randomly scattered)

❌ **Avoid when:**
- Documents are short (under 20 pages) — minimal benefit
- Storage in Qdrant is a constraint (4× more vectors)
- Documents have no natural parent-level structure
