import datetime
import logging
from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.model.config_models import AWSSettings, GoogleSettings, TranslatorSettings
from gui_elements.base_translator_widget import clear_layout

LOGGER = logging.getLogger(__name__)


class LiveOutputWidget(QWidget):
    def __init__(self, translator_settings: TranslatorSettings, parent=None):
        super().__init__(parent)
        self._translator_settings = translator_settings
        self.target_transcript_widgets: Dict[str, QTextEdit] = {}
        self.target_transcript_checkboxes: Dict[str, QCheckBox] = {}
        self.target_transcript_layouts: Dict[str, QVBoxLayout] = {}

        self._setup_ui()

    def update_settings(self, translator_settings: TranslatorSettings):
        """
        Applies the transcription settings to the live output dashboard.
        Args:
            translator_settings (TranslatorSettings): User specific translator settings.
        """
        self._translator_settings = translator_settings
        provider_settings = self._get_active_provider_settings(translator_settings)
        self.show_source_transcript_checkbox.setChecked(provider_settings.show_source_transcript)

        desired_target_states = {
            lang: lang_setting.show_transcript for lang, lang_setting in provider_settings.target_languages.items()
        }

        for lang in list(self.target_transcript_widgets):
            if lang not in desired_target_states:
                self.update_target_transcript_outputs(lang, False)

        for lang, is_checked in desired_target_states.items():
            self.update_target_transcript_outputs(lang, is_checked)

    def _setup_ui(self):
        live_outputs_layout = QVBoxLayout(self)
        live_outputs_layout.setContentsMargins(0, 0, 0, 0)

        transcripts_content = QWidget()
        self.transcripts_tab_layout = QVBoxLayout(transcripts_content)

        self.source_transcript_checkbox_layout = QHBoxLayout()
        self.show_source_transcript_checkbox = QCheckBox('Show Source Language Transcript')
        provider_settings = self._get_active_provider_settings(self._translator_settings)
        self.show_source_transcript_checkbox.setChecked(provider_settings.show_source_transcript)
        self.show_source_transcript_checkbox.setToolTip('Toggle visibility of the source language transcript.')
        self.show_source_transcript_checkbox.setStatusTip('Enable or disable the source language transcript output.')
        self.show_source_transcript_checkbox.toggled.connect(self._toggle_source_transcript_visibility)
        self.source_transcript_checkbox_layout.addWidget(self.show_source_transcript_checkbox)
        self.source_transcript_checkbox_layout.addStretch(1)

        self.source_transcript_output = QTextEdit(readOnly=True)
        self.source_transcript_output.setPlaceholderText('Source language transcript will appear here...')
        self.source_transcript_output.setMinimumHeight(100)

        self.transcripts_tab_layout.addLayout(self.source_transcript_checkbox_layout)
        self.transcripts_tab_layout.addWidget(self.source_transcript_output)

        separator_line = QFrame(frameShape=QFrame.Shape.HLine, frameShadow=QFrame.Shadow.Sunken)
        separator_line.setFixedHeight(1)
        self.transcripts_tab_layout.addWidget(separator_line)

        self.target_transcripts_scroll_area = QScrollArea(widgetResizable=True)
        self.target_transcripts_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.target_transcripts_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.target_transcripts_dynamic_content = QWidget()
        self.target_transcripts_dynamic_layout = QVBoxLayout(self.target_transcripts_dynamic_content)
        self.target_transcripts_scroll_area.setWidget(self.target_transcripts_dynamic_content)
        self.transcripts_tab_layout.addWidget(self.target_transcripts_scroll_area, 1)

        for lang_code, lang_setting in provider_settings.target_languages.items():
            self.update_target_transcript_outputs(lang_code, lang_setting.show_transcript)

        live_outputs_layout.addWidget(transcripts_content, 1)

        self.setLayout(live_outputs_layout)

    def _get_active_provider_settings(self, translator_settings: TranslatorSettings) -> AWSSettings | GoogleSettings:
        if translator_settings.translator == 'google':
            return translator_settings.google_settings
        return translator_settings.aws_settings

    def _toggle_source_transcript_visibility(self, checked: bool):
        self.source_transcript_output.setVisible(checked)

        if not checked:
            self.source_transcript_output.clear()

    def update_target_transcript_outputs(self, lang_code: str, is_checked: bool) -> None:
        """
        Updates the target transcript output widgets based on the checkbox state.
        If the checkbox is checked, it creates a new widget for the target language transcript.
        If unchecked, it removes the existing widget for that language.

        Args:
            lang_code (str): The language code for the target transcript.
            is_checked (bool): The state of the checkbox indicating whether to show or hide the transcript
        """
        if is_checked:
            if lang_code not in self.target_transcript_widgets:
                lang_display_layout = QVBoxLayout()
                checkbox = QCheckBox(f'Show Transcript ({lang_code})')
                checkbox.setChecked(True)
                checkbox.setToolTip(f'Toggle visibility of the {lang_code} transcript.')
                checkbox.setStatusTip(f'Enable or disable the {lang_code} transcript output.')
                text_edit = QTextEdit()
                text_edit.setReadOnly(True)
                text_edit.setPlaceholderText(f'Translated transcript for {lang_code} will appear here...')
                text_edit.setMinimumHeight(50)
                text_edit.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)

                checkbox.toggled.connect(text_edit.setVisible)

                lang_display_layout.addWidget(checkbox)
                lang_display_layout.addWidget(text_edit)
                lang_display_layout.addSpacing(10)

                self.target_transcript_layouts[lang_code] = lang_display_layout
                self.target_transcript_checkboxes[lang_code] = checkbox
                self.target_transcript_widgets[lang_code] = text_edit

                self.target_transcripts_dynamic_layout.insertLayout(
                    self.target_transcripts_dynamic_layout.count() - 1, lang_display_layout
                )
        else:
            if lang_code in self.target_transcript_widgets:
                text_edit = self.target_transcript_widgets[lang_code]
                text_edit.clear()

                lang_display_layout = self.target_transcript_layouts.pop(lang_code)

                while lang_display_layout.count():
                    item = lang_display_layout.takeAt(0)
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
                lang_display_layout.deleteLater()

                self.target_transcript_checkboxes.pop(lang_code, None)
                self.target_transcript_widgets.pop(lang_code, None)

        self.target_transcripts_dynamic_content.adjustSize()
        self.target_transcripts_scroll_area.updateGeometry()

    def update_source_transcription_field(self, text: str):
        """
        Updates the source transcript output widget with the provided text.
        This method is called to append new text to the source transcript output.

        Args:
            text (str): The text to append to the source transcript output.
        """

        # Check if the source transcript output is visible before appending text
        if not self.show_source_transcript_checkbox.isChecked():
            return

        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.source_transcript_output.append(f'[{timestamp}] {text}')
        self._trim_textedit_lines(self.source_transcript_output)
        self._scroll_to_latest_entry(self.source_transcript_output)

    def update_target_transcription_field(self, lang_code: str, text: str):
        """
        Updates the target transcript output widget for a specific language with the provided text.
        This method is called to append new text to the target transcript output.

        Args:
            lang_code (str): The language code for the target transcript.
            text (str): The text to append to the target transcript output.
        """

        if lang_code not in self.target_transcript_widgets:
            return

        checkbox = self.target_transcript_checkboxes.get(lang_code)

        if not checkbox or not checkbox.isChecked():
            return

        timestamp = datetime.datetime.now().strftime('%H:%M:%S')

        text_edit = self.target_transcript_widgets[lang_code]
        text_edit.append(f'[{timestamp}] {text}')
        self._trim_textedit_lines(text_edit)
        self._scroll_to_latest_entry(text_edit)

    @staticmethod
    def _scroll_to_latest_entry(text_edit: QTextEdit) -> None:
        """Ensure the newest appended line is visible in QTextEdit."""
        cursor = text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        text_edit.setTextCursor(cursor)
        text_edit.ensureCursorVisible()

    @staticmethod
    def _trim_textedit_lines(text_edit: QTextEdit, max_lines: int = 500, remove_batch: int = 20):
        """Trims the number of lines in a QTextEdit to a maximum number of lines."""

        doc = text_edit.document()
        # TODO : Make max_lines configurable via settings
        if doc.blockCount() > max_lines:
            cursor = text_edit.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            for _ in range(min(remove_batch, doc.blockCount() - max_lines)):
                cursor.select(cursor.SelectionType.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()

    def append_source_transcript(self, text: str):
        self.source_transcript_output.append(text)

    def append_target_transcript(self, lang_code: str, text: str):
        if lang_code in self.target_transcript_widgets:
            self.target_transcript_widgets[lang_code].append(text)

    def clear_transcripts(self):
        """Clears all transcript output widgets."""
        LOGGER.debug('Clearing all transcripts.')
        self.source_transcript_output.clear()
        for text_edit in self.target_transcript_widgets.values():
            text_edit.clear()
