# Labelling guide — Phase 13 benchmark (`labels_v1.0.csv`)

**Pinned to taxonomy v1.0.** Use only ids from `TAXONOMY_CHEATSHEET.md` (`data/taxonomy/taxonomy_v1.0.json`).
Never invent an id. If the right concept is missing, use the closest node or `none`, and write `gap: <concept>` in
`label_notes`. Labels for a later taxonomy go in a new `labels_v<version>.csv`.

**Label from `raw_text` alone.** Do not look at pipeline outputs, similarity scores or results files.

## Which ids a row may take

| source_type | allowed ids |
|---|---|
| `syllabus` (a theory module or one lab experiment) | `high_level_concept` (**H** in the cheat sheet) |
| `interview` (one interview question) | `granular_skill` (g in the cheat sheet) |

`python evaluation/benchmark/validate_labels.py` rejects any other combination.

## expected_primary (exactly one value)

- The one node the item is **mainly** about. For a syllabus unit, that is where most of its content (or hours) goes.
  For an interview question, it is the skill needed to solve it.
- Prefer the most specific node of the allowed type (e.g. `dsa.trees` rather than `dsa`). Use a domain root (`dsa`,
  `os`, `dbms`, `cn`, `system_design`) only for an overview that spans several of its children.
- `none` means no node of the allowed type fits, e.g. software process models, cryptography, compiler parsing, or a
  question that names no technical skill. Use `none` deliberately; it is a real label.
- Leave it **empty** only if you have not labelled the row yet. Empty rows count as unlabelled.

## expected_secondary (optional, `;`-separated)

- Other nodes of the **same allowed type** that the item **substantially** covers or needs, not passing mentions
  ("Applications", one word in a list). Usually 0–2, at most 3.
- Never repeat the primary, never `none`, and leave it empty when the primary is `none` or empty.
- Example: a module "Stack, Queue, Linked lists" → primary `dsa.stacks_queues`, secondary `dsa.linked_lists; dsa.arrays`.

## label_notes (free text)

Use it for ambiguity ("half OS, half DBMS"), `gap: <concept>` for taxonomy gaps, and anything a second labeller should
know. Do not use it for model suggestions.

## Checking your work

Run `python evaluation/benchmark/validate_labels.py` after each session. It reports labelled rows per source type and
every row that breaks the rules above (unknown id, wrong node type, secondary without primary, duplicates). It exits
with code 1 if any row is invalid.
