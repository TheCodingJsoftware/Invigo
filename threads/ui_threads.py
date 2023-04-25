from datetime import datetime
from functools import partial

from PyQt5.QtCore import QRunnable, Qt, QThread, QTimer

from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu

from ui.custom_widgets import (
    CostLineEdit,
    CurrentQuantitySpinBox,
    DeletePushButton,
    ExchangeRateComboBox,
    HumbleDoubleSpinBox,
    ItemNameComboBox,
    NotesPlainTextEdit,
    PartNumberComboBox,
    POPushButton,
    PriorityComboBox,
    set_status_button_stylesheet,
)
from utils.po import get_all_po


class InventoryItemLoader(QRunnable):
    def __init__(self, parent, category, category_data, table):
        super(InventoryItemLoader, self).__init__()
        self.parent = parent
        self.category = category
        self.tableWidget = table
        self.margins = (15, 15, 5, 5)  # top, bottom, left, right
        self.margin_format = f"margin-top: {self.margins[0]}%; margin-bottom: {self.margins[1]}%; margin-left: {self.margins[2]}%; margin-right: {self.margins[3]}%;"

        self._iter = iter(range(len(list(category_data.keys()))))
        self._timer = QTimer(interval=0, timeout=partial(self.load_item, category_data))
        self._timer.start()
        self.datetime1 = datetime.now()

    def run(self):
        """
        This is an empty function named "run" in a Python class.
        """
        pass

    def load_item(self, category_data) -> None:
        MINIMUM_WIDTH: int = 170
        try:
            row_index = next(self._iter)
            self.tableWidget.setEnabled(False)
            # QApplication.setOverrideCursor(Qt.BusyCursor)
        except StopIteration:
            datetime2 = datetime.now()
            difference = datetime2 - self.datetime1
            print(f"The time difference between the 2 time is: {difference}")
            self._timer.stop()
            set_status_button_stylesheet(
                button=self.parent.status_button, color="#3daee9"
            )
            self.parent.load_item_context_menu()
            self.tableWidget.resizeRowsToContents()
            self.tableWidget.resizeColumnsToContents()
            self.tableWidget.setEnabled(True)
            # QApplication.restoreOverrideCursor()
        except RuntimeError:
            self._timer.stop()
            return
        else:
            __start: float = (row_index + 1) / len(list(category_data.keys()))
            __middle: float = __start + 0.001 if __start <= 1 - 0.001 else 1.0
            __end: float = __start + 0.0011 if __start <= 1 - 0.0011 else 1.0
            self.parent.status_button.setStyleSheet(
                """QPushButton#status_button {background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,stop:%(start)s #3daee9,stop:%(middle)s #3daee9,stop:%(end)s #222222)}"""
                % {"start": str(__start), "middle": str(__middle), "end": str(__end)}
            )
            item = list(category_data.keys())[row_index]

            part_number: str = self.parent.get_value_from_category(
                item_name=item, key="part_number"
            )
            group = self.parent.get_value_from_category(item_name=item, key="group")
            try:
                current_quantity: int = int(
                    self.parent.get_value_from_category(
                        item_name=item, key="current_quantity"
                    )
                )
            except TypeError:
                self._timer.stop()
                return
            # Checking if the item is in the inventory.
            if (
                self.parent.get_value_from_category(
                    item_name=item, key="current_quantity"
                )
                is None
            ):
                return

            # self.item_layouts.append(layout)
            unit_quantity: float = float(
                self.parent.get_value_from_category(item_name=item, key="unit_quantity")
            )
            priority: int = self.parent.get_value_from_category(
                item_name=item, key="priority"
            )
            price: float = self.parent.get_value_from_category(
                item_name=item, key="price"
            )
            notes: str = self.parent.get_value_from_category(item_name=item, key="notes")
            use_exchange_rate: bool = self.parent.get_value_from_category(
                item_name=item, key="use_exchange_rate"
            )
            exchange_rate: float = (
                self.parent.get_exchange_rate() if use_exchange_rate else 1
            )
            total_cost_in_stock: float = current_quantity * price * exchange_rate
            if total_cost_in_stock < 0:
                total_cost_in_stock = 0
            total_unit_cost: float = unit_quantity * price * exchange_rate
            latest_change_part_number: str = self.parent.get_value_from_category(
                item_name=item, key="latest_change_part_number"
            )
            latest_change_unit_quantity: str = self.parent.get_value_from_category(
                item_name=item, key="latest_change_unit_quantity"
            )
            latest_change_current_quantity: str = self.parent.get_value_from_category(
                item_name=item, key="latest_change_current_quantity"
            )
            latest_change_price: str = self.parent.get_value_from_category(
                item_name=item, key="latest_change_price"
            )
            latest_change_use_exchange_rate: str = self.parent.get_value_from_category(
                item_name=item, key="latest_change_use_exchange_rate"
            )
            latest_change_priority: str = self.parent.get_value_from_category(
                item_name=item, key="latest_change_priority"
            )
            latest_change_notes: str = self.parent.get_value_from_category(
                item_name=item, key="latest_change_notes"
            )
            latest_change_name: str = self.parent.get_value_from_category(
                item_name=item, key="latest_change_name"
            )

            col_index: int = 0
            self.tableWidget.insertRow(row_index)
            self.tableWidget.setRowHeight(row_index, 60)

            # PART NAME
            item_name = ItemNameComboBox(
                parent=self.parent,
                selected_item=item,
                items=self.parent.get_all_part_names(),
                tool_tip=latest_change_name,
            )
            item_name.setContextMenuPolicy(Qt.CustomContextMenu)
            item_name.currentTextChanged.connect(
                partial(
                    self.parent.name_change,
                    self.category,
                    item_name.currentText(),
                    item_name,
                )
            )
            item_name.setStyleSheet(self.margin_format)
            # layout.addWidget(item_name)
            self.tableWidget.setCellWidget(row_index, col_index, item_name)
            col_index += 1

            # PART NUMBER
            line_edit_part_number = PartNumberComboBox(
                parent=self.parent,
                selected_item=part_number,
                items=self.parent.get_all_part_numbers(),
                tool_tip=latest_change_part_number,
            )
            line_edit_part_number.currentTextChanged.connect(
                partial(
                    self.parent.part_number_change,
                    self.category,
                    item_name,
                    "part_number",
                    line_edit_part_number,
                )
            )
            line_edit_part_number.setStyleSheet(self.margin_format)
            # layout.addWidget(line_edit_part_number)
            self.tableWidget.setCellWidget(row_index, col_index, line_edit_part_number)

            col_index += 1

            # UNIT QUANTITY
            spin_unit_quantity = HumbleDoubleSpinBox(self.parent)
            # spin_unit_quantity.setButtonSymbols(QAbstractSpinBox.NoButtons)
            spin_unit_quantity.setToolTip(latest_change_unit_quantity)
            spin_unit_quantity.setValue(unit_quantity)
            spin_unit_quantity.valueChanged.connect(
                partial(
                    self.parent.unit_quantity_change,
                    self.category,
                    item_name,
                    "unit_quantity",
                    spin_unit_quantity,
                )
            )
            spin_unit_quantity.setStyleSheet(self.margin_format)
            # layout.addWidget(spin_unit_quantity)
            self.tableWidget.setCellWidget(row_index, col_index, spin_unit_quantity)

            col_index += 1

            # ITEM QUANTITY
            spin_current_quantity = CurrentQuantitySpinBox(self.parent)
            spin_current_quantity.setToolTip(latest_change_current_quantity)
            spin_current_quantity.setValue(current_quantity)
            if current_quantity <= 10:
                quantity_color = "red"
            elif current_quantity <= 20:
                quantity_color = "yellow"

            if current_quantity > 20:
                spin_current_quantity.setStyleSheet(self.margin_format)
            else:
                spin_current_quantity.setStyleSheet(
                    f"color: {quantity_color}; border-color: {quantity_color}; {self.margin_format}"
                )
            spin_current_quantity.valueChanged.connect(
                partial(
                    self.parent.current_quantity_change,
                    self.category,
                    item_name,
                    "current_quantity",
                    spin_current_quantity,
                )
            )
            # layout.addWidget(spin_current_quantity)
            self.tableWidget.setCellWidget(row_index, col_index, spin_current_quantity)

            col_index += 1

            # PRICE
            round_number = lambda x, n: eval(
                '"%.'
                + str(int(n))
                + 'f" % '
                + repr(int(x) + round(float("." + str(float(x)).split(".")[1]), n))
            )
            converted_price: float = (
                price * self.parent.get_exchange_rate()
                if use_exchange_rate
                else price / self.parent.get_exchange_rate()
            )
            spin_price = HumbleDoubleSpinBox(self.parent)
            spin_price.setToolTip(
                "$"
                + str(round_number(converted_price, 2))
                + " CAD"
                + "\n"
                + latest_change_price
                if use_exchange_rate
                else "$"
                + str(round_number(converted_price, 2))
                + " USD"
                + "\n"
                + latest_change_price
            )
            spin_price.setValue(price)
            spin_price.setPrefix("$")
            spin_price.setSuffix(" USD" if use_exchange_rate else " CAD")
            spin_price.editingFinished.connect(
                partial(
                    self.parent.price_change,
                    self.category,
                    item_name,
                    "price",
                    spin_price,
                )
            )
            spin_price.setStyleSheet(self.margin_format)
            # layout.addWidget(spin_price)
            self.tableWidget.setCellWidget(row_index, col_index, spin_price)

            col_index += 1

            # EXCHANGE RATE
            combo_exchange_rate = ExchangeRateComboBox(
                parent=self.parent,
                selected_item="USD" if use_exchange_rate else "CAD",
                tool_tip=latest_change_use_exchange_rate,
            )
            combo_exchange_rate.currentIndexChanged.connect(
                partial(
                    self.parent.use_exchange_rate_change,
                    self.category,
                    item_name,
                    "use_exchange_rate",
                    combo_exchange_rate,
                )
            )
            combo_exchange_rate.setStyleSheet(self.margin_format)
            # layout.addWidget(combo_exchange_rate)
            self.tableWidget.setCellWidget(row_index, col_index, combo_exchange_rate)

            col_index += 1

            # TOTAL COST
            spin_total_cost = CostLineEdit(
                parent=self.parent,
                prefix="$",
                text=total_cost_in_stock,
                suffix=combo_exchange_rate.currentText(),
            )
            spin_total_cost.setStyleSheet(self.margin_format)
            # layout.addWidget(spin_total_cost)
            self.tableWidget.setCellWidget(row_index, col_index, spin_total_cost)

            col_index += 1

            # TOTALE UNIT COST
            spin_total_unit_cost = CostLineEdit(
                parent=self.parent,
                prefix="$",
                text=total_unit_cost,
                suffix=combo_exchange_rate.currentText(),
            )
            spin_total_unit_cost.setStyleSheet(self.margin_format)
            # layout.addWidget(spin_total_unit_cost)
            self.tableWidget.setCellWidget(row_index, col_index, spin_total_unit_cost)

            self.parent.inventory_prices_objects[item_name] = {
                "current_quantity": spin_current_quantity,
                "unit_quantity": spin_unit_quantity,
                "price": spin_price,
                "use_exchange_rate": combo_exchange_rate,
                "total_cost": spin_total_cost,
                "total_unit_cost": spin_total_unit_cost,
            }

            col_index += 1

            # PRIORITY
            combo_priority = PriorityComboBox(
                parent=self.parent,
                selected_item=priority,
                tool_tip=latest_change_priority,
            )
            if combo_priority.currentText() == "Medium":
                combo_priority.setStyleSheet("color: yellow; border-color: yellow;")
            elif combo_priority.currentText() == "High":
                combo_priority.setStyleSheet("color: red; border-color: red;")
            combo_priority.setStyleSheet(self.margin_format)
            combo_priority.currentIndexChanged.connect(
                partial(
                    self.parent.priority_change,
                    self.category,
                    item_name,
                    "priority",
                    combo_priority,
                )
            )
            # layout.addWidget(combo_priority)
            self.tableWidget.setCellWidget(row_index, col_index, combo_priority)

            col_index += 1

            # NOTES
            text_notes = NotesPlainTextEdit(
                parent=self.parent, text=notes, tool_tip=latest_change_notes
            )
            text_notes.textChanged.connect(
                partial(
                    self.parent.notes_changed,
                    self.category,
                    item_name,
                    "notes",
                    text_notes,
                )
            )
            text_notes.setStyleSheet(
                "margin-top: 1%; margin-bottom: 1%; margin-left: 1%; margin-right: 1%;"
            )
            # layout.addWidget(text_notes)
            self.tableWidget.setCellWidget(row_index, col_index, text_notes)

            col_index += 1

            # PURCHASE ORDER
            po_menu = QMenu(self.parent)
            for po in get_all_po():
                po_menu.addAction(po, partial(self.parent.open_po, po))
            btn_po = POPushButton(parent=self.parent)
            btn_po.setMenu(po_menu)
            btn_po.setStyleSheet(self.margin_format)
            # layout.addWidget(btn_po)
            self.tableWidget.setCellWidget(row_index, col_index, btn_po)
            self.parent.po_buttons.append(btn_po)

            col_index += 1

            # DELETE
            btn_delete = DeletePushButton(
                parent=self.parent,
                tool_tip=f"Delete {item_name.currentText()} permanently from {self.category}",
                icon=QIcon(
                    f"ui/BreezeStyleSheets/dist/pyqt6/{self.parent.theme}/trash.png"
                ),
            )
            btn_delete.clicked.connect(
                partial(self.parent.delete_item, self.category, item_name)
            )
            btn_delete.setStyleSheet(self.margin_format)
            # layout.addWidget(btn_delete)
            self.tableWidget.setCellWidget(row_index, col_index, btn_delete)


