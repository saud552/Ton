"""Localization service based on JSON resources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class LocalizationService:
    def __init__(self, locales_dir: Path, default_language: str = "ar"):
        self._default_language = default_language
        self._bundles: Dict[str, Dict[str, Any]] = {}
        self._load_locales(locales_dir)

    def _load_locales(self, locales_dir: Path) -> None:
        if not locales_dir.exists():
            raise FileNotFoundError(f"Locales directory not found: {locales_dir}")
        for file in locales_dir.glob("*.json"):
            with file.open("r", encoding="utf-8") as fp:
                self._bundles[file.stem] = json.load(fp)
        if self._default_language not in self._bundles:
            raise ValueError("Default language bundle is missing")

    def available_languages(self) -> Dict[str, str]:
        langs = {}
        for lang, bundle in self._bundles.items():
            langs[lang] = bundle.get("languages", {}).get(lang, lang)
        return langs

    def gettext(self, language: str, key: str, **kwargs) -> str:
        bundle = self._bundles.get(language) or self._bundles[self._default_language]
        value = self._resolve(bundle, key.split("."))
        if value is None:
            value = self._resolve(self._bundles[self._default_language], key.split("."))
        if value is None:
            return key
        if kwargs:
            return value.format(**kwargs)
        return value

    def _resolve(self, bundle: Dict[str, Any], parts) -> Any:
        data = bundle
        for part in parts:
            if isinstance(data, dict) and part in data:
                data = data[part]
            else:
                return None
        return data


__all__ = ["LocalizationService"]
