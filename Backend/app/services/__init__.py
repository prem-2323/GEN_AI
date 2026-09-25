"""Service layer package — one folder per domain.

    ai/             Qwen text + Gemma vision analysis, phase + pipeline orchestrators
    audio/          text-to-speech / voiceover synthesis
    consistency/    Phase 6 validation engine (UCKR <-> deliverable)
    export/         Phase 10 multi-format exporters (+ md/json/pptx pipeline export)
    extraction/     source text + image extraction (txt, pdf, docx, images)
    jobs/           background job queue and worker
    presentation/   python-pptx deck generator
    projects/       project CRUD + workspace snapshots
    search/         scoped search and project overview
    sources/        source lifecycle + stage machine
    storage/        Local file storage adapters
    transformation/ deliverable generation (Phase 5 engine + pipeline engine)
    uckr/           UCKR builder / validator (Phase 4 engine + pipeline engine)
    validation/     pipeline consistency checks (legacy route shape)

Modules are imported explicitly from their domain package, so nothing is
re-exported here on purpose (keeps the import graph acyclic).
"""
from __future__ import annotations
