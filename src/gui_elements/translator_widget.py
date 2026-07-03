import logging
from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QStackedWidget, QVBoxLayout, QWidget

from config.model.config_models import TranslatorSettings
from constants import TRANSLATOR
from gui_elements.aws_widget import AWSWidget
from gui_elements.google_widget import GoogleWidget

LOGGER = logging.getLogger(__name__)


class TranslatorWidget(QWidget):
    provider_changed = Signal(str)

    """
    A widget for configuring translation service settings, including
    provider selection and specific settings for each provider.
    """

    def __init__(self, translator_settings: TranslatorSettings, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._translator_settings = translator_settings
        self._setup_ui()

    def update_settings(self, translator_settings: TranslatorSettings) -> None:
        """
        Updates the translation settings in the widget.

        Args:
            translator_settings (dict): User specific translation settings,
                                        typically loaded from a config file.
        """
        self._translator_settings = translator_settings
        self.translator_select.setCurrentText(translator_settings.translator)
        self.aws_tab_widget.update_settings(translator_settings.aws_settings)
        self.google_tab_widget.update_settings(translator_settings.google_settings)
        self._update_translation_fields(translator_settings.translator)

    def _setup_ui(self) -> None:
        """
        Sets up the user interface for the TranslatorConfigWidget.
        This includes the service selection and a stacked widget for provider-specific settings.
        """
        main_layout = QVBoxLayout(self)

        service_select_group = QGroupBox('Translation Service Selection')
        service_layout = QFormLayout(
            service_select_group,
            labelAlignment=Qt.AlignmentFlag.AlignHCenter,
            formAlignment=Qt.AlignmentFlag.AlignHCenter,
            fieldGrowthPolicy=QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow,
        )

        self.translator_select = QComboBox()
        self.translator_select.addItems(TRANSLATOR.keys())
        self.translator_select.setCurrentText(self._translator_settings.translator)
        self.translator_select.setStatusTip('Select the translation provider.')
        self.translator_select.setToolTip('Choose the translation provider to be used.')
        self.translator_select.currentTextChanged.connect(self._update_translation_fields)

        service_layout.addRow('Service Provider:', self.translator_select)
        main_layout.addWidget(service_select_group)

        self.translator_stacked = QStackedWidget()

        self.aws_tab_widget = AWSWidget(self._translator_settings.aws_settings)
        self.translator_stacked.addWidget(self.aws_tab_widget)

        self.google_tab_widget = GoogleWidget(self._translator_settings.google_settings)
        self.translator_stacked.addWidget(self.google_tab_widget)

        self._provider_widget_map = {
            'aws': self.aws_tab_widget,
            'google': self.google_tab_widget,
        }

        self._update_translation_fields(self._translator_settings.translator)

        main_layout.addWidget(self.translator_stacked, 1)  # Allows the stacked widget to expand vertically
        self.setLayout(main_layout)

    def add_target_lang_signal(self, target_lang_connector: Callable) -> None:
        """
        Connects the target language toggled signal from AWSConfigWidget to an external slot.
        This allows the main application to react to changes in target language selection.

        Args:
            target_lang_connector (Callable): The slot to connect the signal to.
        """
        if not isinstance(self.aws_tab_widget, AWSWidget) or not isinstance(self.google_tab_widget, GoogleWidget):
            LOGGER.error(f'Translator configs not initialized properly in {self.__class__.__name__}')
            return

        self.aws_tab_widget.target_lang_toggled.connect(target_lang_connector)
        self.google_tab_widget.target_lang_toggled.connect(target_lang_connector)

    def add_provider_changed_signal(self, provider_connector: Callable) -> None:
        self.provider_changed.connect(provider_connector)

    def get_translator_settings(self) -> TranslatorSettings:
        return self._translator_settings

    def _update_translation_fields(self, text: str) -> None:
        """
        Updates the displayed translation configuration fields based on the selected service provider.

        Args:
            text (str): The name of the selected translation service provider (e.g., "aws").
        """
        self._translator_settings.translator = text
        widget = self._provider_widget_map.get(text)
        if widget:
            self.translator_stacked.setCurrentWidget(widget)

        self.provider_changed.emit(text)
