# Semantic Chunker

**Strategy ID:** `semantic` | **LLM Required:** No (uses embedding model) | **Speed:** Slow

## What It Does

Instead of splitting at fixed character/token counts, **SemanticChunker** splits where the **topic changes**. It embeds every sentence, computes cosine similarity between adjacent sentences, and draws a chunk boundary wherever similarity drops below a threshold.

This produces chunks that are **semantically coherent** — each chunk discusses one topic, not an arbitrary slice of text.

---

## How It Works

```
Input text (sentences):
S1: "Vector databases store embeddings alongside metadata."
S2: "HNSW is the most common indexing algorithm used."
S3: "IVF partitions the space into Voronoi cells."
S4: "Companies using vector DBs include Pinecone and Weaviate."
S5: "Pricing models vary between serverless and dedicated plans."
S6: "Cost optimization requires understanding query patterns."

Step 1: Embed each sentence → 6 vectors (384-dim each)

Step 2: Compute cosine similarity between adjacent sentences:
  sim(S1,S2) = 0.82  ← high: both about vector DB internals
  sim(S2,S3) = 0.79  ← high: both about indexing
  sim(S3,S4) = 0.41  ← LOW: shift from technical to vendors
  sim(S4,S5) = 0.71  ← medium: still vendor-related
  sim(S5,S6) = 0.83  ← high: both about cost

Step 3: Find breakpoints (similarity < threshold percentile)
  Breakpoint detected between S3 and S4 (score 0.41 = bottom 10%)

Step 4: Split:
  Chunk 1: S1 + S2 + S3  → "Vector databases store embeddings... IVF partitions..."
  Chunk 2: S4 + S5 + S6  → "Companies using vector DBs... Cost optimization..."
```

The result: Chunk 1 is about indexing algorithms. Chunk 2 is about vendors and costs. Semantically clean.

---

## Threshold Types

The breakpoint detection can be configured via `breakpoint_threshold_type`:

| Type | How it works | When to use |
|---|---|---|
| `percentile` | Bottom X% of similarity scores are breakpoints | General purpose (default) |
| `standard_deviation` | Splits where score is >1 std dev below mean | Balanced — fewer but cleaner splits |
| `interquartile` | Splits using IQR outlier detection | When similarity distribution is skewed |
| `gradient` | Splits where similarity drops sharply | Fast-changing topic documents |

```json
{
  "chunking_strategy": "semantic",
  "chunking_params": {
    "breakpoint_threshold_type": "standard_deviation"
  }
}
```

---

## Metadata Produced

```python
{
  "source": "document.pdf",
  "page": 5,
  "type": "text",
  "chunking": "semantic"
}
```

---

## Demo Example

**Document:** vector-databases-guide.pdf

**Recursive chunking** (fixed 512 chars) — chunk straddles topic boundary:
```
Chunk 23: "...IVF creates Voronoi cell partitions for fast ANN search.
           Companies like Pinecone, Weaviate, and Qdrant offer managed..."
```
This mixes indexing algorithms + vendor comparison in one chunk.

**Semantic chunking** — respects topic boundary:
```
Chunk 18: "...IVF creates Voronoi cell partitions for fast ANN search.
           PQ compresses vectors by breaking them into sub-vectors..."
[BOUNDARY — topic shifts from algorithms to vendors]
Chunk 19: "Companies like Pinecone, Weaviate, and Qdrant offer managed
           vector database services with varying pricing models..."
```

Retrieval for "which companies offer vector databases?" now returns Chunk 19 cleanly.

---

## Performance Cost

SemanticChunker embeds every sentence before deciding where to split:

```
Document: 73 chunks after recursive = ~1000 sentences
Embedding calls: ~1000 (one per sentence)
Time: ~8-15 seconds on M2 MPS (local)
Additional API calls: 0 (uses local sentence-transformers)
```

**This is slow but free** — it uses the local embedding model, not the Gemini API.

---

## When to Use

✅ **Best for:**
- Technical documents where topic shifts happen mid-paragraph
- Research papers with distinct sections blending together
- Documents where retrieval precision matters most
- When you're willing to trade ingestion speed for retrieval quality

❌ **Avoid when:**
- Document already has clear structural delimiters (use `markdown` or `html`)
- Time-sensitive batch ingestion of many documents
- Very short documents (< 10 sentences) — not enough data for meaningful clustering

---

## Dependencies

`langchain-experimental` — installed. No additional setup required.
