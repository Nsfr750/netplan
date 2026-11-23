"""
menu.py
Costruzione della barra dei menu della GUI: voci separate per
Log, Impostazioni e Help.
"""

from PySide6.QtGui import QAction, QActionGroup

from lang.language_manager import LanguageManager, tr


def build_menu_bar(window) -> dict:
    """Crea i menu Log / Impostazioni / Help sulla finestra principale.

    Collega ogni voce ai metodi omonimi di `window` e restituisce un
    dizionario {nome: QAction|QMenu} usato da retranslate() per
    aggiornare i testi quando cambia la lingua.
    """
    bar = window.menuBar()
    items = {}

    # --- Log ---
    menu_log = bar.addMenu(tr("menu_log"))
    items["menu_log"] = menu_log

    act_log = QAction(tr("view_log_action"), window)
    act_log.triggered.connect(window.open_log_viewer)
    menu_log.addAction(act_log)
    items["view_log"] = act_log

    act_logdir = QAction(tr("open_log_folder"), window)
    act_logdir.triggered.connect(window.open_log_folder)
    menu_log.addAction(act_logdir)
    items["open_log_folder"] = act_logdir

    # --- Impostazioni ---
    menu_set = bar.addMenu(tr("menu_settings"))
    items["menu_settings"] = menu_set

    act_pref = QAction(tr("preferences_action"), window)
    act_pref.triggered.connect(window.open_settings)
    menu_set.addAction(act_pref)
    items["preferences"] = act_pref

    menu_lang = menu_set.addMenu(tr("language_menu"))
    items["language_menu"] = menu_lang
    group = QActionGroup(window)
    group.setExclusive(True)
    current = LanguageManager.instance().language
    for code, name in LanguageManager.instance().available_languages().items():
        act = QAction(name, window, checkable=True)
        act.setChecked(code == current)
        act.setData(code)
        act.triggered.connect(lambda checked, c=code: window.set_language(c))
        group.addAction(act)
        menu_lang.addAction(act)

    # --- Help ---
    menu_help = bar.addMenu(tr("menu_help"))
    items["menu_help"] = menu_help

    entries = [
        ("help", tr("help_action"), window.show_help),
        ("check_updates", tr("check_updates_action"), window.check_updates),
        ("sponsor", tr("sponsor_action"), window.show_sponsor),
        ("about", tr("about_action"), window.show_about),
    ]
    for key, text, slot in entries:
        act = QAction(text, window)
        act.triggered.connect(slot)
        menu_help.addAction(act)
        items[key] = act

    return items


def retranslate_menu(items: dict):
    """Riapplica i testi tradotti a menu e azioni (cambio lingua a caldo)."""
    items["menu_log"].setTitle(tr("menu_log"))
    items["view_log"].setText(tr("view_log_action"))
    items["open_log_folder"].setText(tr("open_log_folder"))
    items["menu_settings"].setTitle(tr("menu_settings"))
    items["preferences"].setText(tr("preferences_action"))
    items["language_menu"].setTitle(tr("language_menu"))
    items["menu_help"].setTitle(tr("menu_help"))
    items["help"].setText(tr("help_action"))
    items["check_updates"].setText(tr("check_updates_action"))
    items["sponsor"].setText(tr("sponsor_action"))
    items["about"].setText(tr("about_action"))
