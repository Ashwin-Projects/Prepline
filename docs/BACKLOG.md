# PREPLINE backlog

Deferred issues from the v1.1 scoring-correctness branch (`fix/scoring-correctness`, final review 2026-10-21). Each line ends with its impact if left as is.

## Data

- ~~**Core CS syllabi are scanned images.**~~ Resolved on `data/course-syllabi` (2026-10-21): the owner supplied 20 text-layer course PDFs (`data/raw/syllabi/BCSE*.pdf`), scored as one combined syllabus under config v1.2.
- **BCSE205L L-T-P-C is incomplete in its PDF.** The text layer holds only "3" (L) and "0" (P); the parser records `ltpc_status: "incomplete"` and leaves the values blank. *Impact: none on depth (theory depth comes from module hours); credits are missing from course metadata until the owner verifies the official values.*

- **BCSE101E, BCSE102L and BCSE103E are scored from manual transcriptions; BCSE203E is not supplied.** Their PDFs are Microsoft Print-to-PDF files whose text is drawn as vector outlines (no text layer). Claude transcribed the rendered pages into `data/raw/syllabi/transcribed/<CODE>.txt` (2026-10-22), used only when a PDF has no text; results mark them `text_source: manual_transcription`. BCSE102L Module 4's last line is clipped in the source. The BCSE101E and BCSE103E "ETH"/"ELA" files are byte-identical copies. *Impact: transcription errors would go unnoticed; spot-check the 3 files against the PDFs (or supply text-layer PDFs) and supply BCSE203E (v1.2 scores 25 of 26 core courses).*
- **Embedded (E) courses spread their lab hours over the theory modules too.** BCSE101E/BCSE103E (P = 4, 60 lab hours) give each of their 8 units 7.5 lab hours, unlike L+P pairs where lab hours sit only on lab experiments. *Impact: theory modules of E courses carry a lab signal; their lab block is one unit, not split into experiments.*

## Syllabus parsing (`pipeline/syllabus_parser.py`)

- **Lab-only course units include objectives and outcomes when no experiment list is found.** Lab courses with an "Indicative Experiments" list are now split into one unit per experiment; a lab course without a readable list still becomes one unit that starts at its header. *Impact: outcome prose can create topic presence the experiments do not support (none of the 8 supplied lab PDFs is affected).*
- **An experiment line that wraps onto a line starting with the next item's number is read as a new item.** Experiments are numbered 1, 2, 3, ...; a continuation line is only told apart when its leading number breaks the sequence. *Impact: rare mis-split of one experiment into two units (not seen in the supplied PDFs).*
- **Duplicate module numbers inside one course give duplicate `source_id`s.** A repeated "Module:3", or a body line starting with "Unit 2", yields two `<code>_mod_3` records; only duplicate courses are guarded. *Impact: id-keyed consumers (unmapped-term dedup, versioning lookups) conflate two different units.*
- **A header with "L T P C" on its own line is not recognised.** The layout "CODE Title" / "L T P C" / "3 0 0 3" matches neither header pattern. *Impact: the course silently disappears, and if the catalogue lists it, it is mis-reported as scanned.*

## Matching and scoring (owner decision; tau and taxonomy are frozen)

- **Taxonomy nodes are embedded by description only, never by name.** `embeddings.load_taxonomy` encodes `description`; in the v1.2 course run DAA's "Dynamic Programming" module scores 0.450 against `dsa.dp` (below tau = 0.50; 0.731 with the name prepended), while Computer Architecture and Compiler Design modules match `dsa.dp` at 0.50. *Impact: real coverage is missed and spurious coverage is credited (see results/CHANGES_v1.2.md, "Mapping quality"); fixing it changes matching and needs a new config/results version.*
- **Depth is the mean of normalised signals, so an extra signal can lower it.** A topic matched by a 7-hour module (0.7) and a 3-hour lab experiment (0.3) gets less depth than from the module alone; in the v1.2 run lab signals lowered depth for 6 of 13 theory+lab topics (mean change -0.04). *Impact: small; labs do not add depth the way a reader might expect.*

## API / dashboard

