import os
import re
import json
import pdfplumber
from google import genai

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from an uploaded PDF file."""
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def process_paper(pdf_file, api_key: str) -> tuple[str, str]:
    """Process the entire paper and return the 3-part summary and full text."""
    client = genai.Client(api_key=api_key)
    
    # 1. Extract Full Text
    full_text = extract_text_from_pdf(pdf_file)
    if not full_text.strip():
        raise ValueError("Could not extract any text from the PDF. It may be scanned or empty.")
    
    # Notice: We removed the Map-Reduce chunking. Gemini 1.5 Pro has a 2 Million token 
    # context window. Research papers are typically ~20,000 tokens, so we can effortlessly 
    # pass the entire Document in a SINGLE API request. This completely avoids 
    # exhausting the 15 Requests/Min Free Tier limit.
    final_prompt = f"""You are an expert academic assistant.

Summarize the following research paper context into:
1. Abstract (5–7 lines)
2. Key Points (bullet points)
3. Conclusion (brief)

Make the explanation simple and easy to understand for students.
Avoid complex jargon and focus on clarity.

Here is the unstructured content of the paper:
{full_text}

Format the output clearly separating the three sections."""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=final_prompt
    )
    return response.text, full_text

def analyze_summary(summary: str, api_key: str) -> str:
    """Provides a deeper structured analysis of the summary."""
    client = genai.Client(api_key=api_key)
    prompt = f"""You are an expert research analyst.

Analyze the following research paper summary and provide:

1. Main Problem
2. Proposed Solution
3. Key Strengths (bullet points)
4. Limitations (bullet points)
5. Real-world Applications

Keep it simple and easy to understand.

Summary:
{summary}
"""
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

def chat_with_paper(full_text: str, question: str, api_key: str) -> str:
    """Answers a question based solely on the provided full paper context."""
    client = genai.Client(api_key=api_key)
    prompt = f"""You are an intelligent research assistant.

Based on the research paper text below, answer the user's question.

Instructions:
- Keep answer clear and concise (3–5 lines)
- Do not make up information
- If answer is not present, say:
  'This information is not clearly mentioned in the paper.'

Paper Text:
{full_text}

Question:
{question}

Answer:"""
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

def generate_knowledge_graph(full_text: str, api_key: str) -> str:
    """Generates a clean Mermaid flowchart from the paper."""
    client = genai.Client(api_key=api_key)
    prompt = f"""You are an expert knowledge extractor.
Create a clean, logical flowchart mapping out the following research paper context.

Instructions:
1. Identify the core narrative: Main Problem -> Proposed Solution -> Key Methods -> Results -> Conclusion.
2. Return ONLY a valid Mermaid.js flowchart syntax (starting with `graph TD;`).
3. Keep node labels brief and readable.
4. CRITICAL: You MUST wrap all node text in double quotes to prevent Mermaid syntax errors. 
   Example: A["Main Problem: Text"] --> B("Proposed Solution: Text")
5. Do NOT use any special characters like quotes or brackets INSIDE the text labels.
6. Example format:
graph TD;
    A["Main Problem"] --> B("Proposed Solution");
    B --> C{{"Methods"}};
    C --> D["Result 1"];
    C --> E["Result 2"];

Do NOT wrap the output in markdown code blocks. Just output the raw Mermaid code starting with `graph TD;` (or LR).

Paper Text:
{full_text}
"""
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    # Clean up response in case it returns markdown
    raw_text = response.text.strip()
    if raw_text.startswith("```mermaid"):
        raw_text = raw_text[10:]
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
        
    return raw_text.strip()


def extract_important_sentences(full_text: str, top_n: int = 6) -> list[str]:
    """
    A*-inspired heuristic sentence extraction (runs locally, no API calls).
    
    Scores each sentence using:
        f(n) = g(n) + h(n)
    where:
        g(n) = position-based score (earlier sentences get a slight boost)
        h(n) = importance score (keyword presence + optimal length bonus)
    
    Returns the top_n highest-scoring sentences.
    """
    
    # --- Important academic keywords grouped by relevance ---
    KEYWORDS = [
        "propose", "proposed", "method", "approach", "technique",
        "result", "results", "finding", "findings",
        "conclusion", "conclusions", "demonstrate", "demonstrated",
        "significant", "significantly", "improve", "improvement",
        "novel", "framework", "model", "algorithm",
        "performance", "accuracy", "evaluate", "evaluation",
        "contribute", "contribution", "objective", "hypothesis",
        "experiment", "experimental", "analysis", "achieve", "achieved",
        "outperform", "state-of-the-art", "benchmark"
    ]
    
    # --- Step 1: Split text into sentences ---
    # Use regex to split on sentence-ending punctuation followed by whitespace
    raw_sentences = re.split(r'(?<=[.!?])\s+', full_text.strip())
    
    # --- Step 2: Clean and filter sentences ---
    sentences = []
    for s in raw_sentences:
        cleaned = s.strip().replace("\n", " ")
        # Remove multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        # Keep only sentences with a reasonable length (10-300 words)
        word_count = len(cleaned.split())
        if 10 <= word_count <= 300:
            sentences.append(cleaned)
    
    if not sentences:
        return []
    
    total = len(sentences)
    scored_sentences = []
    
    for i, sentence in enumerate(sentences):
        words = sentence.lower().split()
        word_count = len(words)
        
        # --- g(n): Position-based score ---
        # Earlier sentences (intro, abstract) and late sentences (conclusion)
        # get a higher positional score. Middle sentences get less.
        position_ratio = i / total  # 0.0 = very start, 1.0 = very end
        if position_ratio < 0.15:
            g_score = 3.0  # Abstract / Introduction
        elif position_ratio > 0.85:
            g_score = 2.5  # Conclusion
        elif position_ratio < 0.3:
            g_score = 1.5  # Early body
        else:
            g_score = 1.0  # Middle body
        
        # --- h(n): Importance heuristic ---
        
        # Keyword match count (each keyword found adds to the score)
        keyword_hits = sum(1 for kw in KEYWORDS if kw in words)
        keyword_score = min(keyword_hits * 1.5, 8.0)  # Cap at 8.0
        
        # Length bonus: prefer moderate-length sentences (20-60 words)
        if 20 <= word_count <= 60:
            length_score = 2.0
        elif 15 <= word_count <= 80:
            length_score = 1.0
        else:
            length_score = 0.5
        
        h_score = keyword_score + length_score
        
        # --- f(n) = g(n) + h(n) ---
        f_score = g_score + h_score
        
        scored_sentences.append((f_score, i, sentence))
    
    # --- Step 3: Rank by f(n) descending and pick top_n ---
    scored_sentences.sort(key=lambda x: x[0], reverse=True)
    
    # Select top_n, then re-sort by original position for reading order
    top_sentences = scored_sentences[:top_n]
    top_sentences.sort(key=lambda x: x[1])  # Sort by original index
    
    return [s[2] for s in top_sentences]
