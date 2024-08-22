import contextlib
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import QInputDialog, QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget

from ui.widgets.quote_widget import QuoteWidget
from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.sheets_inventory import SheetsInventory
from utils.quote.quote import Quote
from utils.sheet_settings.sheet_settings import SheetSettings

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow


class PopoutWidget(QWidget):
    def __init__(self, layout_to_popout: QVBoxLayout, parent=None):
        super().__init__(parent)

        self.parent: MainWindow = parent
        self.original_layout = layout_to_popout
        self.original_layout_parent: "QuoteGeneratorTab" = self.original_layout.parentWidget()
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("Quote Generator")
        self.setLayout(self.original_layout)
        self.setObjectName("popout_widget")

    def closeEvent(self, event):
        if self.original_layout_parent:
            self.original_layout_parent.setLayout(self.original_layout)
            self.original_layout_parent.pushButton_popout.setIcon(QIcon("icons/open_in_new.png"))
            self.original_layout_parent.pushButton_popout.clicked.disconnect()
            self.original_layout_parent.pushButton_popout.clicked.connect(self.original_layout_parent.popout)
        super().closeEvent(event)


class QuoteGeneratorTab(QWidget):
    save_quote = pyqtSignal(Quote)
    save_quote_as = pyqtSignal(Quote)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent: MainWindow = parent
        self.components_inventory: ComponentsInventory = self.parent.components_inventory
        self.laser_cut_inventory: LaserCutInventory = self.parent.laser_cut_inventory
        self.sheets_inventory: SheetsInventory = self.parent.sheets_inventory
        self.sheet_settings: SheetSettings = self.parent.sheet_settings

        self.quotes: list[QuoteWidget] = []
        self.current_quote: Quote = None

        self.tab_layout = QVBoxLayout(self)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_layout.setSpacing(6)
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setObjectName("quote_generator_tab_widget")
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.tabBarDoubleClicked.connect(self.rename_tab)
        self.tab_widget.currentChanged.connect(self.tab_changed)
        self.tab_widget.setStyleSheet("QTabWidget#quote_generator_tab_widget > QWidget { border-bottom-left-radius: 0px; }")
        self.pushbutton_new_quote = QPushButton("Add New Quote Tab", self)
        self.pushbutton_new_quote.setStyleSheet("border-radius: 0px; padding: 2px;")
        self.pushbutton_new_quote.clicked.connect(self.add_tab)
        self.tab_widget.setCornerWidget(self.pushbutton_new_quote, Qt.Corner.TopRightCorner)
        self.tab_layout.addWidget(self.tab_widget)

        self.setLayout(self.tab_layout)

        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_current_quote)

        self.shortcut_save_as = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.shortcut_save_as.activated.connect(self.save_current_quote_as)

    def get_quote_by_name(self, quote_name: str) -> Quote:
        for quote in self.quotes:
            if quote_name == quote.name:
                return quote

    def set_quote(self, tab_index: int, new_quote: Quote):
        new_quote.unsaved_changes = True
        new_quote_widget = QuoteWidget(
            new_quote,
            self.components_inventory,
            self.laser_cut_inventory,
            self.sheets_inventory,
            self.sheet_settings,
            self,
        )
        new_quote_widget.quote_unsaved_changes.connect(self.quote_changed)
        old_quote = self.quotes[tab_index].quote
        self.quotes.pop(tab_index)
        self.tab_widget.removeTab(tab_index)
        self.quotes.insert(tab_index, new_quote_widget)
        self.tab_widget.insertTab(tab_index, new_quote_widget, old_quote.name)
        new_quote_widget.load_quote()
        self.tab_widget.setCurrentIndex(tab_index)
        self.update_quote_save_status(new_quote)

    def add_quote(self, quote: Quote):
        quote_widget = QuoteWidget(
            quote,
            self.components_inventory,
            self.laser_cut_inventory,
            self.sheets_inventory,
            self.sheet_settings,
            self,
        )
        quote_widget.quote_unsaved_changes.connect(self.quote_changed)
        self.quotes.append(quote_widget)
        self.tab_widget.addTab(quote_widget, quote.name)

    def add_tab(self, new_quote: Quote = None):
        if not new_quote:
            new_quote = Quote(
                f"Quote{self.tab_widget.count()}",
                None,
                self.components_inventory,
                self.laser_cut_inventory,
                self.sheet_settings,
            )
            new_quote.order_number = self.parent.order_number
        self.add_quote(new_quote)
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
        if self.tab_widget.count() > 1:
            self.tab_widget.setTabsClosable(True)
        else:
            self.tab_widget.setTabsClosable(False)

    def tab_changed(self):
        for quote_widget in self.quotes:
            if self.tab_widget.currentWidget() == quote_widget:
                self.current_quote = quote_widget.quote
                self.update_quote_save_status(quote_widget.quote)
                break

    def close_tab(self, tab_index: int):
        if self.tab_widget.count() == 1:
            return
        quote_to_delete = self.quotes[tab_index]
        if quote_to_delete.quote.unsaved_changes and quote_to_delete.quote.downloaded_from_server:
            msg = QMessageBox(
                QMessageBox.Icon.Question,
                "Unsaved changes",
                f"You are about to remove this quote from your view. This action will not delete the quote from the server. It will only be removed from your current session.\n\nAre you sure you want to delete {quote_to_delete.quote.name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                self,
            )
            response = msg.exec()
            if response in [
                QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Cancel,
            ]:
                return
        self.tab_widget.removeTab(tab_index)
        self.quotes.remove(quote_to_delete)
        self.clear_layout(quote_to_delete)
        if self.tab_widget.count() == 1:
            self.tab_widget.setTabsClosable(False)

    def rename_tab(self, tab_index: int):
        new_name, ok = QInputDialog.getText(self, "Rename Quote", "Enter new quote name:", text=self.current_quote.name)
        if ok and new_name:
            self.current_quote.name = new_name
            self.tab_widget.setTabText(tab_index, new_name)
            self.current_quote.changes_made()
            self.update_quote_save_status(self.current_quote)

    def save_current_quote(self):
        self.save_quote.emit(self.current_quote)
        self.update_quote_save_status(self.current_quote)

    def save_current_quote_as(self):
        self.save_quote_as.emit(self.current_quote)
        self.update_quote_save_status(self.current_quote)

    def quote_changed(self, quote: Quote):
        self.update_quote_save_status(quote)

    def update_quote_save_status(self, quote: Quote):
        if quote.unsaved_changes:
            self.parent.label_quote_save_status.setText("You have unsaved changes")
        else:
            self.parent.label_quote_save_status.setText("")

    def popout(self):
        self.popout_widget = PopoutWidget(self.layout(), self.parent)
        self.popout_widget.show()
        self.pushButton_popout.setIcon(QIcon("icons/dock_window.png"))
        self.pushButton_popout.clicked.disconnect()
        self.pushButton_popout.clicked.connect(self.popout_widget.close)

    def sync_changes(self):
        self.parent.sync_changes("quote_generator_tab")

    def clear_layout(self, layout: QVBoxLayout | QWidget):
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())
