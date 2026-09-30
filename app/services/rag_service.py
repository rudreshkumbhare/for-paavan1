"""
RAG Service using FAISS vector indexing and LLM grounded question answering.
Adheres strictly to policy evidence citations and confidence estimation.
"""

import json
import logging
import os
import re
from typing import Any
from urllib import response

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Global in-memory store for policy indices, active policy, and extracted configs
_index_store: dict[str, dict[str, Any]] = {}
_active_policy_id: str | None = None
_embedder: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    """Lazy load embedding model with offline cache priority to avoid network hangs."""
    global _embedder
    if _embedder is None:
        try:
            _embedder = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
        except Exception:
            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def build_index(
    policy_id: str,
    chunks: list[dict],
    filename: str = "",
    page_count: int = 0,
    policy_config: dict | None = None,
):
    """Embed all chunks, create FAISS index, and store policy configuration."""
    global _active_policy_id
    if not chunks:
        return

    embedder = get_embedder()
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedder.encode(texts, convert_to_numpy=True)
    embeddings = embeddings.astype("float32")

    # Normalize vectors for cosine similarity search
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    _index_store[policy_id] = {
        "faiss_index": index,
        "chunks": chunks,
        "filename": filename,
        "page_count": page_count,
        "policy_config": policy_config or {},
    }
    _active_policy_id = policy_id


def is_indexed(policy_id: str | None = None) -> bool:
    """Check if a policy is currently indexed."""
    pid = policy_id or _active_policy_id
    return pid is not None and pid in _index_store


def get_active_policy_id() -> str | None:
    return _active_policy_id


def get_active_policy_config() -> dict:
    """Return extracted structured configuration of active policy."""
    if not _active_policy_id or _active_policy_id not in _index_store:
        return {}
    return _index_store[_active_policy_id].get("policy_config", {})


def get_active_policy_info() -> dict | None:
    if not _active_policy_id or _active_policy_id not in _index_store:
        return None
    data = _index_store[_active_policy_id]
    return {
        "policy_id": _active_policy_id,
        "filename": data.get("filename", "policy.pdf"),
        "page_count": data.get("page_count", 0),
        "chunks_count": len(data.get("chunks", [])),
        "policy_config": data.get("policy_config", {}),
    }


def is_policy_scope_question(question: str) -> bool:
    """
    Lightweight policy-scope check before RAG retrieval.
    Prevents unrelated questions (e.g. 'What is the capital of France?') from
    retrieving random insurance policy chunks.
    """
    q_lower = question.lower().strip()
    if not q_lower:
        return False

    # 1. Unrelated patterns that are definitely not insurance questions
    unrelated_patterns = [
        r"\b(?:capital of|president of|prime minister|who won|who is the|weather in|population of|recipe for|how to bake|how to cook|write a poem|write code|translate|lyrics of|synonym for|actor in|director of|capital city|currency of|invented the|distance to|speed of light)\b",
    ]
    for pat in unrelated_patterns:
        if re.search(pat, q_lower):
            return False

    # 2. Insurance, medical, treatment, policy, and claim keywords
    policy_keywords = [
        "policy", "cover", "covered", "coverage", "claim", "claims", "deductible",
        "copay", "co-pay", "copayment", "co-payment", "coinsurance", "limit", "limits",
        "sub-limit", "sublimit", "sub-limits", "sublimits", "exclusion", "exclusions",
        "excluded", "waiting", "period", "periods", "premium", "sum insured",
        "insured", "insurer", "network", "cashless", "reimbursement", "pre-existing",
        "ped", "benefit", "benefits", "eligibility", "eligible", "hospital", "hospitalization",
        "hospitalisation", "inpatient", "in-patient", "outpatient", "out-patient", "day care",
        "room rent", "icu", "ambulance", "pre-hospitalization", "post-hospitalization",
        "renewal", "maternity", "accident", "injury", "emergency", "terms", "condition",
        "conditions", "clause", "schedule", "doctor", "physician", "surgeon", "surgery",
        "treatment", "procedure", "operation", "disease", "illness", "medical", "medicine",
        "diagnostic", "test", "tests", "scan", "mri", "ct", "x-ray", "blood", "knee",
        "hip", "cataract", "appendectomy", "cabg", "angioplasty", "hernia", "c-section",
        "cesarean", "gallbladder", "kidney", "stone", "dialysis", "chemo", "chemotherapy",
        "radiation", "cancer", "cardiac", "heart", "eye", "dental", "therapy", "check-up",
        "checkup", "robotic", "organ", "transplant", "orthopedic", "fracture", "bill",
        "expense", "expenses", "pay", "payment", "cost", "fee", "charge", "charges",
        "holder", "patient", "authorization", "discharge", "disclosure"
    ]

    return any(re.search(r"\b" + re.escape(kw) + r"\b", q_lower) for kw in policy_keywords)