- **Multi-file syllabus upload (dashboard task).** `POST /api/v1/syllabi/upload` takes one PDF; combining course PDFs (`parse_syllabus_pdfs`) is CLI-only (`run_full_pipeline.py --pdf-dir`). *Impact: the dashboard cannot score a course-by-course syllabus until the upload accepts several files and returns one syllabus_id.*

- **Optional per-student electives mode (after the MVP).** Score the official core plus the electives a student actually took, as a per-student syllabus on top of the fixed core allowlist (config v1.2). *Impact: today every student gets the same core-only S_comp; electives that cover interview topics (e.g. system design) are not credited.*

## Security (from the 2026-10-21 manual security review)

- **No authentication or authorization on the API (M5).** Anyone who can reach the port can upload syllabi and run the pipeline; ids are now unguessable and the dev server binds 127.0.0.1, but there is no identity check. *Impact: exposing the API beyond localhost (PREPLINE_HOST) lets any client use it and read results for ids it learns.*
- **Upload-derived unmapped terms go into the shared log (L2).** Every upload appends its unmapped syllabus terms to `data/processed/unmapped_terms.log`, the input to the Phase 12 taxonomy review. *Impact: unbounded log growth, and repeated uploads can inflate term frequencies and skew taxonomy decisions; API uploads should log to a separate, bounded store.*
- **NLTK data is downloaded at runtime and safetensors is not enforced (L4).** `_get_rake()` calls `nltk.download` on a server's first request, and the embedding model is loaded without `model_kwargs={"use_safetensors": True}` (its revision is pinned). *Impact: a network fetch without integrity pinning at serve time; pre-download NLTK data at install and enforce safetensors.*

## Security review of `data/course-syllabi` (2026-10-22)

Fixed (High): `split_experiments` rebuilt the experiment string per continuation line (quadratic; 1.4 MB of lab text took ~12 s, reachable from `POST /syllabi/upload`). Now joined once; regression case in `test_regex_safety.py`.

- **Medium: a corrupt PDF or a directory in a combined run aborts the whole run.** `parse_syllabus_pdfs` records only `UnsupportedPDFError` in `file_errors`; pdfminer's `PdfminerException` and `PermissionError` (a directory matching `--glob`) propagate. CLI only. *Impact: one bad file in `--pdf-dir` stops the run with a traceback, contrary to the documented per-file contract.*
- **Medium: unit count per syllabus is unbounded.** Every numbered experiment line (and every `Module:N` header, as before) becomes a unit mapped through RAKE and the embedding model; a crafted upload with tens of thousands of short numbered lines multiplies that work, and a timed-out parse thread keeps running. *Impact: CPU exhaustion of the 2-worker parse pool within the 10 MB / 300-page limits; cap units per syllabus.*
- **Low: `--glob` is not confined to `--pdf-dir`.** A pattern such as `../*.pdf` matches files outside the folder, and glob follows symlinks. *Impact: none across a trust boundary (local CLI run by the owner); surprising input selection.*
- **Low: `--out` is checked with `os.path.exists` then opened with mode `"w"`.** *Impact: a file created in between is overwritten (TOCTOU); open with mode `"x"`.*
- **Low: PDF-derived course titles and experiment text are printed raw by the runner.** *Impact: control or ANSI escape sequences in a crafted PDF reach the terminal.*

## Performance

- **The interview-importance cache grows without bound.** One entry per distinct questions.csv content and denominator. *Impact: negligible for the prototype; a long-running server with many dataset edits slowly leaks memory.*

## Tests

- **No API test that a PDF without course headers returns 400.** Only the parser-level error is tested. *Impact: a routing regression would ship unnoticed.*
- **No test that `run_full_pipeline.run()` returns INSUFFICIENT_DATA below 15 reports.** Verified manually in review only. *Impact: the CLI density gate could regress silently.*
- **No parse-level test that `source_id`s stay unique after a duplicate course.** *Impact: the duplicate-course guard could regress without a failing test.*

## Dependencies

- **Starlette deprecates the httpx-based TestClient.** A clean install pulls a newer Starlette (floored at >=1.1.0 but not pinned) that warns "install httpx2 instead". *Impact: a future Starlette release may break every TestClient-based test.*
- **Transitive dependencies are unpinned.** Only direct requirements are pinned (e.g. a clean install got pydantic 2.14 vs 2.13 locally). *Impact: test environments drift; a lock file would make installs reproducible.*
