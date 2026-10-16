import base64
import json
import mimetypes
from pathlib import Path

import anthropic
import click

from card import Card

MODEL = "claude-opus-5-5"
EFFORT = "high"
CARDS_DIR = Path(__file__).resolve().parent.parent / "eval" / "cards"
INPUT_DOLLARS_PER_MILLION_TOKENS = 4
OUTPUT_DOLLARS_PER_MILLION_TOKENS = 20

SYSTEM_PROMPT = """\
You make flashcards for a beginner learning Japanese. You'll get a screenshot, \
usually a frame from a short video with a Japanese caption. Read the caption and \
fill in the card.

Sentence
- Copy the Japanese text exactly as written, including symbols like 〜 and ….
- If the caption spans several lines, join them into one line.

Vocabulary
- Include every content word: nouns, verbs, adjectives, adverbs, and onomatopoeia. \
Include basic words too; don't skip a word because it seems easy.
- Include proper nouns too (people's names, place names); every word in the \
sentence is worth learning. For a name, give its most common reading, and say \
what kind of name it is in the meaning (family name, given name, place name).
- Leave out particles (が, を, に, は…), the copula when it stands on its own \
(です, だ, でした), interjections and filler sounds (あ〜, えっと), and punctuation.
- Make one entry per dictionary headword: the dictionary form must be a word \
you could look up in a standard dictionary such as Jisho, in its standard \
spelling (分かる, not わかる). If the dictionary marks a word as usually \
written in kana, use the kana (いくらでも, not 幾らでも).
- A verb with helper verbs or grammar endings attached (ている, ます, てあげる, \
てしまう, ようとする, the causative せる) is one entry under the main verb. The \
written form keeps the whole chain (触らせてあげる → 触る).
- A word used with する (ひんやりする, 勉強する) is one entry under the word \
itself (ひんやり); the written form keeps する and its endings.
- An adverb made from a な-adjective with に (勝手に) goes under the \
adjective (勝手).
- If a phrase has its own dictionary entry (気持ちいい), keep it as one entry \
instead of splitting it.
- Give the meaning of the dictionary form only; don't explain how it's used \
in this sentence.
- List words in the order they appear, and list a repeated word only once.
"""


@click.command()
@click.argument("screenshot", type=click.Path(exists=True, path_type=Path))
def make_card(screenshot: Path) -> None:
    """Turn a screenshot into a flashcard, print it, and save it to eval/cards/."""
    media_type, _ = mimetypes.guess_type(screenshot)
    image_data = base64.standard_b64encode(screenshot.read_bytes()).decode("utf-8")

    client = anthropic.Anthropic()
    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        output_config={"effort": EFFORT},
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": "Make a card for this screenshot."},
                ],
            }
        ],
        output_format=Card,
    )

    card = response.parsed_output
    print(card.model_dump_json(indent=2))

    usage = response.usage
    cost = (
        usage.input_tokens * INPUT_DOLLARS_PER_MILLION_TOKENS
        + usage.output_tokens * OUTPUT_DOLLARS_PER_MILLION_TOKENS
    ) / 1_000_000
    print(
        f"\nstop_reason={response.stop_reason} "
        f"tokens={usage.input_tokens} in / {usage.output_tokens} out, ~${cost:.4f}"
    )

    record = {
        "card": card.model_dump(),
        "model": MODEL,
        "effort": EFFORT,
        "stop_reason": response.stop_reason,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cost_usd": round(cost, 4),
    }
    CARDS_DIR.mkdir(exist_ok=True)
    out_path = CARDS_DIR / f"{screenshot.stem}.json"
    out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(f"saved {out_path}")


if __name__ == "__main__":
    make_card()
