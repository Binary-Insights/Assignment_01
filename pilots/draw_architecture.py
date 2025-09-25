# Requires: diagrams, graphviz installed on the system
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.onprem.vcs import Git
from diagrams.onprem.compute import Server
from diagrams.onprem.registry import Harbor as DVC  # icon stand-in for DVC
from diagrams.onprem.analytics import Spark as Eval  # generic "evaluation" stand-in
from diagrams.onprem.monitoring import Prometheus as Bench  # generic "benchmark" stand-in
from diagrams.generic.storage import Storage  as Metastore
from diagrams.generic.blank import Blank
from diagrams.generic.storage import Storage as RawStore
from diagrams.generic.storage import Storage as ParsedStore
from diagrams.generic.compute import Rack as Parser
from diagrams.generic.blank import Blank as MarkdownOut
from diagrams.generic.blank import Blank as JsonlOut
from diagrams.generic.blank import Blank as TxtOut
from diagrams.generic.storage import Storage 
from diagrams.aws.storage import S3
from diagrams.onprem.client import Client

# Cloud APIs (managed "Build vs Buy" fallback)
from diagrams.aws.ml import Textract


# External source
from diagrams.generic.network import Router as SEC_EDGAR

with Diagram("Project LANTERN – Ingestion & Parsing Architecture", show=False, filename="lantern_arch", outformat="png"):
    user = Users("Analysts / Team")
    repo = Git("Private GitHub Repo\n(code + dvc.yaml)")
    dvc = Storage("DVC Cache/Remotes\n(data lineage)")
    orch = Client("Command Line\n(dvc repro)")
    s3remote = S3("DVC Remote Storage (S3)")

    sec = SEC_EDGAR("SEC EDGAR")

    with Cluster("Storage Structure"):
        meta = Storage("data/metadata")
        raw = Storage("data/raw")
        parsed = Storage("data/parsed")
        reports = Storage("data/reports")

    with Cluster("Extraction Services"):
        docling = Server("Docling Service")
        layout_parser = Server("LayoutParser Service")
        pdfplumber_tesseract = Server("PDFPlumber+Tesseract Service")
        hybrid = Server("Hybrid Service")



    with Cluster("Managed Fallback (Build vs Buy)"):
        textract = Textract("AWS Textract")

    # with Cluster("Evaluation & Validation"):
    #     # evalq = Eval("WER / Table P/R\n(regression tests)")
    #     bench = Bench("Runtime & Cost\n(benchmarks)")
    #     xbrl = Server("XBRL Parsing\n(Arelle/python-xbrl)")

    # Flow
    user >> repo
    repo >> orch
    orch >> sec
    sec >> raw

    # raw >> layout >> Edge(label="route blocks") >> text_extract
    # layout >> tables
    # layout >> docling

    # Managed APIs as optional path
    raw >> textract

    # Orchestration: Command line triggers all extraction services
    orch >> [docling, layout_parser, pdfplumber_tesseract, hybrid]

    # Each service reads from storage and writes to storage
    raw >> docling >> [parsed, reports, meta]
    raw >> layout_parser >> [parsed, reports, meta]
    raw >> pdfplumber_tesseract >> [parsed, reports, meta]
    raw >> hybrid >> [parsed, reports, meta]


    # Evaluation & validation
    # [txt, parsed, md, jsonl] >> evalq
    # [textract] >> bench
    # raw >> xbrl
    # [parsed, jsonl] >> xbrl

    # Versioning
    # [raw, parsed, md, jsonl, txt] >> dvc
    # Versioning: DVC manages all storage folders
    [meta, raw, parsed, reports] >> dvc
    dvc >> s3remote
    # repo << dvc
    # orch >> dvc
    # orch << dvc
    orch >> Edge(color="red") >> dvc
    dvc >> Edge(color="blue") >> orch
    # orch >> Edge(label="dvc push") >> dvc
    # dvc >> Edge(label="dvc pull") >> orch
 