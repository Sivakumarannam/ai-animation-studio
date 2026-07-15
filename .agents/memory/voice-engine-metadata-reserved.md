---
name: SQLAlchemy metadata reserved attribute
description: SQLAlchemy 2.0 DeclarativeBase reserves the attribute name `metadata`; naming a mapped column `metadata` causes InvalidRequestError on reimport.
---

## Rule
Never name a SQLAlchemy ORM column attribute `metadata` when using the new-style `DeclarativeBase`. Use a different Python attribute name and map it explicitly to the desired DB column name.

## Why
`DeclarativeBase` (SQLAlchemy 2.0) uses `metadata` as a class-level attribute for the `MetaData()` object. Defining a `mapped_column()` with the same attribute name causes:
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```
This error appears on reimport (e.g. pytest reloading modules) even if the first import succeeds.

## How to apply
Use a prefixed attribute name and specify the DB column name explicitly:
```python
# WRONG
metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

# CORRECT — attribute name is prefixed, DB column name is explicit
output_metadata: Mapped[dict] = mapped_column("vo_output_meta", JSON, nullable=False, default=dict)
```
Phase 7 (`AnimationRenderOutput`) used `metadata_: Mapped[dict] = mapped_column("an_render_output_meta", ...)`.
Phase 8 (`VoiceOutput`) uses `output_metadata: Mapped[dict] = mapped_column("vo_output_meta", ...)`.
Apply this pattern to ALL future phases that need a JSON metadata column.
