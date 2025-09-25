import streamlit as st
import os
from pathlib import Path
import json

# Set up paths
data_dir = Path('data/exports')
pdf_dir = Path('data/raw/pdf')

# Helper to get available PDFs and methods
def get_pdfs():
    return sorted([f.name for f in pdf_dir.glob('*.pdf')])

def get_methods():
    return ['docling', 'layout_parser', 'hybrid', 'pdfplumber_tesseract']


# Updated: Get report paths for markdown, JSON, and text
def get_report_paths(pdf_name, method):
    pdf_stem = Path(pdf_name).stem
    # Method-specific markdown suffixes
    md_suffix_map = {
        'docling': '_docling_converted.md',
        'hybrid': '_hybrid_extraction.md',
        'layout_parser': '_layout_parser_reassembled.md',
        'pdfplumber_tesseract': '_pdfplumber_tesseract.md',
    }
    # Method-specific JSON suffixes
    json_suffix_map = {
        'docling': '_docling_structured.json',
        'hybrid': '_hybrid_extraction.json',
        'layout_parser': '_layout_parser_blocks.json',
        'pdfplumber_tesseract': '_pdfplumber_tesseract.json',
    }
    md_name = pdf_stem + md_suffix_map.get(method, f'_{method}.md')
    json_name = pdf_stem + json_suffix_map.get(method, f'_{method}.json')
    txt_name = f'{pdf_stem}_{method}_clean.txt'
    md_path = Path('data/exports/markdown') / method / md_name
    json_path = Path('data/exports/json') / method / json_name
    txt_path = Path('data/exports/text') / method / txt_name
    return md_path, json_path, txt_path


# Load markdown, JSON, or text report
def load_markdown_report(md_path):
    if md_path.exists():
        with open(md_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def load_json_report(json_path):
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def load_text_report(txt_path):
    if txt_path.exists():
        with open(txt_path, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def show_pdf(pdf_name):
    pdf_path = pdf_dir / pdf_name
    if pdf_path.exists():
        st.markdown(f'#### Preview: {pdf_name}')
        st.download_button('Download PDF', pdf_path.read_bytes(), file_name=pdf_name)
        st.markdown('---')
        st.info('PDF preview not available in browser, but you can download the file above.')
    else:
        st.warning('PDF not found.')


def show_report(md_report, json_report, txt_report, method, report_type):
    st.markdown(f'### {method.replace("_", " ").title()} Report')
    if report_type == "Markdown":
        if md_report:
            st.markdown(md_report)
        else:
            st.error('No markdown report found for this PDF and method.')
    elif report_type == "JSON":
        if json_report:
            st.json(json_report)
        else:
            st.error('No JSON report found for this PDF and method.')
    elif report_type == "Text":
        if txt_report:
            st.text(txt_report)
        else:
            st.error('No text report found for this PDF and method.')
    else:
        st.error('Invalid report type selected.')

# Streamlit UI
st.title('PDF Extraction Report Viewer')

pdfs = get_pdfs()
methods = get_methods()

if not pdfs:
    st.warning('No PDFs found in data/raw/pdf.')
    st.stop()


# Sidebar for PDF, method, and report type selection
selected_pdf = st.sidebar.selectbox('Select PDF', pdfs)
selected_method = st.sidebar.radio('Select Extraction Method', methods)
report_types = ["Markdown", "JSON", "Text"]
selected_report_type = st.sidebar.radio('Select Report Type', report_types)

# Show PDF preview/download
show_pdf(selected_pdf)



# Show report for selected method and report type
md_path, json_path, txt_path = get_report_paths(selected_pdf, selected_method)
md_report = load_markdown_report(md_path)
json_report = load_json_report(json_path)
txt_report = load_text_report(txt_path)
show_report(md_report, json_report, txt_report, selected_method, selected_report_type)
