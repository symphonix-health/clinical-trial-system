"""Compatibility shim for the canonical seeder.

The implementation moved to ``app/seed.py`` so that caid-agent's
``discover_seed`` resolves the file the application actually imports (it
ranks ``backend/app/seed.py``; it has no candidate for
``backend/app/seeding/loader.py``, so the Seeding Alignment Gate previously
found NO seed artefact for this repo at all and failed closed).

This module re-exports. It deliberately holds no copy of the seed data: a
second, hand-maintained copy is the estate's known stale-duplicate defect
class, where the gate measures a file that nothing imports.
"""

from __future__ import annotations

from app.seed import _already_seeded, seed_all, seed_database

# Historic name kept for ``backend/tests/conftest.py`` and any caller that
# imported the private helper before the move.
_seed = seed_all

__all__ = ["_already_seeded", "_seed", "seed_all", "seed_database"]
