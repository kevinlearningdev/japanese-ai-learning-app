from pydantic import BaseModel, Field


class VocabEntry(BaseModel):
    written_form: str = Field(
        description="The word exactly as it appears in the sentence, including any conjugation."
    )
    written_reading: str = Field(description="Hiragana reading of the written form.")
    dictionary_form: str = Field(
        description="The form you would look up in a dictionary."
    )
    dictionary_reading: str = Field(
        description="Hiragana reading of the dictionary form."
    )
    meaning: str = Field(description="Short English meaning of the dictionary form.")


class Card(BaseModel):
    sentence: str = Field(
        description="The Japanese text from the screenshot, exactly as written."
    )
    reading: str = Field(description="Hiragana reading of the whole sentence.")
    translation: str = Field(description="Natural English translation.")
    vocab: list[VocabEntry]
