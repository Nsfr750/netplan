"""
gui.py
Interfaccia grafica (PySide6) per lo strumento di pianificazione copertura.

Permette di scegliere il file di input, la cartella di output e soglie
personalizzate, avvia l'analisi in un thread separato e mostra riepilogo,
tabelle e grafici prodotti. Menu con voci separate per Log (visualizzatore
con filtri), Impostazioni (preferenze e lingua IT/EN) e Help (guida,
controllo aggiornamenti, sponsor, informazioni).

Uso:
    python gui.py
"""

import os
import sys

import pandas as pd

try:
    from PySide6.QtCore import Qt, QThread, QUrl, Signal
    from PySide6.QtGui import QColor, QDesktopServices, QIcon, QPixmap
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QFileDialog,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    print(
        "PySide6 non installato. Installa le dipendenze con: pip install -r requirements.txt",
        file=sys.stderr,
    )
    sys.exit(1)

from analysis import SEVERITY_COLORS, load_thresholds
from data_reader import DataValidationError
from gui_dialogs import (
    AboutDialog,
    HelpDialog,
    LogViewerDialog,
    SettingsDialog,
    SponsorDialog,
)
from lang.language_manager import set_language, tr
from logger import LOG_DIR
from menu import build_menu_bar, retranslate_menu
from pipeline import run_analysis
from settings import get_setting, set_setting
from update import check_for_updates
from version import __version__


def app_title() -> str:
    """Titolo della finestra con versione, nella lingua corrente."""
    return tr("app_title", version=__version__)


def resource_path(relative: str) -> str:
    """Percorso assoluto di una risorsa, in sviluppo e dopo la compilazione.

    Con Nuitka standalone/onefile i dati inclusi con --include-data-dir si
    trovano accanto all'eseguibile; in sviluppo restano nella root del
    progetto (cartella padre di chi importa questo modulo).
    """
    candidates = []
    if getattr(sys, "frozen", False) or "__compiled__" in globals():
        candidates += [os.path.dirname(sys.executable), os.path.dirname(sys.argv[0])]
    candidates.append(os.path.dirname(os.path.abspath(__file__)))
    for base in candidates:
        path = os.path.join(base, relative)
        if os.path.exists(path):
            return path
    return os.path.join(candidates[-1], relative)


ICON_PATH = resource_path(os.path.join("assets", "icon.png"))


class AnalysisWorker(QThread):
    """Esegue la pipeline in background senza bloccare la GUI."""

    finished_ok = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        input_path: str,
        outdir: str,
        thresholds: dict | None,
        trend_cells: int,
        html_report: bool,
        pdf_report: bool,
        strict: bool,
        allow_subscriber: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.input_path = input_path
        self.outdir = outdir
        self.thresholds = thresholds
        self.trend_cells = trend_cells
        self.html_report = html_report
        self.pdf_report = pdf_report
        self.strict = strict
        self.allow_subscriber = allow_subscriber

    def run(self):
        try:
            result = run_analysis(
                self.input_path,
                self.outdir,
                thresholds=self.thresholds,
                trend_cells=self.trend_cells,
                html_report=self.html_report,
                pdf_report=self.pdf_report,
                strict=self.strict,
                allow_subscriber_data=self.allow_subscriber,
            )
            self.finished_ok.emit(result)
        except (FileNotFoundError, DataValidationError, ValueError) as e:
            self.failed.emit(str(e))
        except Exception as e:  # errori imprevisti mostrati all'utente
            self.failed.emit(f"Errore imprevisto: {e}")

class UpdateWorker(QThread):
    """Controlla gli aggiornamenti su GitHub senza bloccare la GUI."""

    done = Signal(dict)

    def run(self):
        self.done.emit(check_for_updates())


