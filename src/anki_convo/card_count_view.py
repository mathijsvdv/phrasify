from aqt import mw
from aqt.qt import QAction
from aqt.utils import qconnect, showInfo


def show_card_count() -> None:
    card_count = mw.col.cardCount()
    showInfo(f"Card count: {card_count}")


def init_card_count_view():
    action = QAction("test", mw)
    qconnect(action.triggered, show_card_count)
    mw.form.menuTools.addAction(action)
