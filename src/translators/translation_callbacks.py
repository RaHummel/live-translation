from dataclasses import dataclass
from typing import Callable


@dataclass
class TranslationCallbacks:
    """A dataclass to hold callback functions for translation events."""

    update_source_field: Callable[[str], None]
    update_target_field: Callable[[str, str], None]
