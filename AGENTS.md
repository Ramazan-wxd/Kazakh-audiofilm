# AI Cinema — Project Instructions

## Project

AI Cinema is an experimental multimodal AI system for generating
temporally-aware audio descriptions of films, initially focused on
Kazakh-language accessibility.

The project has two planned modes:

1. Accessibility Mode
   - Generate concise audio descriptions of visually important events.
   - Place descriptions into available audio windows.
   - Avoid overlapping dialogue and important sound effects.
   - Support original-runtime and extended-runtime generation.

2. Immersive Mode
   - Future feature.
   - Transform scenes into a first-person cinematic retelling.
   - This is NOT part of the initial MVP.

## MVP priority

The MVP is:

Video
→ shot/scene segmentation
→ speech/transcript with timestamps
→ visual event understanding
→ description generation
→ temporal placement
→ Kazakh TTS
→ final synchronized audio/video

The MVP must prioritize:
1. Temporal placement quality.
2. Description usefulness and accuracy.
3. Kazakh language quality.
4. Reproducibility.
5. Evaluation.

Do NOT prematurely build:
- user authentication
- payments
- mobile apps
- production cloud infrastructure
- multi-language support
- character voice cloning
- full-length movie processing
- immersive mode

## Engineering principles

- Prefer simple, modular solutions.
- Do not over-engineer.
- Do not introduce dependencies without a reason.
- Reuse mature libraries and existing models.
- Do not train large models unless explicitly requested.
- Keep model/API providers replaceable.
- Keep expensive API calls isolated behind interfaces.
- Make processing deterministic/reproducible where practical.
- Never hardcode secrets.
- Use environment variables.
- Update .env.example when new environment variables are introduced.

## Research principles

Treat this as both a software project and an experimental research project.

Every important design decision should have:
- motivation
- assumptions
- alternatives considered
- measurable evaluation criteria

Never claim novelty without evidence.

When making claims about research, libraries, models, licenses,
copyright, or APIs, verify them using authoritative sources.

## Copyright

Use only public-domain, openly licensed, or user-provided material
for included demos.

Never commit copyrighted movies, extracted movie scenes, or
unlicensed audio into the repository.

Keep demo assets small and legally usable.

## Code quality

- TypeScript strict mode where applicable.
- Python type hints where applicable.
- Small modules with clear responsibilities.
- Avoid giant files.
- Meaningful variable/function names.
- No dead code.
- No unnecessary abstractions.

## Testing

Every meaningful feature should have tests.

Prefer:
- unit tests for deterministic logic
- integration tests for pipelines
- Playwright for critical UI flows

For the temporal engine, create synthetic tests where exact expected
timestamps are known.

## Git

Make small logical commits.

Before declaring a task complete:
1. Run relevant tests.
2. Run lint/type checks.
3. Inspect the diff.
4. Summarize what changed.
5. Mention anything not tested.

Never silently modify unrelated files.

## Working style

Before implementing a complex feature:
- inspect the existing code
- identify relevant files
- propose a plan
- implement incrementally
- verify after each meaningful stage

If requirements are ambiguous, state the ambiguity and choose the
simplest reasonable interpretation rather than inventing a large system.