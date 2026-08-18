"""Document loading and chunking utilities for multi-format document ingestion (PDF, Text, Markdown, JSON)."""

import io
import json
from typing import List, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_and_chunk_file(
    file_bytes: bytes,
    filename: str,
    content_type: Optional[str] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> List[Document]:
    """Parse raw file bytes into chunked LangChain Documents.

    Supports:
    - .pdf via pypdf
    - .txt / .md plain text
    - .json array/dict structured documents

    Args:
        file_bytes (bytes): Raw content of the uploaded file.
        filename (str): Name of the file including extension.
        content_type (Optional[str]): MIME type if available.
        chunk_size (int): Character chunk limit per document slice.
        chunk_overlap (int): Overlap between adjacent chunks.

    Returns:
        List[Document]: List of chunked and metadata-enriched Document objects.
    """
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    text_content = ""
    metadata = {
        "title": filename,
        "source": f"user_upload:{filename}",
        "url": f"file:///{filename}",
        "file_type": ext or "text",
    }

    if ext == "pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages = []
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)
            text_content = "\n\n".join(pages)
        except Exception as e:
            raise ValueError(f"Failed to parse PDF file '{filename}': {e}")

    elif ext == "json":
        try:
            parsed = json.loads(file_bytes.decode("utf-8"))
            if isinstance(parsed, list):
                docs = []
                for item in parsed:
                    if isinstance(item, dict):
                        page_content = item.get("page_content") or item.get("text") or str(item)
                        item_meta = metadata.copy()
                        if "title" in item:
                            item_meta["title"] = item["title"]
                        docs.append(Document(page_content=page_content, metadata=item_meta))
                    elif isinstance(item, str):
                        docs.append(Document(page_content=item, metadata=metadata))
                if docs:
                    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                    return splitter.split_documents(docs)
            elif isinstance(parsed, dict):
                text_content = json.dumps(parsed, indent=2)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON file '{filename}': {e}")

    if not text_content:
        # Default text / markdown parsing
        try:
            text_content = file_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            raise ValueError(f"Failed to decode text file '{filename}': {e}")

    if not text_content.strip():
        raise ValueError(f"File '{filename}' contains no extractable text content.")

    base_doc = Document(page_content=text_content, metadata=metadata)
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents([base_doc])
