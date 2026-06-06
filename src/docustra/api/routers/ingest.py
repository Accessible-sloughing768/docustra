import json
import shutil
import tempfile
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from docustra.api.schemas import (
    ChunkingParamSpec,
    ChunkingStrategyInfo,
    IngestRequest,
    IngestResponse,
)
from docustra.core import IngestionError, get_logger
from docustra.ingestion.chunker import STRATEGY_DESCRIPTIONS, ChunkingStrategy
from docustra.ingestion.pipeline import IngestionPipeline

router = APIRouter(prefix="/ingest", tags=["ingestion"])
logger = get_logger(__name__)

# ── Parameter specifications per strategy ────────────────────────────────────
_PARAMS: dict[ChunkingStrategy, list[ChunkingParamSpec]] = {
    ChunkingStrategy.RECURSIVE: [
        ChunkingParamSpec(
            name="chunk_size",
            label="Chunk Size",
            type="int",
            default=512,
            min_val=64,
            max_val=4096,
            help="Max characters per chunk",
        ),
        ChunkingParamSpec(
            name="chunk_overlap",
            label="Overlap",
            type="int",
            default=64,
            min_val=0,
            max_val=512,
            help="Overlap characters between consecutive chunks",
        ),
    ],
    ChunkingStrategy.CHARACTER: [
        ChunkingParamSpec(
            name="separator",
            label="Separator",
            type="text",
            default="\n\n",
            help="Character sequence to split on (e.g. \\n\\n, ---,  |||)",
        ),
        ChunkingParamSpec(
            name="chunk_size",
            label="Chunk Size",
            type="int",
            default=512,
            min_val=64,
            max_val=4096,
            help="Max characters per chunk",
        ),
        ChunkingParamSpec(
            name="chunk_overlap",
            label="Overlap",
            type="int",
            default=64,
            min_val=0,
            max_val=512,
            help="Overlap characters between consecutive chunks",
        ),
    ],
    ChunkingStrategy.TOKEN: [
        ChunkingParamSpec(
            name="chunk_size",
            label="Chunk Size (tokens)",
            type="int",
            default=256,
            min_val=32,
            max_val=2048,
            help="Max tokens per chunk (tiktoken cl100k_base)",
        ),
        ChunkingParamSpec(
            name="chunk_overlap",
            label="Overlap (tokens)",
            type="int",
            default=32,
            min_val=0,
            max_val=256,
            help="Overlap tokens between consecutive chunks",
        ),
    ],
    ChunkingStrategy.SENTENCE_TRANSFORMERS: [
        ChunkingParamSpec(
            name="chunk_size",
            label="Chunk Size (tokens)",
            type="int",
            default=256,
            min_val=32,
            max_val=512,
            help="Max tokens per chunk (embedding model tokeniser, max 256 for all-MiniLM-L6-v2)",
        ),
        ChunkingParamSpec(
            name="chunk_overlap",
            label="Overlap (tokens)",
            type="int",
            default=32,
            min_val=0,
            max_val=128,
            help="Overlap tokens between consecutive chunks",
        ),
    ],
    ChunkingStrategy.SEMANTIC: [
        ChunkingParamSpec(
            name="breakpoint_threshold_type",
            label="Breakpoint Detection",
            type="select",
            default="percentile",
            options=["percentile", "standard_deviation", "interquartile", "gradient"],
            help="Algorithm used to detect topic-change boundaries",
        ),
    ],
    ChunkingStrategy.SENTENCE_WINDOW: [
        ChunkingParamSpec(
            name="window_size",
            label="Window Size (±sentences)",
            type="int",
            default=3,
            min_val=1,
            max_val=10,
            help="Number of sentences before and after the indexed sentence to include as context",
        ),
    ],
    ChunkingStrategy.MARKDOWN: [
        ChunkingParamSpec(
            name="chunk_size",
            label="Max Section Size (chars)",
            type="int",
            default=512,
            min_val=128,
            max_val=4096,
            help="Max characters for sections that exceed header boundaries",
        ),
    ],
    ChunkingStrategy.HTML: [
        ChunkingParamSpec(
            name="chunk_size",
            label="Max Section Size (chars)",
            type="int",
            default=512,
            min_val=128,
            max_val=4096,
            help="Max characters for HTML sections",
        ),
    ],
    ChunkingStrategy.PARENT_CHILD: [
        ChunkingParamSpec(
            name="parent_chunk_size",
            label="Parent Size (chars)",
            type="int",
            default=1024,
            min_val=256,
            max_val=8192,
            help="Size of the large parent chunk returned to the LLM",
        ),
        ChunkingParamSpec(
            name="child_chunk_size",
            label="Child Size (chars)",
            type="int",
            default=256,
            min_val=64,
            max_val=1024,
            help="Size of the small child chunk indexed for retrieval",
        ),
        ChunkingParamSpec(
            name="chunk_overlap",
            label="Overlap (chars)",
            type="int",
            default=32,
            min_val=0,
            max_val=256,
            help="Overlap between consecutive child chunks",
        ),
    ],
    ChunkingStrategy.HYPOTHETICAL_QUESTIONS: [
        ChunkingParamSpec(
            name="questions_per_chunk",
            label="Questions per Chunk",
            type="int",
            default=3,
            min_val=1,
            max_val=5,
            help="How many questions the LLM generates per chunk (more = better coverage, more LLM calls)",
        ),
    ],
}

