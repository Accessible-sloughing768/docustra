# Character Text Splitter

**Strategy ID:** `character` | **LLM Required:** No

## What It Does

Splits text using a **single fixed separator** (default: `\n\n`). Unlike Recursive, it does not fall back to smaller separators — if a chunk is still too large after splitting on the separator, it just keeps it as-is (or hard-cuts it). It's the simplest, most predictable splitter.

---

## How It Works

```
Input text:
┌────────────────────────────────────────┐
│ Section A (200 chars)\n\n              │
│ Section B (180 chars)\n\n              │
│ Section C (600 chars)\n\n              │  ← too large, but no fallback
│ Section D (150 chars)                  │
└────────────────────────────────────────┘

chunk_size=512, separator="\n\n"

Split on "\n\n" only:
→ ["Section A", "Section B", "Section C (600 chars — kept as-is)", "Section D"]
```

This is a key difference from Recursive — Section C stays whole even if it exceeds `chunk_size`.

---

## Configuration

```env
CHUNK_SIZE=512
CHUNK_OVERLAP=64
```

Default separator is `\n\n` (paragraph break). Change it via `chunking_params`:
```json
{
  "chunking_strategy": "character",
  "chunking_params": {
    "separator": "\n---\n",
    "chunk_size": 800
  }
}
```

Common separators to use:
| Separator | Use case |
|---|---|
| `\n\n` | Paragraph-structured text (default) |
| `\n` | Line-by-line content |
| `\n---\n` | Markdown horizontal rules |
| `\n===\n` | Section dividers |
| `|||` | Custom delimiter in processed docs |

---

## Metadata Produced

```python
{"source": "document.pdf", "page": 1, "type": "text"}
```

---

## Demo Example

**Use case:** A legal document where each clause is separated by `\n\n`:

```
Input:
"1. PARTIES. This Agreement is entered into...\n\n
 2. TERM. The term of this Agreement shall...\n\n
 3. PAYMENT. Client shall pay Vendor..."

After character chunking (separator="\n\n"):
Chunk 1: "1. PARTIES. This Agreement is entered into..."
Chunk 2: "2. TERM. The term of this Agreement shall..."
Chunk 3: "3. PAYMENT. Client shall pay Vendor..."
```

Each clause becomes its own chunk — making clause-level retrieval precise.

---

## When to Use

✅ **Best for:**
- Documents with consistent, known delimiter structure
- Legal clauses, numbered sections, records separated by a fixed marker
- When you want predictable, deterministic chunk boundaries
- CSV/TSV-like text where rows are meaningful units

❌ **Avoid when:**
- Document has mixed structure (some short sections, some very long)
- You don't know the separator in advance
- Chunks may end up very large (no fallback splitting)