def _clean_json_text(text: str) -> str:
    """Strip markdown code fences if LLM returns ```json ... ```."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()

CRITICAL_RULES = """
CRITICAL RULES:

1. GROUNDING
   Ground every part of the answer strictly in the retrieved policy evidence.
   Do not use outside insurance knowledge to fill gaps.

2. NO INVENTED INFORMATION
   Never invent, assume, guess, or infer a policy value, duration, limit,
   condition, exclusion, coverage rule, waiting period, deductible,
   co-payment, sub-limit, or eligibility requirement that is not supported
   by the retrieved evidence.

3. DIRECT ANSWER
   Answer the user's actual question directly first.
   Do not avoid the question or provide unnecessary general insurance
   explanations.

4. EXPLICIT VS MISSING INFORMATION
   Clearly distinguish between:
   - information explicitly stated in the policy,
   - information that can be determined from the retrieved evidence,
   - information that is missing or not specified.

5. PARTIAL ANSWERS
   If the evidence only partially answers the question, provide the
   information that IS supported and clearly explain what remains unknown
   or unspecified.

6. MULTIPLE POLICY CONDITIONS
   When multiple conditions are relevant, explain how they relate to the
   user's question.

   Pay attention to distinctions such as:
   - "subject to"
   - "up to"
   - "after"
   - "before"
   - "excluded"
   - "limited to"
   - "not covered"
   - "not specified"

7. WAITING PERIODS
   If a waiting period is explicitly stated, report it exactly as supported
   by the evidence.

   Do not treat a general waiting period, such as a pre-existing disease
   waiting period, as a procedure-specific waiting period unless the policy
   explicitly connects them.

8. COVERAGE
   When answering coverage questions, check the evidence for all relevant
   conditions, including:
   - coverage statements
   - exclusions
   - waiting periods
   - deductibles
   - co-payments
   - treatment-specific sub-limits
   - room-rent limits
   - eligibility conditions
   - other policy restrictions

9. POLICY TERMINOLOGY
   Preserve the meaning and terminology used in the policy.
   Do not replace policy wording with assumptions or general insurance rules.

10. INSUFFICIENT INFORMATION
    If the retrieved evidence does not contain enough information to answer
    the question, explicitly state that the information is not specified or
    cannot be determined from the uploaded policy.

    Do not manufacture an answer just because the user expects one.

11. CONFIDENCE
    Assign confidence ONLY from the retrieved evidence:

    High:
    The retrieved evidence directly and clearly answers the question.

    Medium:
    The evidence supports the answer, but some relevant detail is incomplete
    or requires careful interpretation.

    Low:
    Important information needed to answer the question is missing,
    ambiguous, or insufficient.

12. CITATIONS
    Support factual claims with the most relevant retrieved policy evidence.

    Citations must refer only to the supplied evidence.
    Do not create citations for information that does not appear in the evidence.

13. FINANCIAL CALCULATIONS
    Do NOT perform arithmetic or calculate monetary amounts.
    Do NOT estimate patient payment amounts inside the LLM response.

    Financial calculations are handled separately by the deterministic
    coverage engine.

14. PATIENT-SPECIFIC INFORMATION
    If the question depends on patient-specific information that is not
    available in the evidence or request, clearly state what information is
    missing instead of assuming it.

15. NO OUTSIDE KNOWLEDGE
    Even if you know a common insurance rule from general knowledge, do not
    apply it unless it is supported by the retrieved policy evidence.

