import streamlit as st
import os
from dotenv import load_dotenv
from summarizer import process_paper, analyze_summary, chat_with_paper, generate_knowledge_graph, extract_important_sentences
import markdown
from fpdf import FPDF
from io import BytesIO
import streamlit.components.v1 as components

load_dotenv()

st.set_page_config(
    page_title="Refined AI Summarizer",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def generate_pdf_from_md(md_text):
    # Convert Markdown to HTML, stripping emojis for safer PDF font rendering
    clean_text = md_text.encode("ascii", "ignore").decode("ascii")
    html = markdown.markdown(clean_text, extensions=['extra'])
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    try:
        pdf.write_html(html)
    except Exception as e:
        pdf.set_font("Helvetica", size=12)
        pdf.cell(200, 10, txt="Error generating PDF content.", ln=True)
        
    return bytes(pdf.output())

# Inject Custom CSS for Premium Design
st.markdown(
    """
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    /* Global Typography Customization */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    /* Hero Title Restyled */
    .hero-title {
        color: #E63946 !important;
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        text-align: center;
        padding-bottom: 0px;
        margin-bottom: 0px;
    }

    /* Subtitle Customization */
    .hero-subtitle {
        text-align: center;
        color: #888;
        font-size: 1.2rem;
        font-weight: 300;
        margin-top: -5px;
        margin-bottom: 40px;
    }
    
    /* Make the block quotes (often used in abstract/summaries) look better */
    blockquote {
        border-left: 4px solid #C238FF !important;
        padding-left: 15px !important;
        color: #555 !important;
        background: rgba(194, 56, 255, 0.05);
        padding: 10px;
        border-radius: 4px;
    }

    /* Increase visual weight of headers in summaries */
    h2, h3 {
        color: #2C3E50 !important;
    }
    
    /* Center Streamlit buttons in their columns */
    div.stButton > button {
        display: block;
        margin: 0 auto;
        border-radius: 20px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    /* File uploader hover padding (glassmorphic tweak) */
    div[data-testid="stFileUploader"] {
        background: rgba(0, 0, 0, 0.02);
        border: 1px dashed rgba(0, 0, 0, 0.2);
        border-radius: 12px;
        padding: 20px;
        transition: all 0.3s ease;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #C238FF;
        background: rgba(194, 56, 255, 0.05);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header Section
st.markdown('<h1 class="hero-title">AI Research Paper Summarizer 📄</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Upload complex research papers and unlock simplified, actionable insights in seconds.</p>', unsafe_allow_html=True)


# Main Application Layout
api_key_input = os.getenv("GOOGLE_API_KEY", "")

# Center the uploader using columns
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    uploaded_file = st.file_uploader("Drop your PDF Here", type=["pdf"], label_visibility="collapsed")
    
    if uploaded_file is None:
        st.write("")
        st.markdown("---")
        st.markdown("### About the Summarizer")
        st.markdown("This tool transforms lengthy, complex PDFs into digestible summaries with abstracts, key points, and conclusions.")
        
        st.markdown("### ✨ Key Features")
        st.markdown("- **Instant Summarization**: Distills entire papers into abstracts, key points, and conclusions in seconds.")
        st.markdown("- **AI Analysis**: Digs deeper into the main problem, proposed solutions, strengths, and real-world implications.")
        st.markdown("- **Chat with Paper**: An active Q&A chatbot powered by the context of your specific research paper.")
        st.markdown("- **Interactive Flowcharts**: Dynamically maps out the paper's architecture into a draggable, zoomable flowchart.")
        st.markdown("- **PDF Exports**: Download your summaries, analysis reports, and flowcharts instantly for offline use.")
        
        st.markdown("### Instructions")
        st.markdown("1. Upload a valid PDF file in the main area.\n2. Click **Summarize Paper**.\n3. Wait for the magic to happen 🪄.\n4. Explore the *Dive Deeper* tools and download your results!")

if "summary" not in st.session_state:
    st.session_state.summary = None
if "full_text" not in st.session_state:
    st.session_state.full_text = None
if "active_feature" not in st.session_state:
    st.session_state.active_feature = None
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "graph_data" not in st.session_state:
    st.session_state.graph_data = None

if uploaded_file is not None:
    # Action area
    st.write("") # Spacer
    col_btn_1, col_btn_2, col_btn_3 = st.columns([1, 1, 1])
    with col_btn_2:
        summarize_button = st.button("Summarize Paper", type="primary", use_container_width=True)
    
    if summarize_button:
        if not api_key_input:
            st.error("Configuration Error: Missing API Key in `.env`")
        else:
            with st.spinner("🧠 Scanning document and distilling insights..."):
                try:
                    # Reset memory
                    st.session_state.summary = None
                    st.session_state.full_text = None
                    st.session_state.active_feature = None
                    st.session_state.analysis_result = None
                    st.session_state.chat_history = []
                    st.session_state.graph_data = None
                    
                    final_summary, full_text = process_paper(uploaded_file, api_key_input)
                    st.session_state.summary = final_summary
                    st.session_state.full_text = full_text
                    st.toast('Summary generated successfully!', icon='🚀')
                except ValueError as ve:
                    st.error(f"Error reading PDF: {ve}")
                except Exception as e:
                    st.error(f"An error occurred during processing: {e}")

# Display results
if st.session_state.summary:
    st.markdown("---")
    st.markdown("### ✨ Key Insights")
    
    # Place result inside a nice native bordered container
    with st.container(border=True):
        st.markdown(st.session_state.summary)
    
    st.write("") # Spacer

    col_dl_1, col_dl_2, col_dl_3 = st.columns([1, 1, 1])
    with col_dl_2:
        pdf_bytes = generate_pdf_from_md(st.session_state.summary)
        st.download_button(
            label="Download Summary (PDF) 📥",
            data=pdf_bytes,
            file_name="paper_summary.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

    # --- A*-Inspired Important Sentences ---
    st.markdown("---")
    st.markdown("### 📌 Important Sentences (A*-inspired)")
    
    if st.session_state.full_text:
        important = extract_important_sentences(st.session_state.full_text, top_n=6)
        if important:
            with st.container(border=True):
                for sentence in important:
                    st.markdown(f"- {sentence}")
        else:
            st.info("Could not extract important sentences from this document.")
    
    st.markdown("---")
    st.markdown("### Dive Deeper")
    
    col_feat1, col_feat2, col_feat3 = st.columns(3)
    with col_feat1:
        if st.button("🧠 Analyze Paper", use_container_width=True):
            st.session_state.active_feature = "analysis"
    with col_feat2:
        if st.button("💬 Chat with Paper", use_container_width=True):
            st.session_state.active_feature = "chat"
    with col_feat3:
        if st.button("📊 Flowchart", use_container_width=True):
            st.session_state.active_feature = "graph"
            
    if st.session_state.active_feature == "analysis":
        st.markdown("#### 🧠 AI Analysis")
        if not st.session_state.analysis_result:
            if not api_key_input:
                st.error("Missing API Key.")
            else:
                with st.spinner("Analyzing the summary..."):
                    try:
                        st.session_state.analysis_result = analyze_summary(st.session_state.summary, api_key_input)
                    except Exception as e:
                        st.error(f"Error during analysis: {e}")
        
        if st.session_state.analysis_result:
            with st.container(border=True):
                st.markdown(st.session_state.analysis_result)
                
            st.write("") # Spacer
            col_ad_1, col_ad_2, col_ad_3 = st.columns([1, 1, 1])
            with col_ad_2:
                analysis_pdf_bytes = generate_pdf_from_md(st.session_state.analysis_result)
                st.download_button(
                    label="Download Analysis (PDF) 📥",
                    data=analysis_pdf_bytes,
                    file_name="paper_analysis.pdf",
                    mime="application/pdf",
                    type="secondary",
                    use_container_width=True
                )

    elif st.session_state.active_feature == "chat":
        st.markdown("#### 💬 Chat with Paper")
        
        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        # Chat input box
        prompt = st.chat_input("Ask a question about the paper")
        if prompt:
            if not api_key_input:
                st.error("Missing API Key.")
            else:
                # Display user message instantly
                with st.chat_message("user"):
                    st.markdown(prompt)
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                
                # Show assistant response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            response = chat_with_paper(st.session_state.full_text, prompt, api_key_input)
                            st.markdown(response)
                            st.session_state.chat_history.append({"role": "assistant", "content": response})
                        except Exception as e:
                            st.error(f"Error answering question: {e}")

    elif st.session_state.active_feature == "graph":
        st.markdown("#### 📊 Flowchart")
        if not st.session_state.graph_data:
            if not api_key_input:
                st.error("Missing API Key.")
            else:
                with st.spinner("Mapping out core concepts into a flowchart..."):
                    try:
                        st.session_state.graph_data = generate_knowledge_graph(st.session_state.full_text, api_key_input)
                    except Exception as e:
                        st.error(f"Error generating flowchart: {e}")
        
        if st.session_state.graph_data:
            with st.container(border=True):
                # Clean up any potential markdown formatting the LLM might have left
                mermaid_code = st.session_state.graph_data
                
                # Render using Streamlit Components so we don't need Graphviz binaries installed on Windows
                components.html(
                    f"""
                    <style>
                        body {{
                            margin: 0;
                            background-color: #FFFFFF;
                            color: #333333;
                            font-family: sans-serif;
                            overflow: hidden;
                        }}
                        #controls {{
                            position: fixed;
                            bottom: 20px;
                            right: 20px;
                            z-index: 1000;
                            background: rgba(30, 30, 30, 0.8);
                            padding: 10px;
                            border-radius: 8px;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                            display: flex;
                            gap: 10px;
                        }}
                        #controls button {{
                            background: #C238FF;
                            color: white;
                            border: none;
                            padding: 8px 15px;
                            border-radius: 5px;
                            font-weight: bold;
                            cursor: pointer;
                        }}
                        #controls button:hover {{
                            background: #a920e3;
                        }}
                        #pdf-button {{
                            background: #FF6B6B !important;
                        }}
                        #pdf-button:hover {{
                            background: #e55a5a !important;
                        }}
                        #zoom-container {{
                            width: 100vw;
                            height: 100vh;
                            cursor: grab;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                        }}
                        #zoom-container:active {{
                            cursor: grabbing;
                        }}
                        #panzoom-element {{
                            width: 100%;
                            height: 100%;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                        }}
                        .mermaid svg {{
                            max-width: none !important;
                            height: auto;
                            min-width: 1200px;
                        }}
                    </style>
                    
                    <div id="controls">
                        <button id="zoomIn">➕ Zoom In</button>
                        <button id="zoomOut">➖ Zoom Out</button>
                        <button id="resetZoom">🔄 Reset</button>
                        <button id="pdf-button" onclick="downloadPDF()">📥 PDF</button>
                    </div>
                    
                    <div id="zoom-container">
                        <div id="panzoom-element">
                            <pre class="mermaid" id="mermaid-graph" style="background-color: #FFFFFF; padding: 20px;">
                                {mermaid_code}
                            </pre>
                        </div>
                    </div>
                    
                    <script src="https://cdn.jsdelivr.net/npm/@panzoom/panzoom/dist/panzoom.min.js"></script>
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
                    
                    <script type="module">
                        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                        
                        mermaid.initialize({{ 
                            startOnLoad: true, 
                            theme: 'default' 
                        }});
                        
                        // Wait for Mermaid SVG to render
                        const observer = new MutationObserver((mutations) => {{
                            mutations.forEach((mutation) => {{
                                if (mutation.addedNodes.length > 0) {{
                                    const svgElement = document.querySelector('#mermaid-graph svg');
                                    if (svgElement && !window.panzoomInstance) {{
                                        observer.disconnect();
                                        
                                        // Initialize Panzoom
                                        const elem = document.getElementById('panzoom-element');
                                        window.panzoomInstance = Panzoom(elem, {{
                                            maxScale: 5,
                                            minScale: 0.1,
                                            contain: 'outside',
                                            startScale: 1
                                        }});
                                        
                                        const container = document.getElementById('zoom-container');
                                        container.addEventListener('wheel', window.panzoomInstance.zoomWithWheel);
                                        
                                        // Button controls
                                        document.getElementById('zoomIn').addEventListener('click', window.panzoomInstance.zoomIn);
                                        document.getElementById('zoomOut').addEventListener('click', window.panzoomInstance.zoomOut);
                                        document.getElementById('resetZoom').addEventListener('click', window.panzoomInstance.reset);
                                    }}
                                }}
                            }});
                        }});
                        
                        observer.observe(document.getElementById('mermaid-graph'), {{ childList: true, subtree: true }});
                        
                        window.downloadPDF = function() {{
                            // Temporarily reset panzoom so it doesn't crop the PDF output
                            if (window.panzoomInstance) {{
                                window.panzoomInstance.reset();
                            }}
                            
                            const element = document.getElementById('mermaid-graph');
                            const opt = {{
                                margin:       0.5,
                                filename:     'Research_Paper_Flowchart.pdf',
                                image:        {{ type: 'jpeg', quality: 1 }},
                                html2canvas:  {{ scale: 2, useCORS: true, backgroundColor: '#FFFFFF' }},
                                jsPDF:        {{ unit: 'in', format: 'a3', orientation: 'landscape' }}
                            }};
                            
                            // Download
                            html2pdf().set(opt).from(element).save();
                        }};
                    </script>
                    """,
                    height=800,
                    scrolling=False
                )
