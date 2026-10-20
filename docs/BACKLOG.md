# PREPLINE backlog

Deferred issues from the v1.1 scoring-correctness branch (`fix/scoring-correctness`, final review 2026-10-21). Each line ends with its impact if left as is.

## Data

- **Core CS syllabi are scanned images.** 23 of the 26 allowlisted core courses (DSA, DAA, OS, DBMS, CN, …) sit on pages with no text layer, so v1.1 scores only BCSE102P, BMAT205L and BCSE203E. *Impact: S_comp does not yet measure the core curriculum; supply text-layer or offline-OCR'd PDFs as a separate step.*

## Syllabus parsing (`pipeline/syllabus_parser.py`)

- **Lab-only course units include objectives and outcomes.** A course without `Module:` headers becomes one unit that starts at its header, not at "Indicative Experiments". *Impact: outcome prose ("propose solutions through inheritance…") can create topic presence that the experiments themselves do not support.*
- **Duplicate module numbers inside one course give duplicate `source_id`s.** A repeated "Module:3", or a body line starting with "Unit 2", yields two `<code>_mod_3` records; only duplicate courses are guarded. *Impact: id-keyed consumers (unmapped-term dedup, versioning lookups) conflate two different units.*
- **A header with "L T P C" on its own line is not recognised.** The layout "CODE Title" / "L T P C" / "3 0 0 3" matches neither header pattern. *Impact: the course silently disappears, and if the catalogue lists it, it is mis-reported as scanned.*

## Security (from the 2026-10-21 manual security review)

- **No authentication or authorization on the API (M5).** Anyone who can reach the port can upload syllabi and run the pipeline; ids are now unguessable and the dev server binds 127.0.0.1, but there is no identity check. *Impact: exposing the API beyond localhost (PREPLINE_HOST) lets any client use it and read results for ids it learns.*
- **Upload-derived unmapped terms go into the shared log (L2).** Every upload appends its unmapped syllabus terms to `data/processed/unmapped_terms.log`, the input to the Phase 12 taxonomy review. *Impact: unbounded log growth, and repeated uploads can inflate term frequencies and skew taxonomy decisions; API uploads should log to a separate, bounded store.*
- **NLTK data is downloaded at runtime and safetensors is not enforced (L4).** `_get_rake()` calls `nltk.download` on a server's first request, and the embedding model is loaded without `model_kwargs={"use_safetensors": True}` (its revision is pinned). *Impact: a network fetch without integrity pinning at serve time; pre-download NLTK data at install and enforce safetensors.*

## Performance

- **The interview-importance cache grows without bound.** One entry per distinct questions.csv content and denominator. *Impact: negligible for the prototype; a long-running server with many dataset edits slowly leaks memory.*

## Tests

- **No API test that a PDF without course headers returns 400.** Only the parser-level error is tested. *Impact: a routing regression would ship unnoticed.*
- **No test that `run_full_pipeline.run()` returns INSUFFICIENT_DATA below 15 reports.** Verified manually in review only. *Impact: the CLI density gate could regress silently.*
- **No parse-level test that `source_id`s stay unique after a duplicate course.** *Impact: the duplicate-course guard could regress without a failing test.*

## Dependencies

- **Starlette deprecates the httpx-based TestClient.** A clean install pulls a newer Starlette (floored at >=1.1.0 but not pinned) that warns "install httpx2 instead". *Impact: a future Starlette release may break every TestClient-based test.*
- **Transitive dependencies are unpinned.** Only direct requirements are pinned (e.g. a clean install got pydantic 2.14 vs 2.13 locally). *Impact: test environments drift; a lock file would make installs reproducible.*
