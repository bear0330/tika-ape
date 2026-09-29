# Evidence Copilot

`Evidence Copilot` is a local RAG-style document-intelligence demo. It
downloads public PDF and HTML material, extracts it through `tika_ape`, chunks
the text, and embeds those chunks with `sentence-transformers/all-MiniLM-L6-v2`.
It produces an HTML briefing with ranked, source-labelled evidence passages.

Install the Python binding and embedding runtime:

```powershell
& 'C:\Users\Naga\miniconda3\envs\tika-ape\python.exe' -m pip install .\bindings\python sentence-transformers
& 'C:\Users\Naga\miniconda3\envs\tika-ape\python.exe' .\examples\evidence_copilot\evidence_copilot.py
```

The first run downloads the source documents and embedding model. Later runs
perform extraction and retrieval locally. Open
`examples/evidence_copilot/output/index.html` to inspect the briefing.

The binding needs neither a host JVM nor a separate Tika configuration file.
It uses Tika's normal conservative PDF behavior; enable
`tika_ape.configure(inline_images=True)` when a workflow needs PDF inline-image
resources.
