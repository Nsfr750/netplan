"""
gui_dialogs.py
Finestre di dialogo della GUI: visualizzatore log con filtri,
impostazioni, guida, sponsor e informazioni.
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices, QFont, QPixmap
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from about import get_about_text
from help import get_help_text
from lang.language_manager import LanguageManager, get_language, tr
from logger import LOG_FILE
from settings import get_setting, set_setting
from sponsor import get_sponsor_info, make_qr_png
from view_log import LOG_LEVELS, read_log


class LogViewerDialog(QDialog):
    """Visualizzatore di logs/netplan.log con filtri livello/testo."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(tr("log_dialog_title"))
        self.resize(900, 560)

        layout = QVBoxLayout(self)
        filters = QHBoxLayout()

        self.lbl_level = QLabel(tr("filter_level"))
        filters.addWidget(self.lbl_level)
        self.combo_level = QComboBox()
        self.combo_level.addItem(tr("all_levels"), None)
        for level in LOG_LEVELS:
            self.combo_level.addItem(level, level)
        self.combo_level.currentIndexChanged.connect(self._reload)
        filters.addWidget(self.combo_level)

        self.lbl_text = QLabel(tr("filter_text"))
        filters.addWidget(self.lbl_text)
        self.edit_text = QLineEdit()
        self.edit_text.setPlaceholderText(tr("filter_text_placeholder"))
        self.edit_text.textChanged.connect(self._reload)
        filters.addWidget(self.edit_text, 1)

        self.btn_refresh = QPushButton(tr("refresh"))
        self.btn_refresh.clicked.connect(self._reload)
        filters.addWidget(self.btn_refresh)
        layout.addLayout(filters)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.text)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._reload()

    def _reload(self):
        """Rilegge il log applicando livello e testo correnti."""
        entries = read_log(
            LOG_FILE,
            level=self.combo_level.currentData(),
            text=self.edit_text.text().strip() or None,
        )
        if not entries:
            self.text.setPlainText(
                tr("log_file_missing", path=LOG_FILE)
                if not os.path.exists(LOG_FILE)
                else tr("log_empty")
            )
            return
        self.text.setPlainText("\n".join(e["raw"] for e in entries))
        self.text.verticalScrollBar().setValue(self.text.verticalScrollBar().maximum())


class SettingsDialog(QDialog):
    """Impostazioni dell'applicazione (persistite con QSettings)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(tr("settings_dialog_title"))
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)

        row_lang = QHBoxLayout()
        row_lang.addWidget(QLabel(tr("settings_language")))
        self.combo_lang = QComboBox()
        for code, name in LanguageManager.instance().available_languages().items():
            self.combo_lang.addItem(name, code)
        current = get_setting("language")
        idx = self.combo_lang.findData(current)
        self.combo_lang.setCurrentIndex(max(0, idx))
        row_lang.addWidget(self.combo_lang, 1)
        layout.addLayout(row_lang)

        row_out = QHBoxLayout()
        row_out.addWidget(QLabel(tr("settings_outdir")))
        self.edit_outdir = QLineEdit(get_setting("outdir"))
        row_out.addWidget(self.edit_outdir, 1)
        btn_browse = QPushButton(tr("browse"))
        btn_browse.clicked.connect(self._pick_outdir)
        row_out.addWidget(btn_browse)
        layout.addLayout(row_out)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr("settings_save"))
        buttons.button(QDialogButtonBox.Cancel).setText(tr("settings_cancel"))
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.language_changed = False

    def _pick_outdir(self):
        path = QFileDialog.getExistingDirectory(self, tr("select_outdir_title"))
        if path:
            self.edit_outdir.setText(path)

    def _save(self):
        """Persiste le preferenze e segnala se la lingua è cambiata."""
        new_lang = self.combo_lang.currentData()
        self.language_changed = new_lang != get_setting("language")
        set_setting("language", new_lang)
        set_setting("outdir", self.edit_outdir.text().strip() or "output")
        self.accept()


class HelpDialog(QDialog):
    """Mostra il testo della guida (help.py) nella lingua corrente."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(tr("help_dialog_title"))
        self.resize(640, 560)
        layout = QVBoxLayout(self)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Consolas", 9))
        text.setPlainText(get_help_text(get_language()))
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class SponsorDialog(QDialog):
    """Finestra per il supporto del progetto: PayPal, Monero, GitHub."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        info = get_sponsor_info()
        self.setWindowTitle(tr("sponsor_dialog_title"))
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(tr("sponsor_intro")))

        row = QHBoxLayout()
        qr = make_qr_png(info["paypal"])
        if qr:
            lbl_qr = QLabel()
            pix = QPixmap()
            pix.loadFromData(qr)
            lbl_qr.setPixmap(pix)
            row.addWidget(lbl_qr, 0, Qt.AlignTop)

        col = QVBoxLayout()
        btn_paypal = QPushButton(tr("sponsor_paypal"))
        btn_paypal.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(info["paypal"]))
        )
        col.addWidget(btn_paypal)

        btn_github = QPushButton(tr("sponsor_github"))
        btn_github.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(info["github"]))
        )
        col.addWidget(btn_github)
        col.addStretch(1)
        row.addLayout(col, 1)
        layout.addLayout(row)

        row_xmr = QHBoxLayout()
        row_xmr.addWidget(QLabel(tr("sponsor_monero")))
        edit_xmr = QLineEdit(info["monero"])
        edit_xmr.setReadOnly(True)
        row_xmr.addWidget(edit_xmr, 1)
        btn_copy = QPushButton(tr("copy"))
        btn_copy.clicked.connect(
            lambda: self._copy_to_clipboard(edit_xmr.text(), btn_copy)
        )
        row_xmr.addWidget(btn_copy)
        layout.addLayout(row_xmr)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _copy_to_clipboard(self, text: str, button: QPushButton):
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(text)
        button.setText(tr("copied"))


class AboutDialog(QDialog):
    """Finestra Informazioni sull'applicazione."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(tr("about_dialog_title"))
        layout = QVBoxLayout(self)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(get_about_text())
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