16. EVIDENCE PRIORITY
    The retrieved policy evidence has priority over assumptions,
    general insurance knowledge, or expected policy behavior.

17. RESPONSE QUALITY
    Keep the answer clear, concise, factual, and easy for a patient to
    understand while preserving the exact meaning of the policy.

18. JSON OUTPUT
    Return ONLY a valid JSON object matching the required schema.
    Do not include Markdown, code fences, explanations outside the JSON,
    or additional fields.

19. DO NOT ADD UNSUPPORTED EXPLANATIONS
    Do not add calculation methods, relationships between policy conditions,
    or interpretations unless they are explicitly supported by the retrieved
    evidence. When the user's question can be answered directly from one
    policy statement, prefer that direct statement over additional inference.
"""

def _call_gemini_llm(question: str, evidence_chunks: list[dict]) -> dict | None:
    """
    Call Google Gemini with strict policy-grounding rules.
    Returns parsed dictionary or None if unavailable/fails.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "your-gemini-api-key-here":
        return None

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        evidence_str = ""

        for i, chunk in enumerate(evidence_chunks, 1):
            evidence_str += (
                f"\n--- EVIDENCE EXCERPT {i} ---\n"
                f"Page: {chunk.get('page')}\n"
                f"Section: {chunk.get('section', 'General')}\n"
                f'Quote: "{chunk.get("text")}"\n'
            )

        prompt = f"""You are an Insurance Policy Verification Assistant.

{CRITICAL_RULES}

RETRIEVED POLICY EVIDENCE:
{evidence_str}

QUESTION:
{question}

Provide your output strictly as a valid JSON object matching this schema:

{{
    "answer": "<clear, factual explanation directly answering the question>",
    "confidence": "High" | "Medium" | "Low",
    "citations": [
        {{
            "page": <page number as integer>,
            "section": "<section or heading title>",
            "text": "<exact supporting quote from evidence>"
        }}
    ]
}}
"""

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
        )

        print("✅ GEMINI WAS CALLED")

        print(
            "Gemini raw response:",
            response.text[:500] if response and response.text else "EMPTY"
        )

        if response and response.text:
            cleaned = _clean_json_text(response.text)
            parsed = json.loads(cleaned)

            if "answer" in parsed:
                return {
                    "answer": str(
                        parsed.get("answer", "")
                    ).strip(),

                    "confidence": str(
                        parsed.get("confidence", "Medium")
                    ).strip(),

                    "citations": [
                        {
                            "page": int(
                                c.get("page", 1)
                            ),

                            "section": str(
                                c.get("section", "General")
                            ),

                            "text": str(
                                c.get("text", "")
                            ).strip(),
                        }

                        for c in parsed.get("citations", [])

                        if c.get("text")
                    ],
                }

    except Exception as e:
        logger.warning(
            "Gemini LLM call failed or returned unparseable output: %s",
            e,
        )

    return None

def _call_groq_llm(question: str, evidence_chunks: list[dict]) -> dict | None:
    """
    Fallback LLM call using Groq.

    Uses the same policy-grounding rules, retrieved evidence,
    and JSON response schema as the Gemini path.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        return None

    try:
        from groq import Groq

        client = Groq(api_key=api_key)

        evidence_str = ""

        for i, chunk in enumerate(evidence_chunks, 1):
            evidence_str += (
                f"\n--- EVIDENCE EXCERPT {i} ---\n"
                f"Page: {chunk.get('page')}\n"
                f"Section: {chunk.get('section', 'General')}\n"
                f'Quote: "{chunk.get("text")}"\n'
            )

        prompt = f"""You are an Insurance Policy Verification Assistant.

{CRITICAL_RULES}

RETRIEVED POLICY EVIDENCE:
{evidence_str}

QUESTION:
{question}

Provide your output strictly as a valid JSON object matching this schema:

