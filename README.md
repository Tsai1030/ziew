# KBParse

PDF-first company knowledge-base parser MVP.

## Quickstart / validation

```bash
cd /mnt/c/Users/pijh1/Desktop/kbparse
uv run --with pytest pytest tests/ -q
uv run kbparse ingest ./examples/pdfs ./output --parser fake --provider mock
uv run kbparse validate ./output/<doc_id>
```

## Parse a real text-layer PDF with PyMuPDF

PyMuPDF is the lightweight first real parser. It is intended for text-layer PDFs and smoke testing the pipeline. It currently extracts text blocks, renders page images, and extracts embedded images as pending visual assets. Complex layout, OCR, high-fidelity tables, and scanned PDFs should be handled by Docling / Marker adapters.

```bash
cd /mnt/c/Users/pijh1/Desktop/kbparse
uv run kbparse ingest ./examples/pdfs/pymupdf_smoke.pdf ./output_pymupdf --parser pymupdf --provider mock
uv run kbparse validate ./output_pymupdf/pymupdf_smoke
```

Expected output:

```text
Validation OK
```

Expected files:

```text
output_pymupdf/<doc_id>/
  document.json
  document.md
  chunks.jsonl
  quality_report.json
  parse_artifacts/pages/page_0001.png
  assets/images/...
```

`assets/images/` appears only when the PDF contains embedded images.

## Parse with Docling adapter

Docling is an optional heavier parser for richer layout extraction. The current KBParse Docling adapter runs Docling, stores the raw Docling JSON artifact, maps Docling body/layout references directly into canonical KBParse elements when available, crops Docling picture regions into `assets/figures/`, crops Docling table regions into `assets/tables/`, preserves table cells / HTML metadata when available, associates nearby captions, and then lets KBParse generate `document.md`, `chunks.jsonl`, and validation reports from `document.json`.

Install / run with the optional dependency:

```bash
cd /mnt/c/Users/pijh1/Desktop/kbparse
uv run --extra docling kbparse ingest ./examples/pdfs/pymupdf_smoke.pdf ./output_docling --parser docling --provider mock
uv run kbparse validate ./output_docling/pymupdf_smoke
```

Alternative one-shot install style:

```bash
uv run --with docling kbparse ingest ./examples/pdfs/pymupdf_smoke.pdf ./output_docling --parser docling --provider mock
```

Expected files:

```text
output_docling/<doc_id>/
  document.json
  document.md
  chunks.jsonl
  quality_report.json
  parse_artifacts/docling_document.json
  assets/figures/p0001_fig001.png   # when Docling detects picture/figure regions
  assets/tables/p0001_table001.png  # when Docling detects table regions
```

Picture smoke test:

```bash
uv run --with docling kbparse ingest ./examples/pdfs/docling_picture_smoke.pdf ./output_docling_picture --parser docling --provider mock
uv run kbparse validate ./output_docling_picture/docling_picture_smoke
```

Table smoke test:

```bash
uv run --with docling kbparse ingest ./examples/pdfs/docling_table_smoke.pdf ./output_docling_table --parser docling --provider mock
uv run kbparse validate ./output_docling_table/docling_table_smoke
```

Note: Docling may classify simple drawn/vector tables as pictures depending on the source PDF and Docling model behavior. The adapter has unit-level coverage for Docling `table` nodes and will crop them to `assets/tables/` when Docling emits table layout nodes.

Current Docling adapter limitations:

- It maps Docling `body.children` references for text/caption/table/picture nodes, including page number and normalized bbox when `prov` exists.
- It converts Docling table cells into basic Markdown tables for canonical table elements.
- It preserves Docling table cell JSON and table HTML metadata when Docling provides them.
- It crops Docling table regions from the source PDF into `assets/tables/` using Docling bbox coordinates.
- It crops Docling picture regions from the source PDF into `assets/figures/` using Docling bbox coordinates.
- It associates the nearest same-page caption with figure and table elements as `caption_nearby`.
- It creates pending visual elements so VLM enrichment can run later.
- It falls back to exported Markdown only when no mappable Docling body elements exist.
- It does not yet implement high-confidence table classification when Docling itself emits a simple drawn table as `picture` instead of `table`.
- Future work should add richer heading levels, stronger table/figure classifier heuristics, and better caption-to-table/figure matching.

## Manual checks

- Open `output/<doc_id>/document.md` and confirm images render.
- Check `assets/figures/`, `assets/tables/`, or `assets/images/` contains generated assets when the source has images/tables.
- Check `chunks.jsonl` visual chunks include `asset_path`.
- Search `text_for_embedding` and confirm it does not contain `assets/` or raw image extensions like `.png` / `.jpg`.

## MVP scope

The current MVP implements a deterministic fake parser, a PyMuPDF text-layer parser skeleton, an optional Docling adapter with direct body/text/table/picture mapping, figure crops, table crops, table cell/HTML metadata preservation, canonical `document.json`, Markdown export with standard image syntax, structured chunk building, mock VLM enrichment, validation, and quality reports.

## Not yet in scope

- OCR for scanned PDFs.
- High-confidence fallback classification when Docling emits drawn tables as pictures.
- Marker adapter.
- Real OpenAI / Gemini / local VLM providers.
- Vector database ingestion.
