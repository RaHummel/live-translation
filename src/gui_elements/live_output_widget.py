import datetime
import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLayout,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.model.config_models import TranslatorSettings
from gui_elements.text_edit_logger import QTextEditLogger

LOGGER = logging.getLogger(__name__)


class LiveOutputWidget(QWidget):
    def __init__(self, translator_settings: TranslatorSettings, text_edit_logger: QTextEditLogger, parent=None):
        super().__init__(parent)
        self._translator_settings = translator_settings
        self.target_transcript_widgets = {}
        self.target_transcript_labels = {}
        self.target_transcript_checkboxes = {}
        self.target_transcript_layouts = {}

        self._setup_ui()
        self._setup_logger(text_edit_logger)

    def update_settings(self, translator_settings: TranslatorSettings):
        """
        Applies the transcription settings to the live output dashboard.
        Args:
            translator_settings (TranslatorSettings): User specific translator settings.
        """

        self.show_source_transcript_checkbox.setChecked(translator_settings.aws_settings.show_source_transcript)

        for lang, lang_setting in translator_settings.aws_settings.target_languages.items():
            is_checked = lang_setting.show_transcript
            self.target_transcript_checkboxes[lang].setChecked(is_checked)

        self._translator_settings = translator_settings

    def _setup_ui(self):
        live_outputs_layout = QVBoxLayout(self)
        live_outputs_layout.setContentsMargins(0, 0, 0, 0)

        self.live_output_tabs = QTabWidget(tabPosition=QTabWidget.TabPosition.North)
        self.live_output_tabs.tabBar().setUsesScrollButtons(False)

        self.transcripts_tab_content = QWidget()
        self.transcripts_tab_layout = QVBoxLayout(self.transcripts_tab_content)

        self.source_transcript_checkbox_layout = QHBoxLayout()
        self.show_source_transcript_checkbox = QCheckBox('Show Source Language Transcript')
        self.show_source_transcript_checkbox.setChecked(self._translator_settings.aws_settings.show_source_transcript)
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

        for lang_code, lang_setting in self._translator_settings.aws_settings.target_languages.items():
            self.update_target_transcript_outputs(lang_code, lang_setting.show_transcript)

        self.logs_tab_content = QWidget()
        logs_tab_layout = QVBoxLayout(self.logs_tab_content)
        self.log_output = QTextEdit(readOnly=True)
        self.log_output.setPlaceholderText('Application logs will appear here...')
        self.log_output.setStatusTip('Change log level in the settings to see more details.')
        logs_tab_layout.addWidget(self.log_output, 2)

        self.live_output_tabs.addTab(self.transcripts_tab_content, 'Transcripts')
        self.live_output_tabs.addTab(self.logs_tab_content, 'Logs')

        live_outputs_layout.addWidget(self.live_output_tabs, 1)

        self.setLayout(live_outputs_layout)

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
                text_edit = self.target_transcript_widgets.get(lang_code)
                text_edit.clear()

                lang_display_layout = self.target_transcript_layouts.pop(lang_code)

                while lang_display_layout.count():
                    item = lang_display_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                    elif item.layout():
                        self._clear_layout(item.layout())
                        item.layout().deleteLater()
                lang_display_layout.deleteLater()

                self.target_transcript_labels.pop(lang_code, None)
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

        # Automatically scroll to the bottom of the source transcript output
        self.source_transcript_output.verticalScrollBar().setValue(
            self.source_transcript_output.verticalScrollBar().maximum()
        )

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
        # Automatically scroll to the bottom of the target transcript output
        text_edit.verticalScrollBar().setValue(text_edit.verticalScrollBar().maximum())

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

    def _clear_layout(self, layout: QLayout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
                item.layout().deleteLater()

    def _setup_logger(self, text_edit_logger: QTextEditLogger):
        text_edit_logger.connect_slot(self.append_log)

    def append_log(self, text: str):
        """
        Appends a log message to the log_output QTextEdit.
        This method is now a slot connected to the QTextEditLogger's signal.
        """
        self.log_output.append(text)
        self._trim_textedit_lines(self.log_output)

        # Automatically scroll to the bottom of the log output
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

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