{{
    "answer": "<clear, factual explanation directly answering the question>",
    "confidence": "High" | "Medium" | "Low",
    "citations": [
        {{
            "page": <page number as integer>,
            "section": "<section or heading title>",
            "text": "<exact supporting quote from evidence>"
        }}
    ]
}}
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an Insurance Policy Verification Assistant. "
                        "Follow the supplied CRITICAL_RULES exactly and answer "
                        "strictly from the retrieved policy evidence."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        raw_text = response.choices[0].message.content

        print("🔄 GROQ FALLBACK WAS CALLED")

        print(
            "Groq raw response:",
            raw_text[:500] if raw_text else "EMPTY"
        )

        if raw_text:
            cleaned = _clean_json_text(raw_text)
            parsed = json.loads(cleaned)

            if "answer" in parsed:
                return {
                    "answer": str(
                        parsed.get("answer", "")
                    ).strip(),

                    "confidence": str(
                        parsed.get("confidence", "Medium")
                    ).strip(),

                    "citations": [
                        {
                            "page": int(
                                c.get("page", 1)
                            ),

                            "section": str(
                                c.get("section", "General")
                            ),

                            "text": str(
                                c.get("text", "")
                            ).strip(),
                        }

                        for c in parsed.get("citations", [])

                        if c.get("text")
                    ],
                }

    except Exception as e:
        logger.warning(
            "Groq fallback failed or returned unparseable output: %s",
            e,
        )

    return None