class ProcessItemSelectedThread(QThread):
    """This class is a QThread that emits a signal when it's done processing a list of items"""

    def __init__(self, QObjects: dict, highlight_color: str, selected_item) -> None:
        """
        A constructor for the class.

        Args:
          QObjects (dict): dict = {'QObject1': QObject1, 'QObject2': QObject2, 'QObject3': QObject3}
          highlight_color (str): str = The color to highlight the selected item with.
          selected_item: The item that was selected in the list
        """
        QThread.__init__(self)
        self.QObjects: dict = QObjects
        self.highlight_color: str = highlight_color
        self.selected_item = selected_item
        self.theme: str = (
            "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        )

    def run(self) -> None:
        """
        It's a function that changes the background color of a QComboBox widget and a QSpinBox widget
        when the QComboBox widget is clicked
        """
        for item in list(self.QObjects.keys()):
            spin_current_quantity = self.QObjects[item]["current_quantity"]
            if item.currentText() == self.selected_item:
                if self.highlight_color == "#3daee9":
                    item.setStyleSheet(
                        f"background-color: {self.highlight_color}; border: 1px solid {self.highlight_color};"
                    )
                    if spin_current_quantity.value() <= 0:
                        spin_current_quantity.setStyleSheet(
                            "background-color: #1d2023; color: red"
                        )
                    else:
                        spin_current_quantity.setStyleSheet(
                            "background-color: #1d2023; color: white"
                        )
                else:
                    if spin_current_quantity.value() <= 0:
                        spin_current_quantity.setStyleSheet(
                            f"background-color: {self.highlight_color}; border: 1px solid {self.highlight_color}; color: red"
                        )
                    else:
                        spin_current_quantity.setStyleSheet(
                            f"background-color: {self.highlight_color}; border: 1px solid {self.highlight_color}; color: white"
                        )
                    self.highlight_color = "#3daee9"
            elif self.theme == "dark":
                if self.highlight_color == "#3daee9":
                    item.setStyleSheet("background-color: #1d2023")
                if spin_current_quantity.value() <= 0:
                    spin_current_quantity.setStyleSheet(
                        "background-color: #1d2023; color: red"
                    )

                else:
                    spin_current_quantity.setStyleSheet(
                        "background-color: #1d2023; color: white"
                    )

            else:
                if self.highlight_color == "#3daee9":
                    item.setStyleSheet("background-color: #eff0f1")
                if spin_current_quantity.value() <= 0:
                    spin_current_quantity.setStyleSheet(
                        "background-color: #eff0f1; color: red"
                    )
                else:
                    spin_current_quantity.setStyleSheet(
                        "background-color: #eff0f1; color: white"
                    )


class SetStyleSheetThread(QThread):
    """This class is a QThread that sets the stylesheet of a QWidget"""

    def __init__(self, QObject: object, stylesheet: str) -> None:
        """
        A constructor for the class.

        Args:
          QObject (object): The object you want to apply the stylesheet to.
          stylesheet (str): The stylesheet you want to apply to the QObject
        """
        QThread.__init__(self)
        self.QObject: object = object
        self.stylesheet: str = stylesheet

    def run(self) -> None:
        """
        It sets the stylesheet of the QObject to the stylesheet that was passed in
        """
        self.QObject.setStyleSheet(self.stylesheet)
