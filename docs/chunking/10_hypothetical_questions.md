# Hypothetical Questions Chunker

**Strategy ID:** `hypothetical_questions` | **LLM Required:** Yes 🤖 | **Speed:** Slow

## What It Does

For each text chunk, uses the LLM to **generate 3-5 questions** that the chunk answers. Those questions — not the chunk text — are used as the embedding text stored in Qdrant.

The core insight: **user queries and document text live in different embedding spaces**. A user asks *"How does HNSW handle deletions?"* — a question. The document says *"HNSW marks deleted nodes as tombstones during soft-deletion"* — a statement. The embedding similarity between these is lower than between two similar questions.

By embedding **questions that the chunk answers**, the indexed representation looks like user queries — dramatically improving retrieval for conversational and Q&A-style access patterns.

---

## Relationship to HyDE

This is the **ingestion-time inverse of HyDE**:

| | HyDE (Query Time) | Hypothetical Questions (Ingestion Time) |
|---|---|---|
| When | At query time | At ingestion time |
| What | Generates a hypothetical document from the query | Generates hypothetical questions from the document |
| Embeds | The hypothetical document | The generated questions |
| Uses | Hypothetical doc vector to search real docs | Question vectors to answer real queries |
| LLM calls | 1 per query | 1 per chunk |

They're complementary — use both together for maximum alignment.

---

## How It Works

```
Chunk text:
"HNSW marks deleted vectors as tombstones during soft deletion.
 These tombstones are cleaned up during the next segment compaction.
 Hard deletion removes the vector immediately but is more expensive."

LLM prompt: "Generate 3 questions this passage answers"

Generated questions:
Q1: "How does HNSW handle deleted vectors?"
Q2: "What is soft deletion in a vector database?"
Q3: "What happens during segment compaction in Qdrant?"

Stored in Qdrant (3 vectors per chunk):
┌───────────────────────────────��────────────────────────┐
│ Vector 1: embed("How does HNSW handle deleted vectors?")│
│ Payload:  {original_content: "HNSW marks deleted...",  │
│            question_index: 0}                          │
│                                                        │
│ Vector 2: embed("What is soft deletion in vector DB?") │
│ Payload:  {original_content: "HNSW marks deleted...",  │
│            question_index: 1}                          │
│                                                        │
│ Vector 3: embed("What happens during compaction?")     │
│ Payload:  {original_content: "HNSW marks deleted...",  │
│            question_index: 2}                          │
└────────────────────────────────────────────────────────┘

Query: "How are deletions handled in Qdrant?"
  → Similarity to Q1: 0.94 (near-identical questions!)
  → LLM receives original_content: "HNSW marks deleted vectors as tombstones..."
```

---

## Configuration

```json
{
  "chunking_strategy": "hypothetical_questions",
  "chunking_params": {
    "questions_per_chunk": 3
  }
}
```

| questions_per_chunk | Vectors in Qdrant | Retrieval coverage |
|---|---|---|
| 2 | 2× more | Good |
| 3 | 3× more | Very good (default) |
| 5 | 5× more | Comprehensive |

More questions = better coverage but more LLM calls and Qdrant storage.

---

## Metadata Produced

```python
{
  "source": "vector-databases-guide.pdf",
  "page": 15,
  "type": "text",
  "original_content": "HNSW marks deleted vectors as tombstones...",
  "question_index": 0,
  "chunking": "hypothetical_questions"
}
```

The `page_content` of the stored document is the **question** (used for similarity).
The `original_content` metadata is the **answer** (returned to the LLM).

---

## Cost Analysis

```
Document: 73 chunks × 3 questions = 219 LLM calls

At 15 RPM free tier with retry backoff:
  Time: ~15-20 minutes for 73-chunk document

On paid API (1000 RPM):
  Time: ~15 seconds
```

⚠️ **This strategy is impractical on the free API tier for large documents.** Use it for small, high-value documents (< 20 chunks) or upgrade to a paid tier.

---

## Demo Example

**Document section:**
```
"Qdrant supports both dense and sparse vectors in the same collection.
 Dense vectors capture semantic meaning through neural embeddings.
 Sparse vectors represent term frequency (like BM25) for keyword matching.
 Combining both enables hybrid search with RRF (Reciprocal Rank Fusion)."
```

**Generated questions:**
```
Q1: "What types of vectors does Qdrant support?"
Q2: "What is the difference between dense and sparse vectors?"
Q3: "How does hybrid search work in Qdrant?"
Q4: "What is RRF in the context of vector search?"
```

**Queries that now work perfectly:**
- "Does Qdrant support keyword search?" → matches Q1/Q3
- "What is BM25 in vector databases?" → matches Q2
- "How to combine semantic and keyword search?" → matches Q3
- "What is reciprocal rank fusion?" → matches Q4

All four queries retrieve the same chunk with its full explanation.

---

## Combining with Other Strategies

For best results, combine Hypothetical Questions with Parent-Child:

1. First apply Parent-Child chunking (creates parent + child chunks)
2. Then apply Hypothetical Questions to child chunks only

```
Child chunk (256 chars) → 3 questions generated → 3 vectors
Each vector's metadata has:
  - original_content: child chunk text
  - parent_content: full parent chunk (1024 chars) for LLM context
```

This is the highest-quality retrieval setup — but most expensive to build.

---

## When to Use

✅ **Best for:**
- FAQ documents, knowledge bases, Q&A pairs
- Documentation accessed conversationally ("How do I...", "What is...")
- High-value small documents where ingestion cost is acceptable
- When you've observed users phrasing questions that "miss" relevant chunks

❌ **Avoid when:**
- Document has >50 chunks (too many LLM calls on free tier)
- Document is a report/narrative (questions won't align well)
- Cost is a concern (3 LLM calls per chunk × document size)
- Time-sensitive batch processing

---

## Fallback Behavior

If the LLM fails to generate questions for a chunk (rate limit, malformed output), the system falls back to storing the original chunk text as the embedding. No data is lost.