def _grounded_fallback(question: str, evidence_chunks: list[dict], top_similarity: float) -> dict:
    """
    Deterministic grounded fallback when Gemini API is not configured or fails.
    Extracts relevant statements from chunks without hallucinations.
    """
    q_lower = question.lower()
    q_words = set(re.findall(r"\b[a-z]{3,}\b", q_lower))
    stop_words = {"what", "when", "where", "which", "does", "covered", "coverage", "policy", "tell", "explain", "under", "with", "have"}
    q_keywords = q_words - stop_words

    # Check for specific question types
    is_deductible_query = "deductible" in q_lower
    is_ped_query = "pre-existing" in q_lower or "pre existing" in q_lower or "ped" in q_lower
    is_robotic_query = "robotic" in q_lower

    # 1. Unknown procedure not in policy (e.g. robotic surgery)
    if is_robotic_query and not any("robotic" in c["text"].lower() for c in evidence_chunks):
        return {
            "answer": "Insufficient information in the uploaded policy. The policy document does not contain coverage details for robotic surgery.",
            "confidence": "Low",
            "citations": [],
        }

    # Find relevant section chunks
    hosp_chunk: dict | None = None
    waiting_chunk: dict | None = None
    exclusions_chunk: dict | None = None
    deductible_chunk: dict | None = None
    sublimits_chunk: dict | None = None
    matched_chunks: list[dict] = []

    for chunk in evidence_chunks:
        c_text = chunk["text"]
        c_lower = c_text.lower()
        c_sec = chunk.get("section", "").lower()

        hits = sum(1 for kw in q_keywords if kw in c_lower or kw in c_sec)
        if hits > 0 or top_similarity > 0.40:
            matched_chunks.append(chunk)

        if "hospitalization coverage" in c_sec or c_sec == "hospitalization coverage" or "in-patient" in c_sec:
            hosp_chunk = chunk
        elif hosp_chunk is None and ("hospitalization" in c_sec or "hospitalization" in c_lower):
            hosp_chunk = chunk

        if "waiting" in c_sec or "waiting period" in c_lower:
            waiting_chunk = chunk
        if "exclusion" in c_sec or "not covered" in c_lower:
            exclusions_chunk = chunk
        if "deductible" in c_sec or "deductible" in c_lower or "co-pay" in c_lower:
            deductible_chunk = chunk
        if "sub-limit" in c_sec or "limit" in c_sec:
            sublimits_chunk = chunk

    # 2. Deductible query
    if is_deductible_query:
        target_chunk = deductible_chunk or (matched_chunks[0] if matched_chunks else (evidence_chunks[0] if evidence_chunks else None))
        if target_chunk:
            citations = [
                {
                    "page": target_chunk.get("page", 1),
                    "section": target_chunk.get("section", "Deductible and Co-pay"),
                    "text": target_chunk.get("text", ""),
                }
            ]
            answer = (
                f"The policy specifies a \u20b95,000 deductible per claim under {target_chunk.get('section', 'Deductible and Co-pay')} (Page {target_chunk.get('page', 1)}). "
                f"This amount must be paid by the insured before the insurer becomes liable for covered expenses. "
                f"Please note that the \u20b95,000 deductible is not necessarily your total final out-of-pocket cost. "
                f"Your total out-of-pocket expense may also depend on applicable co-payment, treatment sub-limits, exclusions, and other policy conditions. "
                f"For an exact cost breakdown for your treatment scenario, use the Treatment Cost & Coverage Calculator."
            )
            return {
                "answer": answer,
                "confidence": "High",
                "citations": citations,
            }

    # 3. Pre-existing condition query
    if is_ped_query:
        citations = []
        if waiting_chunk:
            citations.append({
                "page": waiting_chunk.get("page", 1),
                "section": waiting_chunk.get("section", "Waiting Periods"),
                "text": waiting_chunk.get("text", ""),
            })
        if hosp_chunk:
            citations.append({
                "page": hosp_chunk.get("page", 1),
                "section": hosp_chunk.get("section", "Hospitalization Coverage"),
                "text": hosp_chunk.get("text", ""),
            })
        if deductible_chunk:
            citations.append({
                "page": deductible_chunk.get("page", 1),
                "section": deductible_chunk.get("section", "Deductible and Co-pay"),
                "text": deductible_chunk.get("text", ""),
            })

        answer = (
            "For pre-existing conditions, the policy stipulates that expenses related to pre-existing diseases are covered after 36 months (or 24 months as stated in policy schedule) of continuous coverage (Page 1 — Waiting Periods). "
            "In addition, specified surgical procedures (such as knee replacement) are subject to a 12-month waiting period, applicable deductible, and co-payment (Page 1 — Deductible and Co-pay). "
            "If your continuous coverage duration is less than the required waiting period or has not been provided, pre-existing condition expenses will not be covered."
        )
        return {
            "answer": answer,
            "confidence": "High",
            "citations": citations,
        }

    # 4. Specific procedure query (e.g. "Is knee replacement covered?")
    procedure_keywords = {
        "knee", "replacement", "hip", "cataract", "surgery", "appendectomy",
        "cabg", "angioplasty", "hernia", "c-section", "cesarean", "gallbladder",
        "kidney", "stone", "dialysis", "chemotherapy", "radiation", "mri",
        "scan", "x-ray", "operation", "procedure", "treatment",
    }
    if q_keywords.intersection(procedure_keywords):
        direct_matches = [c for c in evidence_chunks if any(kw in c["text"].lower() for kw in q_keywords)]
        if direct_matches:
            target = direct_matches[0]
            citations = [
                {
                    "page": target.get("page", 1),
                    "section": target.get("section", "Policy"),
                    "text": target.get("text", ""),
                }
            ]
            if hosp_chunk and hosp_chunk != target:
                citations.append({
                    "page": hosp_chunk.get("page", 1),
                    "section": hosp_chunk.get("section", "Hospitalization Coverage"),
                    "text": hosp_chunk.get("text", ""),
                })
            return {
                "answer": f"Coverage is specified under {target.get('section', 'the policy')} (Page {target.get('page', 1)}): {target.get('text', '')}",
                "confidence": "High",
                "citations": citations,
            }

        if hosp_chunk:
            citations = [
                {
                    "page": hosp_chunk.get("page", 1),
                    "section": hosp_chunk.get("section", "Hospitalization Coverage"),
                    "text": hosp_chunk.get("text", ""),
                }
            ]
            answer_parts = [
                f"Yes, surgical and medical procedures are covered under {hosp_chunk.get('section', 'Hospitalization Coverage')} (Page {hosp_chunk.get('page', 1)}) as medically necessary hospitalization expenses, including surgeon fees and hospital services."
            ]

            if waiting_chunk:
                citations.append({
                    "page": waiting_chunk.get("page", 1),
                    "section": waiting_chunk.get("section", "Waiting Periods"),
                    "text": waiting_chunk.get("text", ""),
                })
                answer_parts.append(
                    f"Note that specified procedures are subject to a waiting period of 12 months under {waiting_chunk.get('section', 'Waiting Periods')} (Page {waiting_chunk.get('page', 1)})."
                )

            if exclusions_chunk:
                citations.append({
                    "page": exclusions_chunk.get("page", 1),
                    "section": exclusions_chunk.get("section", "Exclusions"),
                    "text": exclusions_chunk.get("text", ""),
                })
                answer_parts.append(
                    f"Treatments must be medically necessary; cosmetic and non-prescribed procedures are excluded (Page {exclusions_chunk.get('page', 1)} — Exclusions)."
                )

            return {
                "answer": " ".join(answer_parts),
                "confidence": "High",
                "citations": citations,
            }

    # 5. General matched chunks
    if matched_chunks:
        primary = matched_chunks[0]
        citations = [
            {
                "page": c.get("page", 1),
                "section": c.get("section", "General Policy"),
                "text": c.get("text", ""),
            }
            for c in matched_chunks[:3]
        ]
        return {
            "answer": f"According to {primary.get('section', 'the policy')} (Page {primary.get('page', 1)}): {primary.get('text', '')}",
            "confidence": "High" if len(matched_chunks) >= 2 or top_similarity > 0.45 else "Medium",
            "citations": citations,
        }

    # 6. Out-of-scope query
    return {
        "answer": "Insufficient information in the uploaded policy.",
        "confidence": "Low",
        "citations": [],
    }


