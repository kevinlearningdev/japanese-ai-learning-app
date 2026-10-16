# Japanese AI Learning App

Turns a screenshot with a Japanese caption into a flashcard: the sentence, its reading, a translation, and the vocabulary in it.

It's a learning project, rebuilt from scratch to understand what different models are good and bad at and how to chain them.
Right now it runs from the command line with one frontier vision-model call; a web app comes later.

## Setup

Needs [uv](https://docs.astral.sh/uv/), [Task](https://taskfile.dev/), and an [Anthropic API key](https://console.anthropic.com/).

```sh
cd backend && uv sync
echo "ANTHROPIC_API_KEY=sk-ant-..." > backend/.env
```

## Usage

```sh
task card -- path/to/screenshot.png   # print the card and save it to eval/cards/
task cards                            # every screenshot in eval/screenshots/
task lint
```

Each card is saved as JSON with the model, effort, token counts, and estimated cost.

The `eval/` folder is git-ignored, since the screenshots are other people's content; put your own in `eval/screenshots/`.

## Layout

- `backend/` — the card model (`card.py`) and the screenshot-to-card script (`main.py`)
- `docs/` — card creation requirements and technical design
- `eval/` — screenshots and generated cards (not committed)

## License

MIT
