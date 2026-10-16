# Japanese AI Learning App — Card Creation Technical Design

## Context and scope

Card creation turns a screenshot of a Japanese caption into a study card (requirements in `jp-app-card-requirements.md`).
Producing a card takes several model tasks: reading the caption, generating the translation and vocabulary, readings, and speech.
Each task has several candidate models with different accuracy, cost and failure modes, and the right choice is decided by measurement.
The design centers on making every model call swappable and comparable; the web app, storage and hosting are built around that pipeline.

## Goals and non-goals

**Goals**
- Any model call can be replaced by another implementation (a different model, a local model, a stub) with a one-line change.
- Steps chain together, and mismatched input and output types are caught by the type checker.
- Every step call reports model, tokens, cost and time, so runs can be compared.
- Local and remote models differ only in the lowest layer.
- The pipeline runs from the command line, independent of the web app.

**Non-goals**
- A general-purpose framework; the abstraction covers this app's model calls only.
- Studying cards and the conversation partner, which have their own designs.
- Retries, fallbacks, or handling for failures that haven't happened.
- Multi-user support.

## Overview

A screenshot goes through a chain of model steps and a card comes out.
A model step is any object with one `run` method that takes a typed input and returns a typed output, along with run metadata.
Inside an LLM-backed step there are two layers: the step's own logic (prompt and output type) on top of a provider call that sends the request to a model and returns parsed output plus usage.

```
                         ┌──────────── pipeline ────────────┐
screenshot ─► Image ─►   OCR step ─► text ─► card step ─► Card ─► TTS step ─► audio
                         └──────────────────────────────────┘
                                         │
                       provider calls: Anthropic API, Ollama, Modal

command line ─┐
              ├─► pipeline ─► card + run record
FastAPI ──────┘                   │
   ▲                              ▼
React page                 SQLite + files on disk
```

Whether the card comes from one vision-model call or a chain (OCR, then card generation) is a configuration choice, decided by evaluation.

## Detailed design

### Card model

Pydantic models in `backend/card.py`:

```python
class VocabEntry(BaseModel):
    written_form: str        # as it appears in the sentence, conjugation included
    written_reading: str     # hiragana
    dictionary_form: str     # the headword to look up
    dictionary_reading: str  # hiragana
    meaning: str             # English meaning of the dictionary form


class Card(BaseModel):
    sentence: str
    reading: str             # hiragana
    translation: str
    vocab: list[VocabEntry]
```

The same model is the LLM's output schema, the saved format and the API contract.
Field descriptions are sent to the model as part of the schema, so editing one changes model behavior.
Furigana and audio fields are added by the steps that produce them.

**Vocabulary rule:** one entry per dictionary headword, so splits are the same every run and can be checked on Jisho.
Helper verbs and endings stay with the main verb (触らせてあげる → 触る), words used with する go under the word (ひんやり), and particles, a standalone copula and filler sounds are left out.

### Model-step interface

A generic `Protocol`, parameterized over input and output type:

```python
class ModelStep[In, Out](Protocol):
    def run(self, input: In) -> StepResult[Out]: ...


@dataclass
class StepResult[Out]:
    output: Out
    model: str               # "claude-opus-5-5", "stub"
    effort: str | None
    input_tokens: int
    output_tokens: int
    cost_usd: float
    seconds: float
```

A step conforms by having a matching `run` method; it inherits nothing.
Steps share a shape but not behavior (an OCR step and a TTS step have nothing in common inside), so a protocol describes them and a base class would not.
A base class for LLM-backed steps is worth adding only once several of them repeat the same request and usage code.
Steps without token counts (a local OCR model, TTS) report zeros.

### Provider call

The bottom layer of an LLM-backed step: send a system prompt, content and output schema to a model, and return parsed output and usage.
Everything provider-specific (API key, base URL, request shape, local server failures) stays here.
If local-vs-remote logic shows up in a step's own code, the boundary is in the wrong place.
Local models run behind Ollama during development and on Modal when deployed; both are additional provider calls with the same return shape.

