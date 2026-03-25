"""
pdf_extractor.py
----------------
Reads all PDF files in a given folder and extracts scheme data
using a rule-based approach. Saves output to data/schemes.json.

Usage:
    python scripts/pdf_extractor.py --pdf_dir ./pdfs --output ./data/schemes.json
"""

import os
import json
import re
import argparse
from pathlib import Path

# Try to import PDF libraries
try:
    import pdfplumber
    PDF_LIB = "pdfplumber"
except ImportError:
    try:
        import fitz  # PyMuPDF
        PDF_LIB = "pymupdf"
    except ImportError:
        PDF_LIB = None
        print("[WARNING] No PDF library found. Install pdfplumber: pip install pdfplumber")


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF file."""
    text = ""
    if PDF_LIB == "pdfplumber":
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    elif PDF_LIB == "pymupdf":
        import fitz
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text() + "\n"
    else:
        raise RuntimeError("No PDF extraction library available. Run: pip install pdfplumber")
    return text


def extract_scheme_name(text: str) -> str:
    """Extract scheme name from text using keyword patterns."""
    patterns = [
        r"(?:SCHEME OF|SCHEME FOR|GUIDELINES FOR|GUIDELINES\s+FOR)\s+([A-Z][^\n]{5,80})",
        r"(?:SCHOLARSHIP SCHEME|FELLOWSHIP SCHEME)\s+(?:FOR|OF)\s+([A-Z][^\n]{5,80})",
        r"^([A-Z][A-Z\s\-&]{10,80})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(1).strip().title()
    # Fallback: first non-empty line
    for line in text.split("\n"):
        line = line.strip()
        if len(line) > 15 and line.isupper():
            return line.title()
    return "Unknown Scheme"


def extract_eligibility(text: str) -> list:
    """Extract eligibility conditions as a list."""
    conditions = []
    # Find eligibility section
    section_match = re.search(
        r"(?:ELIGIBILITY|ELIGIBILITY CONDITIONS?|ELIGIBILITY CRITERIA)[:\s]*(.*?)(?:\n\n|\d+\.\s+[A-Z])",
        text, re.DOTALL | re.IGNORECASE
    )
    if section_match:
        block = section_match.group(1)
        # Split by numbered/bulleted items
        items = re.split(r"\n\s*[\(\[]?(?:[ivxIVX]+|\d+|[a-z])[\)\]\.]\s+", block)
        for item in items:
            item = item.strip().replace("\n", " ")
            if len(item) > 20:
                conditions.append(item[:300])  # cap length
    return conditions[:15]  # max 15 conditions


def extract_documents(text: str) -> list:
    """Extract required documents list."""
    docs = []
    section_match = re.search(
        r"(?:REQUIRED DOCUMENTS?|DOCUMENTS? REQUIRED|documents.*?required)[:\s]*(.*?)(?:\n\n|\d+\.\s+[A-Z])",
        text, re.DOTALL | re.IGNORECASE
    )
    if section_match:
        block = section_match.group(1)
        items = re.split(r"\n\s*[\(\[]?(?:[ivxIVX]+|\d+|[a-z])[\)\]\.]\s+", block)
        for item in items:
            item = item.strip().replace("\n", " ")
            if 10 < len(item) < 200:
                docs.append(item)
    # Common fallback patterns
    common_docs = [
        r"(Aadhaar[^\n.]{0,60})",
        r"(income certificate[^\n.]{0,60})",
        r"(caste certificate[^\n.]{0,60})",
        r"(disability certificate[^\n.]{0,60})",
        r"(UDID[^\n.]{0,60})",
    ]
    if not docs:
        for pat in common_docs:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                docs.append(m.group(1).strip())
    return docs[:12]


def extract_office(text: str) -> str:
    """Extract office/contact information."""
    patterns = [
        r"(?:address|office|contact)[:\s]+([^\n]{20,200})",
        r"((?:Ministry|Department|Commission|Council)[^\n]{20,150})",
        r"(New Delhi[^\n]{0,100})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "Refer to respective Ministry/Department website"


def extract_link(text: str) -> str:
    """Extract application link from text."""
    urls = re.findall(r"https?://[^\s\)\"\'<>]{5,100}", text)
    # Prefer scholarship portals
    for url in urls:
        if "scholarships.gov.in" in url or "nsp" in url.lower():
            return url
    if urls:
        return urls[0]
    return "https://www.scholarships.gov.in"


def process_pdf(pdf_path: str, scheme_id: str) -> dict:
    """Process a single PDF and return a scheme dict."""
    print(f"[INFO] Processing: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)

    scheme = {
        "scheme_id": scheme_id,
        "scheme_name": extract_scheme_name(text),
        "source_file": os.path.basename(pdf_path),
        "eligibility_conditions": extract_eligibility(text),
        "required_documents": extract_documents(text),
        "office_to_visit": extract_office(text),
        "application_link": extract_link(text),
    }
    return scheme


def main():
    parser = argparse.ArgumentParser(description="Extract scheme data from PDFs")
    parser.add_argument("--pdf_dir", default="./pdfs", help="Directory containing PDF files")
    parser.add_argument("--output", default="./data/schemes.json", help="Output JSON file path")
    args = parser.parse_args()

    pdf_dir = Path(args.pdf_dir)
    if not pdf_dir.exists():
        print(f"[ERROR] PDF directory not found: {pdf_dir}")
        return

    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[WARNING] No PDF files found in {pdf_dir}")
        return

    all_schemes = []
    for idx, pdf_file in enumerate(pdf_files, start=1):
        scheme_id = f"SCH{idx:03d}"
        try:
            scheme = process_pdf(str(pdf_file), scheme_id)
            all_schemes.append(scheme)
            print(f"[OK] Extracted: {scheme['scheme_name']}")
        except Exception as e:
            print(f"[ERROR] Failed to process {pdf_file.name}: {e}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_schemes, f, indent=2, ensure_ascii=False)

    print(f"\n[DONE] Extracted {len(all_schemes)} schemes → {output_path}")


if __name__ == "__main__":
    main()
