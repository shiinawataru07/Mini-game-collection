"""Translation lookup shared by game-specific text catalogs."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from .types import Language

Translations = Mapping[Language, Mapping[str, str]]
Translator = Callable[[Language, str], str]


def translate(translations: Translations, language: Language, key: str) -> str:
    """Return one translated label from a game-owned catalog."""

    return translations[language][key]


def bind_translations(translations: Translations) -> Translator:
    """Create the conventional ``text(language, key)`` game helper."""

    def text(language: Language, key: str) -> str:
        return translate(translations, language, key)

    return text
