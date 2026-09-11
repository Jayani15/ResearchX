import re


SECTION_PATTERNS = {
    "abstract": r"^\s*(abstract)\s*$",
    "introduction": r"^\s*(1[\.\s]+)?introduction\s*$",
    "literature_review": r"^\s*(2[\.\s]+)?(literature review|related work|related studies)\s*$",
    "methodology": r"^\s*(3[\.\s]+)?(methodology|methods|materials and methods|proposed method)\s*$",
    "results": r"^\s*(4[\.\s]+)?(results|experimental results|experiments)\s*$",
    "discussion": r"^\s*(5[\.\s]+)?discussion\s*$",
    "conclusion": r"^\s*(6[\.\s]+)?(conclusion|conclusions)\s*$",
    "references": r"^\s*(references|bibliography)\s*$",
}


def detect_section_heading(line: str) -> str | None:
    """
    Identify whether a line is a known research-paper section heading.
    """

    cleaned = line.strip()

    if not cleaned:
        return None

    for section, pattern in SECTION_PATTERNS.items():
        if re.match(pattern, cleaned, re.IGNORECASE):
            return section

    return None


def split_into_sections(text: str) -> dict[str, str]:
    """
    Split research-paper text into detected sections.
    """

    lines = text.splitlines()

    sections = {}
    current_section = "unknown"
    current_content = []

    for line in lines:

        detected_section = detect_section_heading(line)

        if detected_section:

            # Save previous section
            if current_content:
                sections[current_section] = "\n".join(
                    current_content
                ).strip()

            current_section = detected_section
            current_content = []

        else:
            current_content.append(line)

    # Save final section
    if current_content:
        sections[current_section] = "\n".join(
            current_content
        ).strip()

    return sections