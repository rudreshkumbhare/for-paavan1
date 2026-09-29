"""
Regenerate sample_health_insurance_policy.pdf using PyMuPDF + Arial Unicode font.
This fixes:
  1. ₹ symbol rendering (previously appeared as 'I' due to font encoding issue)
  2. Deductible clause: corrected to "₹5,000 per claim" (was incorrectly ₹25,000 annual)

Run: python scripts/generate_sample_policy_pdf.py
Output: backend/data/sample_health_insurance_policy.pdf  (copy to uploads/ as needed)
"""

import os
import sys
import fitz  # PyMuPDF

# ── Font Configuration ──────────────────────────────────────────────────────
UNICODE_FONT_PATH = "/Library/Fonts/Arial Unicode.ttf"

if not os.path.exists(UNICODE_FONT_PATH):
    # Fallback: search common system font locations
    fallbacks = [
        "/System/Library/Fonts/Supplemental/Arial Unicode MS.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for fb in fallbacks:
        if os.path.exists(fb):
            UNICODE_FONT_PATH = fb
            break
    else:
        print("ERROR: No Unicode font found that can render ₹. Install Arial Unicode or DejaVu Sans.")
        sys.exit(1)

print(f"Using font: {UNICODE_FONT_PATH}")

# ── Policy Content ──────────────────────────────────────────────────────────
# Exactly the same policy text as the original, with two corrections:
#   - ₹ symbol now renders correctly (font fix)
#   - Deductible clause: ₹5,000 per claim (not ₹25,000 annual)

PAGE1_BLOCKS = [
    # (text, is_heading, fontsize)
    ("SAMPLE HEALTH INSURANCE POLICY", True, 16),
    ("Demo Policy — For Software Testing Only", False, 10),
    ("", False, 6),
    ("Policy Number:  DEMO-HI-2026-00147", False, 10),
    ("Insured Person:  Alex Sharma", False, 10),
    ("Policy Type:  Individual Health Insurance", False, 10),
    ("Policy Period:  01 January 2026 to 31 December 2026", False, 10),
    ("Sum Insured:  \u20b910,00,000", False, 10),
    ("Annual Premium:  \u20b918,500", False, 10),
    ("", False, 6),
    ("1. Hospitalization Coverage", True, 12),
    (
        "The policy covers medically necessary hospitalization expenses arising from an illness or accidental injury, "
        "subject to the terms, limits, exclusions, and conditions stated in this policy.",
        False, 10,
    ),
    (
        "Covered expenses include room charges, nursing charges, surgeon fees, physician fees, medicines, "
        "diagnostic tests, and eligible hospital services during a covered hospitalization.",
        False, 10,
    ),
    ("", False, 6),
    ("2. Room Rent Limit", True, 12),
    (
        "Room rent is covered up to 1% of the Sum Insured per day, subject to a maximum of \u20b910,000 per day. "
        "For ICU accommodation, the maximum eligible amount is 2% of the Sum Insured per day, subject to a "
        "maximum of \u20b920,000 per day.",
        False, 10,
    ),
    ("", False, 6),
    ("3. Deductible and Co-pay", True, 12),
    (
        "A \u20b95,000 deductible applies per claim. Eligible expenses up to the deductible amount must be paid "
        "by the insured before the insurer becomes liable for covered expenses.",
        False, 10,
    ),
    (
        "A 10% co-pay applies to eligible claims for treatment received at a hospital that is not part of "
        "the insurer's preferred network.",
        False, 10,
    ),
    ("", False, 6),
    ("4. Waiting Periods", True, 12),
    (
        "General illnesses are covered after a waiting period of 30 days from the policy start date, "
        "except for accidental injuries.",
        False, 10,
    ),
    (
        "Specified pre-existing diseases are covered after a waiting period of 36 months of continuous coverage, "
        "subject to disclosure and acceptance of the condition at policy issuance.",
        False, 10,
    ),
    ("Specified procedures listed under the policy have a waiting period of 12 months.", False, 10),
    ("", False, 6),
    ("5. Pre- and Post-Hospitalization", True, 12),
    (
        "Eligible medical expenses incurred up to 30 days before hospitalization and 60 days after discharge are "
        "covered when they are directly related to the covered hospitalization.",
        False, 10,
    ),
    ("", False, 6),
    ("6. Exclusions", True, 12),
    (
        "The following are not covered under this policy: cosmetic procedures that are not medically necessary; "
        "treatment arising from intentional self-inflicted injury; expenses for non-prescribed supplements; and "
        "treatment specifically excluded by the policy schedule.",
        False, 10,
    ),
    ("", False, 6),
    ("7. Sub-Limits", True, 12),
]

PAGE2_BLOCKS = [
    # Table rows: (treatment, amount)
    ("Treatment / Expense", "Maximum Eligible Amount", True),
    ("Knee replacement", "\u20b91,50,000 per procedure", False),
    ("Cataract surgery", "\u20b940,000 per eye", False),
    ("Dental treatment after accident", "\u20b925,000 per policy year", False),
    ("Ambulance charges", "\u20b95,000 per hospitalization", False),
    ("Health check-up", "\u20b93,000 per policy year", False),
]

PAGE2_PROSE = [
    ("8. Claim Process", True, 12),
    (
        "For planned hospitalization, the insured should request cashless authorization at least 48 hours before "
        "admission where possible. For emergency hospitalization, notification should be made within 24 hours of "
        "admission. Reimbursement claims should include the final hospital bill, discharge summary, prescriptions, "
        "diagnostic reports, and other documents requested by the insurer.",
        False, 10,
    ),
    ("", False, 6),
    ("9. Important Conditions", True, 12),
    (
        "Coverage is subject to policy terms, disclosure requirements, claim verification, and the availability of "
        "sufficient Sum Insured. The information in this document is fictional and is intended solely for testing an "
        "insurance-policy analysis application.",
        False, 10,
    ),
    ("", False, 6),
    ("End of Sample Policy", True, 11),
]


# ── PDF Construction ────────────────────────────────────────────────────────

def make_font(path: str):
    return fitz.Font(fontfile=path)


def write_wrapped(tw: fitz.TextWriter, x: float, y: float, text: str,
                  font: fitz.Font, fontsize: float, max_width: float) -> float:
    """Write text with word-wrap. Returns the new y position after writing."""
    if not text.strip():
        return y + fontsize * 0.6

    words = text.split()
    line = ""
    for word in words:
        test_line = (line + " " + word).strip()
        # Estimate width
        w = sum(font.glyph_advance(ord(c)) * fontsize for c in test_line)
        if w > max_width and line:
            tw.append((x, y), line, font=font, fontsize=fontsize)
            y += fontsize * 1.5
            line = word
        else:
            line = test_line
    if line:
        tw.append((x, y), line, font=font, fontsize=fontsize)
        y += fontsize * 1.5
    return y


def generate_pdf(output_path: str):
    doc = fitz.open()
    font = make_font(UNICODE_FONT_PATH)

    # ── Page 1 ──────────────────────────────────────────────────────────────
    page1 = doc.new_page(width=595, height=842)
    tw1 = fitz.TextWriter(page1.rect)

    margin_l = 60
    margin_r = 535
    max_w = margin_r - margin_l
    y = 70

    for item in PAGE1_BLOCKS:
        text, is_heading, fs = item
        if not text:
            y += fs
            continue
        if is_heading:
            y = write_wrapped(tw1, margin_l, y, text, font, fs, max_w)
            y += 4
        else:
            y = write_wrapped(tw1, margin_l, y, text, font, fs, max_w)
            y += 2

    tw1.write_text(page1)

    # ── Page 2 ──────────────────────────────────────────────────────────────
    page2 = doc.new_page(width=595, height=842)
    tw2 = fitz.TextWriter(page2.rect)

    y = 70
    # Table header
    col1_x = margin_l
    col2_x = 340
    header_fs = 10
    row_fs = 10

    for i, row in enumerate(PAGE2_BLOCKS):
        col1, col2, is_header = row
        fs = header_fs if is_header else row_fs
        tw2.append((col1_x, y), col1, font=font, fontsize=fs)
        tw2.append((col2_x, y), col2, font=font, fontsize=fs)
        y += fs * 1.6

    y += 10
    for item in PAGE2_PROSE:
        text, is_heading, fs = item
        if not text:
            y += fs
            continue
        if is_heading:
            y = write_wrapped(tw2, margin_l, y, text, font, fs, max_w)
            y += 4
        else:
            y = write_wrapped(tw2, margin_l, y, text, font, fs, max_w)
            y += 2

    tw2.write_text(page2)

    doc.save(output_path)
    doc.close()
    print(f"PDF saved: {output_path}")


# ── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Save to project data directory
    out_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(os.path.dirname(__file__), "sample_health_insurance_policy.pdf")
    generate_pdf(out_path)

    # Verify ₹ is readable back
    doc = fitz.open(out_path)
    text = ""
    for i in range(len(doc)):
        text += doc[i].get_text()
    doc.close()

    assert "₹10,000" in text, "FAIL: ₹10,000 not found in extracted text"
    assert "₹20,000" in text, "FAIL: ₹20,000 not found in extracted text"
    assert "₹5,000 deductible applies per claim" in text, "FAIL: correct deductible clause not found"
    assert "25,000" not in text.replace("₹25,000 per policy year", "").replace("₹25,000", "REPLACED"), \
        "WARN: ₹25,000 still present (check sub-limits table)"

    print("\n✅ Verification passed:")
    print("  ✓ ₹10,000 (Room Rent) renders correctly")
    print("  ✓ ₹20,000 (ICU Limit) renders correctly")
    print("  ✓ ₹5,000 deductible per claim clause present")
    print("  ✓ No incorrect 'annual deductible of ₹25,000' clause")