### Pipeline steps

| Step | Input → output | Candidates |
|---|---|---|
| Card (single call) | `Image` → `Card` | Claude Opus 5.5 (reference ceiling) |
| OCR | `Image` → text | manga-ocr, OwOCR or MeikiOCR, an open vision LLM |
| Card generation | text → `Card` | a local LLM (Qwen2.5 7B baseline), one alternative, the frontier model |
| Readings and furigana | text → bracket furigana | fugashi/cutlet, a local LLM |
| Speech | text → audio file | VOICEVOX, one alternative |

At most three candidates per step, plus the frontier model as the ceiling.
Furigana uses bracket notation over kanji only: `問[と]い合[あ]わせ`.

### Pipeline wiring

A plain function that loads the screenshot and calls the steps in order:

```python
def screenshot_to_card(path: Path, card_step: ModelStep[Image, Card]) -> StepResult[Card]:
    return card_step.run(Image.from_path(path))
```

Swapping a step means passing a different object.
Steps take `Image` bytes rather than a path, so the same step serves a file on the command line and an HTTP upload.
A runner that builds chains from configuration is added when the evaluation harness needs to compare chains.

### Evaluation harness

`eval/run.py` runs a chosen step or chain over `eval/screenshots/`, compares against checked expected outputs, and writes a table of per-screenshot results, cost and time.
Grading is exact / close / wrong, by hand where needed; no scoring framework.
Each run saves a record per screenshot and step: the output plus the `StepResult` metadata.

### Web API

FastAPI in `backend/`, wrapping the pipeline:

| Endpoint | Purpose |
|---|---|
| `GET /health` | liveness |
| `POST /api/cards` | multipart screenshot upload → run the pipeline → save and return the card |
| `GET /api/cards` | list saved cards |
| `GET /api/cards/{id}` | one card |

The Pydantic `Card` is the request and response contract; audio files are served as static files.
Card creation is synchronous until the wait is long enough to need background generation.

### Storage

SQLite with one `cards` table; vocabulary is a JSON column until a query needs it split out.
Screenshots and audio are files on local disk, referenced from the row.
No migrations: on a schema change, the development database is deleted.

### Frontend

Vite and React in `frontend/`, with the dev server proxying API calls to the backend.
Three views: upload, card (furigana and play buttons), and the saved-card list.
Only kanji go inside `<ruby>`; kana before or between kanji stay outside it.

### Hosting

An always-on home computer serves the web app and storage and runs no models.
Model calls go to the Anthropic API or to Modal functions, with model weights cached on a Modal Volume.

## Alternatives considered

- **Base class instead of a protocol.** Shares implementation for free, but forces an is-a relationship on steps that only share a shape.
- **`run` returns the bare output.** Simpler for callers, but metadata then needs a side channel, and the harness needs it per step.
- **A `Pipeline` class.** Useful for configurable chains; a plain function covers fixed ones.
- **LangChain or a similar framework.** Covers this, but hides the pattern the app exists to learn.
- **Prompt-only JSON instead of schema-constrained output.** Works on some models and breaks on others; compared per model during evaluation.

## Cross-cutting concerns

- **Cost:** every step reports cost, computed from published per-token prices for API models and GPU time for Modal.
- **Privacy:** `eval/` (screenshots, outputs) is git-ignored and never published.
- **Errors:** a malformed response raises a Pydantic `ValidationError`. Other failures are handled when they first occur, by fixing the cause.
- **Determinism:** Opus 5.5 takes no temperature, and GPU output isn't bit-identical to local, so evaluation runs each screenshot more than once where consistency matters.

## Open questions

- Where `Image` lives: `card.py`, or a module of shared types.
- Whether `stop_reason` belongs on `StepResult` or stays provider-specific.
- Whether speech runs on the home server or needs Modal.
