"""
PDF text extraction and section-aware chunking using PyMuPDF (fitz).
"""

import re
import fitz

COMMON_SECTIONS = [
    "Hospitalization Coverage",
    "In-Patient Care",
    "Day Care Procedures",
    "Room Rent Limit",
    "ICU Limits",
    "Deductible and Co-pay",
    "Waiting Periods",
    "Pre- and Post-Hospitalization",
    "Exclusions",
    "General Exclusions",
    "Sub-Limits",
    "Specific Illness Limits",
    "Claim Process",
    "Cashless Authorization",
    "Reimbursement Claims",
    "Important Conditions",
    "Terms and Conditions",
    "Definitions",
    "Eligibility",
    "Benefits Schedule",
    "Maternity Benefits",
    "Ambulance Charges",
    "Preventive Health Check-up",
]


def detect_heading(line: str) -> str | None:
    """Detect if a line looks like a section or heading in an insurance policy."""
    line = line.strip()
    if not line or len(line) > 90:
        return None

    # Numbered heading: '1. Hospitalization Coverage' or 'Section 2: ...' or 'Part A - ...'
    m_num = re.match(
        r"^(?:(?:Section|Article|Part)\s+[A-Za-z0-9]+[:.\-\s]+|\d+[\.\)]\s+)([A-Za-z0-9\s\-/&,\(\)]+)",
        line,
        re.IGNORECASE,
    )
    if m_num:
        clean_heading = m_num.group(1).strip()
        if len(clean_heading) >= 3:
            return clean_heading

    # Common insurance section names match
    for sec in COMMON_SECTIONS:
        if line.lower() == sec.lower() or line.lower().startswith(sec.lower()):
            return sec

    # Uppercase title line (e.g. 'BENEFIT SCHEDULE', 'GENERAL CONDITIONS')
    if line.isupper() and 4 <= len(line) <= 60 and not line.endswith("."):
        return line.title()

    # Short capitalized line ending with a colon
    if line.endswith(":") and len(line) <= 50 and line[0].isupper():
        return line.rstrip(":").strip()

    return None


def extract_and_chunk(file_path: str) -> list[dict]:
    """
    Extract text from every PDF page using PyMuPDF.
    Preserves:
      - page number (1-based)
      - section/heading if detectable
      - text
    Returns chunks in format:
      {
          "text": "...",
          "page": 7,
          "section": "Hospitalisation",
          "chunk_id": "chunk_7_1"
      }
    """
    doc = fitz.open(file_path)
    chunks: list[dict] = []
    chunk_counter = 0
    current_section = "General Policy"

    for page_idx in range(len(doc)):
        page_num = page_idx + 1
        page = doc[page_idx]
        text = page.get_text()
        if not text or not text.strip():
            continue

        lines = [line.strip() for line in text.split("\n")]
        buffer: list[str] = []

        for line in lines:
            if not line:
                continue

            heading = detect_heading(line)
            if heading:
                # Flush existing buffer before switching section
                if buffer:
                    chunk_text = " ".join(buffer).strip()
                    if len(chunk_text) >= 40:
                        chunk_counter += 1
                        chunks.append({
                            "text": chunk_text,
                            "page": page_num,
                            "section": current_section,
                            "chunk_id": f"chunk_{page_num}_{chunk_counter}",
                        })
                    buffer = []
                current_section = heading
                continue

            buffer.append(line)
            combined = " ".join(buffer)

            # Split into reasonable chunks (~400-550 characters)
            if len(combined) >= 480:
                chunk_counter += 1
                chunks.append({
                    "text": combined.strip(),
                    "page": page_num,
                    "section": current_section,
                    "chunk_id": f"chunk_{page_num}_{chunk_counter}",
                })
                # Keep small trailing context if possible
                words = buffer[-3:] if len(buffer) >= 3 else []
                buffer = words

        if buffer:
            chunk_text = " ".join(buffer).strip()
            if len(chunk_text) >= 20:
                chunk_counter += 1
                chunks.append({
                    "text": chunk_text,
                    "page": page_num,
                    "section": current_section,
                    "chunk_id": f"chunk_{page_num}_{chunk_counter}",
                })

    doc.close()
    return chunks
