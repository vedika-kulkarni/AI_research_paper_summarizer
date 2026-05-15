# AI Research Paper Summarizer 📄

An intelligent Streamlit web application that transforms lengthy, complex research papers (PDFs) into digestible summaries, interactive flowcharts, and AI-powered insights.

## ✨ Features

- **Instant Summarization** — Distills entire papers into abstracts, key points, and conclusions in seconds.
- **AI Analysis** — Digs deeper into the main problem, proposed solutions, strengths, limitations, and real-world applications.
- **Chat with Paper** — An interactive Q&A chatbot powered by the full context of your uploaded paper.
- **Interactive Flowchart** — Dynamically maps the paper's core structure into a draggable, zoomable Mermaid.js flowchart.
- **PDF Exports** — Download summaries, analysis reports, and flowcharts as PDF files for offline use.
- **📌 Important Sentences (A\*-inspired)** — Extracts the most critical sentences from the paper using a local heuristic scoring algorithm inspired by the A\* search strategy. Runs instantly with zero API calls.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- A free [Google Gemini API Key](https://aistudio.google.com/app/apikey)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SID-2006/AI-Research-Paper-Summarizer.git
   cd AI-Research-Paper-Summarizer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the project root and add your API key:
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```
   > ⚠️ This step is mandatory. The app will not work without a valid API key.

4. **Run the app:**
   ```bash
   streamlit run app.py
   ```

5. Open your browser at `http://localhost:8501` and start uploading papers!

## 🔍 How A* Search is Used

One of the unique features of this project is an **Important Sentences Extractor** that uses a heuristic scoring method inspired by the **A\* search algorithm**. Unlike the other AI-powered features, this one runs **entirely locally in Python** with no API calls, making it blazing fast.

### The A* Analogy

In classical A\*, the algorithm finds the optimal path by evaluating nodes using:

```
f(n) = g(n) + h(n)
```

We adapt this concept to **sentence selection** in a research paper:

| Component | Classical A\* | Our Adaptation |
|-----------|--------------|----------------|
| **Node** | A point on a graph | A sentence in the paper |
| **g(n)** | Cost from start to node | **Position-based score** — sentences in the abstract/intro (top 15%) and conclusion (bottom 15%) are weighted higher |
| **h(n)** | Estimated cost to goal | **Importance heuristic** — keyword relevance + optimal sentence length |
| **f(n)** | Total estimated cost | **Final importance score** — used to rank and select top sentences |

### Scoring Breakdown

**g(n) — Position Score:**
- Abstract / Introduction region (first 15%): `3.0`
- Conclusion region (last 15%): `2.5`
- Early body (15–30%): `1.5`
- Middle body: `1.0`

**h(n) — Importance Heuristic:**
- **Keyword matching**: Each match against 35+ academic keywords (`"propose"`, `"novel"`, `"result"`, `"framework"`, `"conclusion"`, etc.) adds `1.5` to the score (capped at `8.0`)
- **Length bonus**: Sentences with 20–60 words (ideal readability) get `2.0`; 15–80 words get `1.0`; others get `0.5`

**Final ranking:**
- All sentences are scored with `f(n) = g(n) + h(n)`
- Top 6 sentences are selected
- They are re-sorted into their original reading order for coherent output

## 🛠️ Built With

- [Streamlit](https://streamlit.io/) — Frontend framework
- [Google Gemini API](https://ai.google.dev/) — AI summarization & analysis
- [pdfplumber](https://github.com/jsvine/pdfplumber) — PDF text extraction
- [Mermaid.js](https://mermaid.js.org/) — Flowchart rendering
- [html2pdf.js](https://ekoopmans.github.io/html2pdf.js/) — Client-side PDF generation