_REQUIRES_LLM = {ChunkingStrategy.HYPOTHETICAL_QUESTIONS, ChunkingStrategy.SEMANTIC}
_BEST_FOR = {
    ChunkingStrategy.RECURSIVE: "General purpose — works well for most documents",
    ChunkingStrategy.CHARACTER: "Documents with consistent paragraph structure",
    ChunkingStrategy.TOKEN: "Strict LLM context window compliance",
    ChunkingStrategy.SENTENCE_TRANSFORMERS: "Prevents embedding model truncation",
    ChunkingStrategy.SEMANTIC: "Technical docs where topic coherence matters most",
    ChunkingStrategy.SENTENCE_WINDOW: "Dense text requiring precise retrieval + rich context",
    ChunkingStrategy.MARKDOWN: "Markdown docs, wikis, READMEs",
    ChunkingStrategy.HTML: "Web pages, HTML reports, scraped content",
    ChunkingStrategy.PARENT_CHILD: "Best retrieval accuracy on long documents",
    ChunkingStrategy.HYPOTHETICAL_QUESTIONS: "Conversational Q&A, FAQ-style documents",
}


@router.get("/strategies", response_model=list[ChunkingStrategyInfo])
async def list_chunking_strategies() -> list[ChunkingStrategyInfo]:
    """List all available chunking strategies with configurable parameters."""
    return [
        ChunkingStrategyInfo(
            id=s.value,
            name=s.name.replace("_", " ").title(),
            description=STRATEGY_DESCRIPTIONS[s],
            requires_llm=s in _REQUIRES_LLM,
            best_for=_BEST_FOR[s],
            params=_PARAMS.get(s, []),
        )
        for s in ChunkingStrategy
    ]


@router.post("", response_model=IngestResponse)
async def ingest_document(request: IngestRequest) -> IngestResponse:
    pipeline = IngestionPipeline()
    try:
        result = pipeline.ingest(
            request.file_path,
            build_graph=request.build_graph,
            chunking_strategy=request.chunking_strategy,
            chunking_params=request.chunking_params,
        )
        return IngestResponse(**result)
    except IngestionError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected ingestion error", error=str(e))
        raise HTTPException(status_code=500, detail="Ingestion failed unexpectedly.") from e


@router.post("/upload", response_model=IngestResponse)
async def upload_and_ingest(
    file: Annotated[UploadFile, File()],
    build_graph: Annotated[bool, Form()] = False,
    chunking_strategy: Annotated[str, Form()] = ChunkingStrategy.RECURSIVE,
    chunking_params: Annotated[str, Form()] = "{}",
) -> IngestResponse:
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        strategy = ChunkingStrategy(chunking_strategy)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown chunking strategy: {chunking_strategy}.",
        ) from None

    try:
        params = json.loads(chunking_params) if chunking_params else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="chunking_params must be valid JSON.") from None

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    from pathlib import Path

    pipeline = IngestionPipeline()
    try:
        result = pipeline.ingest(
            tmp_path,
            build_graph=build_graph,
            chunking_strategy=strategy,
            chunking_params=params,
        )
        result["file"] = file.filename
        return IngestResponse(**result)
    except IngestionError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    finally:
        Path(tmp_path).unlink(missing_ok=True)
