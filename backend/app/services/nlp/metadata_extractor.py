import re


def extract_title(text: str) -> str:
    """
    Estimate the title from the beginning of the paper.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return ""

    # Ignore obvious metadata/header lines
    for line in lines[:10]:
        lower = line.lower()

        if (
            len(line) > 15
            and len(line) < 250
            and not lower.startswith(("abstract", "keywords", "arxiv"))
        ):
            return line

    return lines[0]


def extract_year(text: str) -> int | None:
    """
    Extract a likely publication year.
    """

    years = re.findall(r"\b(20\d{2})\b", text[:5000])

    if not years:
        return None

    # Prefer the earliest plausible publication year
    return min(int(year) for year in years)


def extract_doi(text: str) -> str | None:
    """
    Extract DOI if present.
    """

    pattern = r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b"

    match = re.search(
        pattern,
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(0).rstrip(".,;)")

    return None


def extract_metadata(text: str) -> dict:
    """
    Extract basic research-paper metadata.
    """

    return {
        "title": extract_title(text),
        "year": extract_year(text),
        "doi": extract_doi(text),
    }