import logging
from abc import abstractmethod
from typing import Dict, List

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from config.model.config_models import LanguageSettings
from constants import TRANSLATOR
from utils.language_names import display_name, sorted_by_display_name

LOGGER = logging.getLogger(__name__)


class BaseTranslatorProviderWidget(QWidget):
    """
    Abstract base for provider-specific translator widgets (AWS, Google, etc.).
    Handles the shared target-language grid, engine/voice selection, and state management.
    Subclasses implement provider-specific connection UI and settings hooks.
    """

    target_lang_toggled = Signal(str, bool)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.target_lang_checkboxes: Dict[str, QCheckBox] = {}
        self.voice_selectors: Dict[str, QComboBox] = {}
        self.target_lang_containers: Dict[str, QWidget] = {}
        self.language_engines_state: Dict[str, str] = {}
        self.language_voices_state: Dict[str, str] = {}
        self._highlight_timer: QTimer | None = None

    @abstractmethod
    def _get_provider_key(self) -> str:
        """Return the key in TRANSLATOR dict, e.g. 'aws' or 'google'."""

    @abstractmethod
    def _get_engine_names(self) -> List[str]:
        """Return available engine names, e.g. ['standard', 'neural']."""

    @abstractmethod
    def _build_connection_ui(self, parent_layout: QVBoxLayout) -> None:
        """Build provider-specific connection/credential widgets into *parent_layout*."""

    @abstractmethod
    def _get_source_language(self) -> str:
        """Return currently selected source language text."""

    @abstractmethod
    def _get_source_language_combo(self) -> QComboBox:
        """Return the source language QComboBox instance."""

    def _build_extra_source_options(self, layout: QHBoxLayout) -> None:
        """Override to add widgets next to the source language / engine combos."""

    def _build_extra_language_options(self, layout: QFormLayout) -> None:
        """Override to add extra rows below the source language form (e.g. endpointing)."""

    def _build_extra_engine_options(self, layout: QHBoxLayout) -> None:
        """Override to add widgets directly next to the engine combo (same row)."""

    def _setup_language_ui(self, parent_layout: QVBoxLayout) -> None:
        """Builds the shared Language Settings group (source + target grid)."""
        language_settings_group = QGroupBox('Language Settings')
        language_settings_layout = QVBoxLayout(language_settings_group)

        source_lang_form_layout = QFormLayout(fieldGrowthPolicy=QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        source_lang_layout = QHBoxLayout()
        source_lang_layout.addWidget(self._get_source_language_combo())
        self._build_extra_source_options(source_lang_layout)
        source_lang_layout.addStretch()
        source_lang_form_layout.addRow('Source Language:', source_lang_layout)

        engine_layout = QHBoxLayout()
        self.engine_select = QComboBox()
        self.engine_select.addItems(self._get_engine_names())
        self.engine_select.setCurrentText(self._get_engine_names()[0])
        self.engine_select.setToolTip(
            'Selects the synthesis/recognition engine tier. Different engines offer different '
            'languages, voices and quality/latency trade-offs.'
        )
        self.engine_select.setStatusTip('Choose the engine tier used for translation/voices.')
        self.engine_select.currentTextChanged.connect(self._on_engine_changed)
        self.engine_select.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._build_extra_engine_options(engine_layout)
        engine_label = QLabel('Engine:')
        engine_layout.addWidget(engine_label)
        engine_layout.addWidget(self.engine_select)
        engine_layout.addStretch()
        source_lang_form_layout.addRow(engine_layout)

        self._build_extra_language_options(source_lang_form_layout)
        language_settings_layout.addLayout(source_lang_form_layout)

        target_lang_label = QLabel('Translation Target Languages:')
        language_settings_layout.addWidget(target_lang_label)

        self.target_lang_search = QLineEdit()
        self.target_lang_search.setPlaceholderText('Search language…')
        self.target_lang_search.setClearButtonEnabled(True)
        self.target_lang_search.setStatusTip('Scroll to a target language.')
        self.target_lang_search.setToolTip('Type a display name to automatically scroll to the matching language.')
        self.target_lang_search.textChanged.connect(self._on_search_text_changed)
        language_settings_layout.addWidget(self.target_lang_search)

        # Target grid in scroll area
        self.target_scroll_area = QScrollArea(widgetResizable=True)
        self.target_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.target_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.scroll_content_widget = QWidget()
        self.target_grid_layout = QGridLayout(self.scroll_content_widget)
        self.target_grid_layout.setContentsMargins(5, 5, 5, 5)
        self.target_grid_layout.setSpacing(10)
        self.target_grid_layout.setColumnStretch(0, 1)
        self.target_grid_layout.setColumnStretch(1, 1)

        self.target_scroll_area.setWidget(self.scroll_content_widget)
        language_settings_layout.addWidget(self.target_scroll_area)
        parent_layout.addWidget(language_settings_group)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

    def _init_target_state(self, target_languages: Dict[str, LanguageSettings]) -> None:
        """Populate internal state dicts from settings and build the initial grid."""
        for lang, lang_setting in target_languages.items():
            self.language_engines_state[lang] = lang_setting.engine
            self.language_voices_state[lang] = lang_setting.voice_id

        self._build_target_grid(self.engine_select.currentText(), self._get_source_language())

    def _apply_target_language_state(self, target_languages: Dict[str, LanguageSettings]) -> None:
        """Re-apply target language state from updated settings."""
        self.language_engines_state.clear()
        self.language_voices_state.clear()

        for lang, lang_setting in target_languages.items():
            self.language_engines_state[lang] = lang_setting.engine
            self.language_voices_state[lang] = lang_setting.voice_id

        if hasattr(self, 'engine_select'):
            self._build_target_grid(self.engine_select.currentText(), self._get_source_language())

    def _on_engine_changed(self, new_engine: str) -> None:
        self._build_target_grid(new_engine, self._get_source_language())

    def _update_target_languages(self, selected_source: str) -> None:
        self._build_target_grid(self.engine_select.currentText(), selected_source)

    def _build_target_grid(self, selected_engine: str, selected_source: str) -> None:
        clear_layout(self.target_grid_layout)
        self.target_lang_checkboxes.clear()
        self.voice_selectors.clear()
        self.target_lang_containers.clear()

        provider_key = self._get_provider_key()
        if selected_engine not in TRANSLATOR[provider_key]:
            return

        languages_for_engine = sorted_by_display_name(TRANSLATOR[provider_key][selected_engine].keys())

        row = 0
        col = 0
        num_cols = 2

        for lang in languages_for_engine:
            lang_label = display_name(lang)
            lang_selection_layout = QVBoxLayout()
            lang_selection_layout.setContentsMargins(0, 0, 0, 0)

            checkbox = QCheckBox(lang_label)

            assigned_engine = self.language_engines_state.get(lang)
            is_checked = assigned_engine is not None
            checkbox.blockSignals(True)
            checkbox.setChecked(is_checked)
            checkbox.blockSignals(False)

            is_source = lang == selected_source
            different_engine = is_checked and assigned_engine != selected_engine
            checkbox.setEnabled(not is_source and not different_engine)

            if different_engine:
                checkbox.setText(f'{lang_label} (in {assigned_engine})')
                font = checkbox.font()
                font.setStrikeOut(True)
                checkbox.setFont(font)
                checkbox.setToolTip(f"Already selected in '{assigned_engine}' engine.")
            elif is_source:
                checkbox.setToolTip('Cannot select source language as target.')
            else:
                checkbox.setToolTip(f'Enable translation to {lang_label}.')

            checkbox.toggled.connect(lambda state, la=lang, eng=selected_engine: self._on_lang_toggled(la, state, eng))

            voice_selector = QComboBox()
            voices = TRANSLATOR[provider_key][selected_engine][lang].get('voice_ids', [])
            voice_selector.addItems(voices)

            if is_checked and not different_engine:
                voice_selector.setEnabled(True)
                voice_id = self.language_voices_state.get(lang)
                if voice_id is not None and voice_id in voices:
                    voice_selector.setCurrentText(voice_id)
            else:
                voice_selector.setEnabled(False)

            voice_selector.currentTextChanged.connect(lambda text, la=lang: self._on_voice_changed(la, text))
            checkbox.toggled.connect(
                lambda state, vs=voice_selector, la=lang, eng=selected_engine: self._toggle_voice_selector(
                    state, vs, la, eng
                )
            )

            lang_selection_layout.addWidget(checkbox)
            lang_selection_layout.addWidget(voice_selector)

            lang_container = QWidget()
            lang_container.setLayout(lang_selection_layout)
            self.target_grid_layout.addWidget(lang_container, row, col)

            col += 1
            if col >= num_cols:
                col = 0
                row += 1

            self.target_lang_checkboxes[lang] = checkbox
            self.voice_selectors[lang] = voice_selector
            self.target_lang_containers[lang] = lang_container

        if col > 0:
            self.target_grid_layout.addItem(
                QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum),
                row,
                col,
            )
        self.target_grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding),
            row + 1,
            0,
            1,
            num_cols,
        )

    def _on_search_text_changed(self, text: str) -> None:
        """Scrolls the target-language grid to the first language whose display name matches *text*."""
        search_text = text.strip().lower()
        if not search_text:
            return

        for lang, _checkbox in self.target_lang_checkboxes.items():
            if search_text in display_name(lang).lower():
                container = self.target_lang_containers.get(lang)
                if container is not None:
                    self.target_scroll_area.ensureWidgetVisible(container)
                    self._highlight_container(container)
                break

    def _highlight_container(self, container: QWidget) -> None:
        """Briefly highlights *container* so the scrolled-to result is visually noticeable."""
        if self._highlight_timer is not None:
            self._highlight_timer.stop()

        container.setStyleSheet('background-color: rgba(0, 102, 204, 90); border-radius: 4px;')

        self._highlight_timer = QTimer(self)
        self._highlight_timer.setSingleShot(True)
        self._highlight_timer.timeout.connect(lambda: container.setStyleSheet(''))
        self._highlight_timer.start(1000)

    def _on_lang_toggled(self, lang: str, state: bool, engine: str) -> None:
        if state:
            self.language_engines_state[lang] = engine
            self.language_voices_state[lang] = self.voice_selectors[lang].currentText()
        else:
            self.language_engines_state.pop(lang, None)
            self.language_voices_state.pop(lang, None)

        self.target_lang_toggled.emit(lang, state)

    def _on_voice_changed(self, lang: str, text: str) -> None:
        if lang in self.language_engines_state:
            self.language_voices_state[lang] = text

    def _toggle_voice_selector(self, state: bool, voice_selector: QComboBox, lang: str, engine: str) -> None:
        provider_key = self._get_provider_key()
        has_voices = TRANSLATOR[provider_key][engine][lang].get('voice_ids', [])
        voice_selector.setEnabled(state and (lang != self._get_source_language()) and bool(has_voices))

    def get_target_language_settings(self) -> Dict[str, dict]:
        """Return current target language settings as {lang: {'voice_id': ..., 'engine': ...}}."""
        for lang, cb in self.target_lang_checkboxes.items():
            if cb.isChecked() and cb.isEnabled():
                self.language_voices_state[lang] = self.voice_selectors[lang].currentText()

        settings: Dict[str, dict] = {}
        for lang, engine in self.language_engines_state.items():
            settings[lang] = {
                'voice_id': self.language_voices_state.get(lang, ''),
                'engine': engine,
            }
        return settings


def clear_layout(layout: QLayout) -> None:
    """Recursively remove all items from a layout."""
    while layout.count():
        item = layout.takeAt(0)
        if item is None:
            continue

        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
            continue

        child_layout = item.layout()
        if child_layout is not None:
            clear_layout(child_layout)
            child_layout.deleteLater()