class MainWindow(QMainWindow):
    """Finestra principale dell'applicazione."""

    def __init__(self):
        super().__init__()
        set_language(get_setting("language"))
        self.setWindowTitle(app_title())
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        self.resize(1000, 720)
        self.worker: AnalysisWorker | None = None
        self.update_worker: UpdateWorker | None = None

        self._menu_items = build_menu_bar(self)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        layout.addLayout(self._build_inputs())
        layout.addWidget(self._build_tabs())
        layout.addLayout(self._build_bottom_bar())
        self._load_settings()

    # ----- costruzione UI -------------------------------------------------

    def _build_inputs(self) -> QVBoxLayout:
        box = QVBoxLayout()

        row1 = QHBoxLayout()
        self.lbl_input = QLabel(tr("input_file_label"))
        row1.addWidget(self.lbl_input)
        self.input_edit = QLineEdit()
        row1.addWidget(self.input_edit)
        self.btn_in = QPushButton(tr("browse"))
        self.btn_in.clicked.connect(self._pick_input)
        row1.addWidget(self.btn_in)
        box.addLayout(row1)

        row2 = QHBoxLayout()
        self.lbl_outdir = QLabel(tr("outdir_label"))
        row2.addWidget(self.lbl_outdir)
        self.outdir_edit = QLineEdit("output")
        row2.addWidget(self.outdir_edit)
        self.btn_out = QPushButton(tr("browse"))
        self.btn_out.clicked.connect(self._pick_outdir)
        row2.addWidget(self.btn_out)
        box.addLayout(row2)

        row3 = QHBoxLayout()
        self.lbl_thresholds = QLabel(tr("thresholds_label"))
        row3.addWidget(self.lbl_thresholds)
        self.thresholds_edit = QLineEdit()
        self.thresholds_edit.setPlaceholderText(tr("thresholds_placeholder"))
        row3.addWidget(self.thresholds_edit)
        self.btn_th = QPushButton(tr("browse"))
        self.btn_th.clicked.connect(self._pick_thresholds)
        row3.addWidget(self.btn_th)
        box.addLayout(row3)

        row4 = QHBoxLayout()
        self.chk_html = QCheckBox(tr("opt_html"))
        self.chk_html.setChecked(True)
        self.chk_pdf = QCheckBox(tr("opt_pdf"))
        self.chk_pdf.setChecked(True)
        self.chk_strict = QCheckBox(tr("opt_strict"))
        self.chk_subscriber = QCheckBox(tr("opt_subscriber"))
        row4.addWidget(self.chk_html)
        row4.addWidget(self.chk_pdf)
        row4.addWidget(self.chk_strict)
        row4.addWidget(self.chk_subscriber)
        self.lbl_trend = QLabel(tr("trend_cells_label"))
        row4.addWidget(self.lbl_trend)
        self.spin_trend = QSpinBox()
        self.spin_trend.setRange(1, 30)
        self.spin_trend.setValue(6)
        row4.addWidget(self.spin_trend)
        row4.addStretch(1)
        self.btn_run = QPushButton(tr("run_analysis"))
        self.btn_run.setStyleSheet(
            "background-color:#4C72B0;color:white;font-weight:bold;padding:6px 18px"
        )
        self.btn_run.clicked.connect(self._run)
        row4.addWidget(self.btn_run)
        box.addLayout(row4)

        return box

    def _build_tabs(self) -> QTabWidget:
        self.tabs = QTabWidget()

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.tabs.addTab(self.summary_text, tr("tab_summary"))

        self.table_cells = QTableWidget()
        self.tabs.addTab(self.table_cells, tr("tab_cells"))

        self.table_sites = QTableWidget()
        self.tabs.addTab(self.table_sites, tr("tab_sites"))

        self.table_tech = QTableWidget()
        self.tabs.addTab(self.table_tech, tr("tab_tech"))

        self.table_subscriber = QTableWidget()
        self.tabs.addTab(self.table_subscriber, tr("tab_subscriber"))

        self.charts_area = QScrollArea()
        self.charts_widget = QWidget()
        self.charts_layout = QVBoxLayout(self.charts_widget)
        self.charts_area.setWidget(self.charts_widget)
        self.charts_area.setWidgetResizable(True)
        self.tabs.addTab(self.charts_area, tr("tab_charts"))

        return self.tabs

    def _build_bottom_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        bar.addWidget(self.progress, 1)
        self.btn_close = QPushButton(tr("close"))
        self.btn_close.setStyleSheet(
            "background-color:red;color:white;font-weight:bold;padding:6px 24px"
        )
        self.btn_close.clicked.connect(self.close)
        bar.addWidget(self.btn_close, 0, Qt.AlignRight)
        return bar

    # ----- impostazioni persistenti ----------------------------------------

    def _load_settings(self):
        """Ripristina le preferenze salvate (QSettings)."""
        self.outdir_edit.setText(get_setting("outdir"))
        self.thresholds_edit.setText(get_setting("thresholds"))
        self.spin_trend.setValue(int(get_setting("trend_cells")))
        self.chk_html.setChecked(bool(get_setting("html_report")))
        self.chk_pdf.setChecked(bool(get_setting("pdf_report")))
        self.chk_strict.setChecked(bool(get_setting("strict")))
        self.chk_subscriber.setChecked(bool(get_setting("subscriber")))

    def _save_settings(self):
        """Salva lo stato corrente delle opzioni dell'interfaccia."""
        set_setting("outdir", self.outdir_edit.text().strip() or "output")
        set_setting("thresholds", self.thresholds_edit.text().strip())
        set_setting("trend_cells", self.spin_trend.value())
        set_setting("html_report", self.chk_html.isChecked())
        set_setting("pdf_report", self.chk_pdf.isChecked())
        set_setting("strict", self.chk_strict.isChecked())
        set_setting("subscriber", self.chk_subscriber.isChecked())

    # ----- menu: Log / Impostazioni / Help ----------------------------------

    def open_log_viewer(self):
        LogViewerDialog(self).exec()

    def open_log_folder(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(LOG_DIR)))

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            if dlg.language_changed:
                self.set_language(get_setting("language"))
            self._load_settings()

    def set_language(self, code: str):
        """Cambia lingua a caldo e la persiste nelle impostazioni."""
        set_language(code)
        set_setting("language", code)
        self.retranslate()

    def show_help(self):
        HelpDialog(self).exec()

    def check_updates(self):
        self._menu_items["check_updates"].setEnabled(False)
        self.update_worker = UpdateWorker(self)
        self.update_worker.done.connect(self._on_update_result)
        self.update_worker.start()

    def _on_update_result(self, result: dict):
        self._menu_items["check_updates"].setEnabled(True)
        if result["error"]:
            QMessageBox.warning(
                self,
                tr("update_dialog_title"),
                tr("update_error", error=result["error"]),
            )
            return
        if result["update_available"]:
            box = QMessageBox(self)
            box.setWindowTitle(tr("update_dialog_title"))
            box.setText(
                tr(
                    "update_available",
                    latest=result["latest"],
                    current=result["current"],
                )
            )
            btn_open = box.addButton(tr("update_open_page"), QMessageBox.AcceptRole)
            box.addButton(QMessageBox.Close)
            box.exec()
            if box.clickedButton() is btn_open:
                QDesktopServices.openUrl(QUrl(result["url"]))
        else:
            QMessageBox.information(
                self,
                tr("update_dialog_title"),
                tr("update_uptodate", current=result["current"]),
            )

    def show_sponsor(self):
        SponsorDialog(self).exec()

    def show_about(self):
        AboutDialog(self).exec()

    def retranslate(self):
        """Riapplica tutte le stringhe tradotte dopo un cambio lingua."""
        self.setWindowTitle(app_title())
        self.lbl_input.setText(tr("input_file_label"))
        self.lbl_outdir.setText(tr("outdir_label"))
        self.lbl_thresholds.setText(tr("thresholds_label"))
        self.thresholds_edit.setPlaceholderText(tr("thresholds_placeholder"))
        for btn in (self.btn_in, self.btn_out, self.btn_th):
            btn.setText(tr("browse"))
        self.chk_html.setText(tr("opt_html"))
        self.chk_pdf.setText(tr("opt_pdf"))
        self.chk_strict.setText(tr("opt_strict"))
        self.chk_subscriber.setText(tr("opt_subscriber"))
        self.lbl_trend.setText(tr("trend_cells_label"))
        self.btn_run.setText(tr("run_analysis"))
        self.btn_close.setText(tr("close"))
        for i, key in enumerate(
            (
                "tab_summary",
                "tab_cells",
                "tab_sites",
                "tab_tech",
                "tab_subscriber",
                "tab_charts",
            )
        ):
            self.tabs.setTabText(i, tr(key))
        retranslate_menu(self._menu_items)

    # ----- azioni ----------------------------------------------------------

    def _pick_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("select_input_title"), "", tr("kpi_files_filter")
        )
        if path:
            self.input_edit.setText(path)

    def _pick_outdir(self):
        path = QFileDialog.getExistingDirectory(self, tr("select_outdir_title"))
        if path:
            self.outdir_edit.setText(path)

    def _pick_thresholds(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("select_thresholds_title"), "", tr("thresholds_filter")
        )
        if path:
            self.thresholds_edit.setText(path)

    def _run(self):
        input_path = self.input_edit.text().strip()
        if not input_path:
            QMessageBox.warning(self, app_title(), tr("msg_select_input"))
            return

        try:
            thresholds = (
                load_thresholds(self.thresholds_edit.text().strip())
                if self.thresholds_edit.text().strip()
                else None
            )
        except (OSError, ValueError) as e:
            QMessageBox.critical(
                self, app_title(), tr("msg_invalid_thresholds", error=e)
            )
            return

        self._save_settings()
        self.btn_run.setEnabled(False)
        self.progress.setRange(0, 0)  # indeterminato
        self.summary_text.setPlainText(tr("msg_analysis_running"))

        self.worker = AnalysisWorker(
            input_path,
            self.outdir_edit.text().strip() or "output",
            thresholds,
            self.spin_trend.value(),
            self.chk_html.isChecked(),
            self.chk_pdf.isChecked(),
            self.chk_strict.isChecked(),
            self.chk_subscriber.isChecked(),
            parent=self,
        )
        self.worker.finished_ok.connect(self._on_done)
        self.worker.failed.connect(self._on_error)
        self.worker.start()

    def _on_done(self, result: dict):
        self.btn_run.setEnabled(True)
        self.progress.setRange(0, 1)
        self.progress.setValue(1)

        cs = result["cell_summary"]
        counts = cs["severity"].value_counts()
        lines = [
            result["description"],
            "",
            f"Celle analizzate: {len(cs)}",
            f"  Critiche:   {counts.get('CRITICO', 0)}",
            f"  Attenzione: {counts.get('ATTENZIONE', 0)}",
            f"  OK:         {counts.get('OK', 0)}",
            "",
            "File prodotti:",
        ]
        for key in (
            "csv_cell",
            "csv_site",
            "csv_tech",
            "csv_subscriber",
            "xlsx",
            "html",
            "pdf",
        ):
            if result.get(key):
                lines.append(f"  {result[key]}")
        lines += [f"  {p}" for p in result["charts"]]
        self.summary_text.setPlainText("\n".join(lines))

        self._fill_table(self.table_cells, cs)
        self._fill_table(self.table_sites, result["site_summary"])
        self._fill_table(self.table_tech, result["tech_summary"])
        sub = result.get("subscriber_summary")
        self._fill_table(
            self.table_subscriber, sub if sub is not None else pd.DataFrame()
        )
        self._show_charts(result["charts"])

    def _on_error(self, message: str):
        self.btn_run.setEnabled(True)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.summary_text.setPlainText(tr("msg_error_prefix", error=message))
        QMessageBox.critical(self, app_title(), message)

    # ----- rendering risultati ----------------------------------------------

    def _fill_table(self, table: QTableWidget, df: pd.DataFrame):
        """Riempie una QTableWidget da un DataFrame, colorando la severità."""
        table.setRowCount(len(df))
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels([str(c) for c in df.columns])
        for i, (_, row) in enumerate(df.iterrows()):
            for j, col in enumerate(df.columns):
                v = row[col]
                text = f"{v:.2f}" if isinstance(v, float) else str(v)
                item = QTableWidgetItem(text)
                if col == "severity":
                    item.setBackground(QColor(SEVERITY_COLORS.get(v, "#999999")))
                    item.setForeground(QColor("white"))
                table.setItem(i, j, item)
        table.resizeColumnsToContents()

    def _show_charts(self, chart_paths: list[str]):
        """Mostra i PNG generati nell'area scorrevole dei grafici."""
        while self.charts_layout.count():
            item = self.charts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for path in chart_paths:
            if not os.path.exists(path):
                continue
            label = QLabel()
            pix = QPixmap(path)
            label.setPixmap(pix)
            label.setAlignment(Qt.AlignCenter)
            self.charts_layout.addWidget(label)


def main():
    app = QApplication(sys.argv)
    set_language(get_setting("language"))
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
