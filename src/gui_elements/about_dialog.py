from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from utils.version import get_app_version


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('About Live Translation')
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        title = QLabel('<h2>Live Translation</h2>')
        version_str = get_app_version()
        version = QLabel(f'Version: {version_str}')
        description = QLabel(
            'Real-time speech translation service with multi-language audio output.\n\n'
            'For more information and to report issues, visit the project on GitHub.'
        )
        description.setWordWrap(True)

        authors = QLabel('Authors: Matthias Kuczera, Raimund Hummel')
        license_label = QLabel('License: GPL-3.0-or-later')
        authors.setWordWrap(True)
        license_label.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(description)
        layout.addWidget(authors)
        layout.addWidget(license_label)

        links = QHBoxLayout()
        homepage_btn = QPushButton('Homepage')
        issues_btn = QPushButton('Report Issue')
        homepage_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl('https://github.com/RaHummel/live-translation'))
        )
        issues_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl('https://github.com/RaHummel/live-translation/issues'))
        )
        links.addWidget(homepage_btn)
        links.addWidget(issues_btn)
        layout.addLayout(links)

        ok = QPushButton('OK')
        ok.clicked.connect(self.accept)
        layout.addWidget(ok, alignment=Qt.AlignmentFlag.AlignRight)
