from pathlib import Path

from docustra.core import IngestionError, get_logger
from docustra.graph.builder import KnowledgeGraphBuilder
from docustra.ingestion.chunker import ChunkingStrategy, get_chunker
from docustra.ingestion.embedder import get_embeddings
from docustra.ingestion.parser import DocumentParser
from docustra.storage.vector_store import VectorStore

logger = get_logger(__name__)


class IngestionPipeline:
    """
    End-to-end document ingestion:
      parse → chunk (selectable strategy) → embed → Qdrant
      optionally: entity extract → Neo4j knowledge graph
    """

    def __init__(self) -> None:
        self._parser = DocumentParser()
        self._vector_store = VectorStore(get_embeddings())
        self._graph_builder = KnowledgeGraphBuilder()

    def ingest(
        self,
        file_path: str | Path,
        build_graph: bool = False,
        chunking_strategy: ChunkingStrategy | str = ChunkingStrategy.RECURSIVE,
        chunking_params: dict | None = None,
    ) -> dict:
        path = Path(file_path)
        if not path.exists():
            raise IngestionError(f"File not found: {path}")

        logger.info(
            "Starting ingestion",
            file=path.name,
            strategy=str(chunking_strategy),
            build_graph=build_graph,
        )

        try:
            parsed = self._parser.parse(path)
        except Exception as e:
            raise IngestionError(f"Parsing failed for {path.name}: {e}") from e

        all_docs = parsed.text_chunks + parsed.tables

        chunker = get_chunker(chunking_strategy, **(chunking_params or {}))
        chunks = chunker.chunk(all_docs)

        logger.info(
            "Chunking complete",
            strategy=str(chunking_strategy),
            input_docs=len(all_docs),
            output_chunks=len(chunks),
        )

        ids = self._vector_store.add_documents(chunks)

        graph_entities = 0
        if build_graph and chunks:
            graph_entities = self._graph_builder.build_from_documents(chunks)

        logger.info(
            "Ingestion complete",
            file=path.name,
            chunks=len(chunks),
            images=len(parsed.images),
            graph_entities=graph_entities,
        )

        return {
            "file": path.name,
            "chunks_indexed": len(chunks),
            "images_found": len(parsed.images),
            "graph_entities": graph_entities,
            "chunking_strategy": str(chunking_strategy),
            "doc_ids": ids,
        }

    def ingest_batch(
        self,
        file_paths: list[str | Path],
        build_graph: bool = False,
        chunking_strategy: ChunkingStrategy | str = ChunkingStrategy.RECURSIVE,
    ) -> list[dict]:
        results = []
        for path in file_paths:
            try:
                results.append(
                    self.ingest(path, build_graph=build_graph, chunking_strategy=chunking_strategy)
                )
            except IngestionError as e:
                logger.error("Ingestion failed", file=str(path), error=str(e))
                results.append({"file": str(path), "error": str(e)})
        return results
