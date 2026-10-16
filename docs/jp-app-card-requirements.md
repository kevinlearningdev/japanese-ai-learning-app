# Japanese AI Learning App — Card Creation Requirements

## Overview

Card creation turns a screenshot of a Japanese caption into a study card: the sentence, its reading, a translation, the vocabulary in it, and audio.
It's one part of a personal Japanese learning app; studying cards with spaced repetition and the spoken conversation partner have their own requirements.

**Scope:** built for one user, its builder, a beginner who can't yet read most Japanese unaided.
Every requirement assumes a beginner: card fields are limited to what a beginner can check by lookup, and a card should be usable without already knowing the language.

## Problem

Vocabulary lists and textbook sentences teach words in an order unrelated to what the learner actually reads and hears, so they're hard to remember and often not the words that matter.
Language learned in the context where it was met sticks better, and it's the language the learner is already consuming.
What's missing is a way to capture that language as it's encountered and turn it into something reviewable.

Japanese video of every kind (short-form clips, long-form YouTube, drama, anime) is full of real, colloquial language in captions and subtitles.
Looking up a line means pausing, retyping the Japanese into a dictionary or translator, looking up each word separately, and getting no pronunciation.
It's slow enough that most phrases get skipped, and nothing is kept for review.

Tools that capture subtitles into study cards exist mostly on desktop, as browser extensions and desktop apps.
Much of this video is watched on a phone, where those options are limited, so the app is mobile-first.

## Existing options

- **Desktop is well covered.** Browser extensions and players (Migaku, Language Reactor, asbplayer, Yomitan with Anki) read subtitle text from streaming sites and local files and turn lines into cards.
- **Mobile is limited by the platform.** Native video apps (YouTube, Netflix, Instagram, TikTok) don't expose subtitle text, iOS extensions can't reach other apps, and short-form captions are often burned into the video. A screenshot is the one capture method that works everywhere.
- **Screenshot OCR on mobile exists, but stops at words.** Live Text and Google Lens give text and a translation; apps like Nihongo Pro and Mojiyomi turn a scan into word lookups and word flashcards. Android has system-wide OCR overlays (Poe) that export to Anki; iOS has no equivalent.
- **The gap:** a phone-first tool where one screenshot becomes a complete sentence card (sentence, reading, translation, vocabulary, audio) in one step, with captions burned into short-form video handled well.
- **Limit:** DRM-protected streaming apps can blank screenshots, so services like Netflix may not be capturable this way.

## Goals

- Go from a screenshot to a complete card with no typing.
- Capture and review entirely from the phone.
- Every field on a card is something a beginner can check: a dictionary headword, a kana reading, a natural translation.
- Hear the sentence and each word spoken.
- Keep cards and come back to them.
- Choose each model in the pipeline from measurements on real screenshots, so the trade-offs between models are understood, not guessed.

## Non-goals

- Multi-user support, accounts, or public hosting.
- Part of speech, literal translation, romaji: hard for a beginner to check, so they can't be evaluated.
- Studying cards (spaced repetition, quizzes) and the conversation partner: separate requirements.
- Editing a card's generated content.
- Live in-app camera capture.

## User

The builder: a beginner learning Japanese who watches Japanese video daily, mostly on a phone.

## User workflow

**Without the app**
1. Pause on a caption with an unfamiliar phrase.
2. Retype it into a dictionary or translator.
3. Look up words one at a time, with no pronunciation.
4. Resume the video; nothing is saved.

**With the app**
1. Pause and screenshot.
2. Give the screenshot to the app from the phone.
3. Get a card: sentence with furigana, translation, vocabulary, audio.
4. The card is saved and can be reopened later.

## Requirements

Priority: **P0** the core card, **P1** a usable app, **P2** later.

| ID | Requirement | Priority |
|---|---|---|
| R1 | Read the Japanese caption from a screenshot exactly as written. | P0 |
| R2 | Give a hiragana reading of the sentence. | P0 |
| R3 | Give a natural English translation. | P0 |
| R4 | List every content word once, as a dictionary headword checkable on Jisho, with the written and dictionary forms, both readings, and the dictionary form's meaning. | P0 |
| R5 | Record the model, cost and time for every card made. | P0 |
| R6 | Show furigana over kanji only, correctly placed. | P1 |
| R7 | Play audio for the sentence and for each vocabulary word. | P1 |
| R8 | Save cards so they survive a restart; list and reopen them. | P1 |
| R9 | Create and view cards from a web page on the phone. | P1 |
| R10 | Keep or delete a card before it's saved. | P2 |
| R11 | A short grammar note on the sentence. | P2 |

## Non-functional requirements

- **Cost:** a few cents per card at most.
- **Privacy:** screenshots are other people's content and are never published; code and docs are public.
- **Failure:** a malformed model response fails loudly. A card built on a misread caption fails silently, so accuracy is measured on an evaluation set rather than assumed.

## Success metrics

- Accuracy per field (caption text, readings, vocabulary headwords) on the evaluation set, per model.
- Cost and time per card, per model.
- A written decision, with the reasoning, for each model choice in the pipeline.

## Open questions

- How to grade expected outputs at a beginner level: hand-check caption and readings only, or cross-check two frontier models.
- Whether cards get an illustration.
- Name readings can't be verified by lookup; grading needs a "plausible" grade for them.
