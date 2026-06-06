# HTML Header Text Splitter

**Strategy ID:** `html` | **LLM Required:** No

## What It Does

Splits HTML documents on heading tags (`<h1>` through `<h4>`) and preserves the **heading breadcrumb path** as metadata. Analogous to the Markdown splitter but for HTML content — web pages, API docs, scraped websites, HTML reports.

---

## How It Works

```html
Input HTML:
<h1>Qdrant Documentation</h1>
<h2>Getting Started</h2>
<p>Install Qdrant using Docker...</p>

<h2>Collections</h2>
<h3>Creating a Collection</h3>
<p>A collection is the top-level container...</p>

<h3>Collection Configuration</h3>
<p>You can configure vector size, distance metric...</p>

Split on <h1>, <h2>, <h3>:

Chunk 1:
  {h1: "Qdrant Documentation", h2: "Getting Started"}
  "Install Qdrant using Docker..."

Chunk 2:
  {h1: "Qdrant Documentation", h2: "Collections", h3: "Creating a Collection"}
  "A collection is the top-level container..."

Chunk 3:
  {h1: "Qdrant Documentation", h2: "Collections", h3: "Collection Configuration"}
  "You can configure vector size, distance metric..."
```

---

## Metadata Produced

```python
{
  "source": "qdrant_docs.html",
  "h1": "Qdrant Documentation",
  "h2": "Collections",
  "h3": "Creating a Collection",
  "chunking": "html"
}
```

The full heading path lets you filter retrieval by section:
```python
# Only retrieve from the "Collections" section
filter={"must": [{"key": "h2", "match": {"value": "Collections"}}]}
```

---

## Configuration

```json
{
  "chunking_strategy": "html",
  "chunking_params": {
    "chunk_size": 800
  }
}
```

Default headers: `h1`, `h2`, `h3`, `h4`

---

## Graceful Fallback

If the input is not valid HTML (e.g., a PDF page extracted as plain text), the HTML splitter falls back to `RecursiveChunker` automatically rather than failing.

---

## Demo Example

**Use case:** Ingesting a scraped product documentation page

```html
<h1>Qdrant REST API</h1>
<h2>Points API</h2>
<h3>POST /collections/{collection_name}/points</h3>
<p>Insert or update points in a collection.
   Points are objects containing a vector and optional payload...</p>

<h3>GET /collections/{collection_name}/points/{id}</h3>
<p>Retrieve a point by its ID. Returns the vector and payload...</p>
```

**After HTML chunking:**
```
Chunk 1 metadata: {h1: "Qdrant REST API", h2: "Points API",
                   h3: "POST /collections/{collection_name}/points"}
Chunk 1 content:  "Insert or update points in a collection..."

Chunk 2 metadata: {h1: "Qdrant REST API", h2: "Points API",
                   h3: "GET /collections/{collection_name}/points/{id}"}
Chunk 2 content:  "Retrieve a point by its ID..."
```

Query "How do I insert points?" retrieves Chunk 1 with perfect precision.

---

## When to Use

✅ **Best for:**
- Web-scraped content (product docs, Wikipedia, news)
- API documentation in HTML format
- HTML exports from Confluence, Notion, SharePoint
- Any HTML where `<h1>`-`<h4>` tags mark semantic sections

❌ **Avoid when:**
- Content has no heading tags (flat HTML)
- HTML is deeply nested without semantic headings
- Input is PDF text (use `markdown` strategy after conversion)

---

## Ingesting Web Pages

```python
# Scrape and ingest a documentation page
import requests

html = requests.get("https://qdrant.tech/documentation/concepts/collections/").text

# Save to file, then ingest via API
with open("data/qdrant_collections.html", "w") as f:
    f.write(html)

# Ingest (note: currently Docustra only supports PDFs via upload)
# For HTML, use the file_path endpoint with a pre-saved HTML file
```

> **Note:** Docustra's upload endpoint currently accepts PDFs only. HTML files can be ingested via the `/ingest` endpoint with a local `file_path`. Full HTML upload support is a planned enhancement.
