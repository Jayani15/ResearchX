def chunk_text(
    pages: list[dict],
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[dict]:

    chunks = []

    for page in pages:
        text = page["text"]

        start = 0

        while start < len(text):

            end = start + chunk_size

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(
                    {
                        "chunk_id": len(chunks),
                        "page_number": page["page_number"],
                        "text": chunk,
                    }
                )

            start += chunk_size - overlap

    return chunks