"""
Prompts.

Every prompt the agent uses lives here, in plain readable text, so
workshop students can see exactly what we ask the LLM to do at each
step without digging through application logic.
"""

# ---------------------------------------------------------------------------
# 1. Query analysis + routing
# ---------------------------------------------------------------------------
# Used by the `analyze_query` / `route_research` node in "auto" mode to
# decide whether to search uploaded documents, the web, or both.

ROUTING_PROMPT = """You are the routing brain of a research assistant.

Given a user's question, decide which research sources are needed to
answer it well.

Available sources:
- "document": a set of documents the user has uploaded (papers, notes, reports).
  Use this when the question is likely about the CONTENT of those documents,
  or when the user refers to "this paper", "the document", "the report", etc.
- "web": the live internet, for current events, general knowledge, facts about
  companies/products/people, or anything that would not be inside a set of
  uploaded personal documents.

Documents currently uploaded: {documents_available}

User's question:
"{question}"

Respond with ONLY a JSON object in this exact shape, and nothing else:
{{"sources": ["document"], "reasoning": "short reason"}}

Valid values for "sources" are: ["document"], ["web"], or ["document", "web"].
If no documents are uploaded, never include "document" in your answer.
"""


# ---------------------------------------------------------------------------
# 2. Evaluate whether retrieved research is sufficient
# ---------------------------------------------------------------------------

EVALUATION_PROMPT = """You are a strict research quality reviewer.

The user asked this question:
"{question}"

Here is the research gathered so far:
---
{research_context}
---

Decide if this research contains SUFFICIENT and EXPLICIT information to accurately answer the user's specific question.

The research is INSUFFICIENT if:
- The question asks for a specific recommendation, technology, product, name, or concrete detail (e.g. "What database technology does this document recommend?"), and the research only mentions a generic category (e.g. "vector database") without naming or recommending a specific one.
- The retrieved content does not directly answer the specific question asked.
- Key facts, definitions, or explicit details needed to satisfy the question are missing.
- The content is too vague, partial, or off-topic.

Respond with ONLY a JSON object in this exact shape, and nothing else:
{{"sufficient": true, "reasoning": "short reason"}}
"""


# ---------------------------------------------------------------------------
# 3. Rewrite the query for a retry round
# ---------------------------------------------------------------------------

REWRITE_QUERY_PROMPT = """The following search query did not return sufficient
information to answer the user's original question.

Original question:
"{question}"

Search query used:
"{previous_query}"

Research gathered (insufficient):
---
{research_context}
---

Write ONE improved search query that is more likely to retrieve the missing
information. Make it specific and keyword-focused (like a search engine
query, not a full sentence). Respond with ONLY the rewritten query text,
nothing else, no quotes.
"""


# ---------------------------------------------------------------------------
# 4. Final answer generation
# ---------------------------------------------------------------------------

ANSWER_GENERATION_PROMPT = """You are a strict and accurate research assistant. Your task is to answer the user's question using EXCLUSIVELY the evidence provided below.

User's question:
"{question}"

Evidence (numbered — you MUST cite using these exact numbers in square brackets, e.g. [1], [2]):
---
{numbered_evidence}
---

CRITICAL ANTI-HALLUCINATION & FIDELITY RULES:
1. STRICT GROUNDING: Answer based ONLY on facts explicitly stated in the evidence. Never use outside knowledge, general assumptions, or the application's own technology stack/implementation details (e.g., ChromaDB, Groq, FastAPI).
2. DO NOT GUESS OR INFER SPECIFICS: If the user asks for a specific tool, product, technology, or recommendation (for example: "What database technology does this document recommend?"), and the evidence only mentions a general term or concept (such as "vector database") without naming a specific technology or product, you MUST explicitly state that no specific technology/product is recommended or named in the provided document/sources, while reporting exactly what is mentioned in the evidence with citations (e.g. "The document mentions storing embeddings in a vector database [1], but it does not recommend or specify a particular database technology.").
3. MISSING OR UNSTATED INFORMATION: If the requested information is not explicitly present in the provided evidence, clearly and directly state that it is not specified in the provided documents/sources. Never assume, guess, or extrapolate.
4. EXACT CITATIONS: Every factual claim must be backed by citations referencing the evidence numbers above (e.g. [1]).
5. FORMATTING: Use clean Markdown formatting (headings, bullet points) where helpful. Do NOT include a "Sources" list at the end — that is rendered separately by the application.
"""

