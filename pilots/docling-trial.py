from docling.document_converter import DocumentConverter
# from docling.document_converter import DocumentConverter, PdfFormatOption
# from docling.datamodel.base_models import InputFormat
# from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.pipeline_options import PipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend


source = "https://arxiv.org/pdf/2408.09869"  # PDF path or URL
converter = DocumentConverter()
# result = converter.convert_single(source)
# print(result.render_as_markdown())  # output: "## Docling Technical Report[...]"
# print(result.render_as_doctags())  # output: "<document><title><page_1><loc_20>..."