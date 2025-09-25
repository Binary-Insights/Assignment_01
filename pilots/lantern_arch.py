# Requires: diagrams, graphviz installed on the system
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.onprem.vcs import Git
from diagrams.onprem.compute import Server
from diagrams.onprem.registry import Harbor as DVC  # icon stand-in for DVC
from diagrams.onprem.analytics import Spark as Eval  # generic "evaluation" stand-in
from diagrams.onprem.monitoring import Prometheus as Bench  # generic "benchmark" stand-in
from diagrams.onprem.database import PostgreSQL as Metastore
from diagrams.onprem.workflow import Airflow  # stand-in for orchestration (DVC stages)
from diagrams.generic.storage import Storage as RawStore
from diagrams.generic.storage import Storage as ParsedStore
from diagrams.generic.compute import Rack as Parser
from diagrams.generic.blank import Blank as MarkdownOut
from diagrams.generic.blank import Blank as JsonlOut
from diagrams.generic.blank import Blank as TxtOut

# Cloud APIs (managed "Build vs Buy" fallback)
from diagrams.aws.ml import Textract
from diagrams.gcp.ml import AutoML as DocAI   # stand-in for Google Document AI
from diagrams.azure.ml import CognitiveServices as AzureDI

# External source
from diagrams.generic.network import Router as SEC_EDGAR

with Diagram("Project LANTERN – Ingestion & Parsing Architecture", show=False, filename="lantern_arch", outformat="png"):
    user = Users("Analysts / Team")
    repo = Git("Private GitHub Repo\n(code + dvc.yaml)")
    dvc = DVC("DVC Cache/Remotes\n(data lineage)")
    orch = Airflow("Pipeline Orchestrator\n(dvc repro)")

    sec = SEC_EDGAR("SEC EDGAR")

    with Cluster("Storage"):
        raw = RawStore("data/raw (PDFs + XBRL)")
        parsed = ParsedStore("data/parsed (CSV/Tables)")
        md = MarkdownOut("reports/*.md (Markdown)")
        jsonl = JsonlOut("metadata/*.jsonl")
        txt = TxtOut("text/*.txt")
        meta = Metastore("Provenance/Metadata Index")

    with Cluster("Open-source Parsing Pipeline"):
        downloader = Server("sec-edgar-downloader")
        text_extract = Parser("pdfplumber\n+ OCR (Tesseract)")
        tables = Parser("Camelot\n(lattice/stream)")
        layout = Parser("LayoutParser\n(blocks/bboxes)")
        docling = Parser("Docling\n(reading order, tables)")

    with Cluster("Managed Fallback (Build vs Buy)"):
        textract = Textract("AWS Textract")
        gdocai = DocAI("Google Document AI")
        azdi = AzureDI("Azure Document Intelligence")

    with Cluster("Evaluation & Validation"):
        evalq = Eval("WER / Table P/R\n(regression tests)")
        bench = Bench("Runtime & Cost\n(benchmarks)")
        xbrl = Server("XBRL Parsing\n(Arelle/python-xbrl)")

    # Flow
    user >> repo
    repo >> orch >> downloader >> sec
    sec >> raw

    raw >> layout >> Edge(label="route blocks") >> text_extract
    layout >> tables
    layout >> docling

    # Managed APIs as optional path
    raw >> textract
    raw >> gdocai
    raw >> azdi

    # Outputs
    text_extract >> txt
    tables >> parsed
    docling >> md
    docling >> jsonl

    # Metadata / provenance
    layout >> meta
    docling >> meta
    tables >> meta
    text_extract >> meta

    # Evaluation & validation
    [txt, parsed, md, jsonl] >> evalq
    [textract, gdocai, azdi] >> bench
    raw >> xbrl
    [parsed, jsonl] >> xbrl

    # Versioning
    [raw, parsed, md, jsonl, txt] >> dvc
    repo << dvc
