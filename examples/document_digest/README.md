# Document Digest

Turn a folder containing PDFs, Office files, HTML, and text documents into one
Markdown corpus. Each section records the source path, detected MIME type,
metadata, and extracted text for an LLM context or RAG-ingestion step.

Install the Python binding, then run the example:

```powershell
& 'C:\Users\Naga\miniconda3\envs\tika-ape\python.exe' -m pip install .\bindings\python
& 'C:\Users\Naga\miniconda3\envs\tika-ape\python.exe' `
  .\examples\document_digest\document_digest.py `
  C:\Documents\research `
  --output .\document-digest.md
```

The example calls `tika_ape` directly. Its bundled Host Services provider
needs no host Java installation. Tika's normal conservative PDF behavior is
used; call `tika_ape.configure(inline_images=True)` before extraction when a
workflow also needs PDF inline-image resources.