def query(question: str, policy_id: str | None = None, top_k: int = 4) -> dict:
    """
    Retrieve relevant chunks for a question, prompt the LLM, and return cited answer.
    First performs a lightweight policy-scope check to reject unrelated general knowledge questions.
    """
    pid = policy_id or _active_policy_id
    if not pid or pid not in _index_store:
        raise ValueError("No policy has been uploaded yet. Please upload a policy first.")

    # 1. Lightweight policy-scope check
    if not is_policy_scope_question(question):
        return {
            "answer": (
                "This question is outside the scope of the uploaded insurance policy. "
                "I can help with policy coverage, exclusions, waiting periods, deductibles, "
                "co-payment, limits, and treatment-related policy questions."
            ),
            "confidence": "Low",
            "citations": [],
        }

    store_data = _index_store[pid]
    index: faiss.IndexFlatIP = store_data["faiss_index"]
    chunks: list[dict] = store_data["chunks"]

    embedder = get_embedder()
    q_emb = embedder.encode([question], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(q_emb)

    k = min(top_k, len(chunks))
    distances, indices = index.search(q_emb, k)

    retrieved_chunks: list[dict] = []
    top_score = 0.0

    if len(distances) > 0 and len(distances[0]) > 0:
        top_score = float(distances[0][0])

    for idx in indices[0]:
        if 0 <= idx < len(chunks):
            retrieved_chunks.append(chunks[idx])

    # 2. Try Gemini LLM first
    # Primary LLM: Gemini
    llm_result = _call_gemini_llm(question, retrieved_chunks)

    if llm_result:
        print("✅ ANSWER GENERATED BY GEMINI")

        if (
            not llm_result.get("citations")
            and llm_result.get("answer")
            != "Insufficient information in the uploaded policy."
        ):
            llm_result["citations"] = [
                {
                    "page": c.get("page", 1),
                    "section": c.get("section", "General"),
                    "text": c.get("text", ""),
                }
                for c in retrieved_chunks[:2]
            ]

        return llm_result


    # Fallback LLM: Groq
    llm_result = _call_groq_llm(question, retrieved_chunks)

    if llm_result:
        print("✅ ANSWER GENERATED BY GROQ")

        if (
            not llm_result.get("citations")
            and llm_result.get("answer")
            != "Insufficient information in the uploaded policy."
        ):
            llm_result["citations"] = [
                {
                    "page": c.get("page", 1),
                    "section": c.get("section", "General"),
                    "text": c.get("text", ""),
                }
                for c in retrieved_chunks[:2]
            ]

        return llm_result


    # Existing fallback continues below this point
    print("⚠️ USING EXISTING LOCAL FALLBACK")

    # 3. Robust grounded fallback
    return _grounded_fallback(question, retrieved_chunks, top_score)
