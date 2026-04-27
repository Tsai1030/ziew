# Sample parse output: Attention Is All You Need

This folder contains a real KBParse Docling parse result for the arXiv paper **Attention Is All You Need** (`1706.03762`).

- Main Markdown output: [`document.md`](document.md)
- RAG chunks: [`chunks.jsonl`](chunks.jsonl)
- Quality report: [`quality_report.json`](quality_report.json)
- Cropped visual/table assets: [`assets/`](assets/)

The Markdown uses relative image paths such as `assets/figures/p0003_fig001.png`, so GitHub can render the extracted figure assets from this folder.

Generated with:

```bash
uv run --with docling kbparse ingest ./examples/real_papers/attention_is_all_you_need.pdf ./output_sample_attention_docling --parser docling --provider mock
uv run kbparse validate ./output_sample_attention_docling/attention_is_all_you_need
```
