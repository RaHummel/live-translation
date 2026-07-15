"""Human-readable display names for BCP-47 / provider language codes.

Backend logic (translator APIs, config dict keys, Mumble usernames, etc.) must
keep using the raw language codes (e.g. ``de-DE``). This module is only meant
to provide a friendlier label for the GUI (comboboxes, checkboxes, channel
names), falling back to the raw code whenever ``langcodes`` cannot resolve it
(e.g. non-standard tags like ``en-GB-WLS``).
"""

import logging
from functools import lru_cache
from typing import Iterable, List

import langcodes

LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def display_name(lang_code: str) -> str:
    """Return a human-readable display name for *lang_code*.

    Falls back to *lang_code* itself if it cannot be resolved (e.g. malformed
    or non-standard tags such as ``en-GB-WLS``).
    """
    try:
        return langcodes.Language.get(lang_code).display_name()
    except Exception as e:
        LOGGER.debug('Could not resolve display name for "%s": %s', lang_code, e)
        return lang_code


def sorted_by_display_name(lang_codes: Iterable[str]) -> List[str]:
    """Return *lang_codes* sorted alphabetically by their display name."""
    return sorted(lang_codes, key=lambda code: display_name(code).casefold())
