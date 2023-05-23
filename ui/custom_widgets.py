import os

from PyQt5.QtCore import (
    QMargins,
    QMimeData,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    pyqtSignal,
    QEvent,
)
from PyQt5.QtGui import QDrag, QIcon, QPalette, QPixmap, QCursor
from PyQt5.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileSystemModel,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionComboBox,
    QStylePainter,
    QTableWidget,
    QTabWidget,
    QTreeView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QTabBar,
    QToolBox,
)


class MultiToolBox(QWidget):
    '''The class MultiToolBox is a QWidget.'''
    def __init__(self, parent=None):
        super(MultiToolBox, self).__init__(parent)
        self.widgets = []
        self.buttons = []
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        self.setLayout(main_layout)

    def addItem(self, widget: QWidget, title: str):
        """
        This function adds a widget with a title and a toggle button to a layout.
        
        Args:
          widget (QWidget): QWidget - This is the widget that will be added to the sheet. It can be any
        type of QWidget, such as a QLabel, QComboBox, or even another layout.
          title (str): A string representing the title of the widget that will be added to the layout.
        """
        button = QPushButton()
        button.setObjectName("sheet_nest_button")
        button.setText(title)
        button.setChecked(True)
        button.setCheckable(True)
        button.clicked.connect(lambda checked, w=widget: self.toggle_widget_visibility(w))

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 3, 0, 0) 
        layout.addWidget(button)
        layout.addWidget(widget)

        self.buttons.append(button)
        self.widgets.append(widget)

        self.layout().addLayout(layout)

    def setItemText(self, index: int, new_name: str):
        """
        This function sets the text of a button at a given index to a new name.
        
        Args:
          index (int): an integer representing the index of the button whose text needs to be changed.
          new_name (str): A string representing the new text that will be set for the button at the
        specified index.
        """
        if 0 <= index < len(self.buttons):
            self.buttons[index].setText(new_name)
            
    def setItemIcon(self, index: int, icon_path: str):
        """
        This function sets the icon of a button at a given index with the icon located at a specified
        file path.
        
        Args:
          index (int): An integer representing the index of the button in the list of buttons.
          icon_path (str): The path to the icon file that will be used as the button's icon.
        """
        if 0 <= index < len(self.buttons):
            button = self.buttons[index]
            icon = QIcon(icon_path)
            button.setIcon(icon)
    
    def getWidget(self, index):
        """
        This function returns the widget at the specified index if it exists, otherwise it returns None.
        
        Args:
          index: The index parameter is an integer value that represents the position of the widget in
        the list of widgets. It is used to retrieve a specific widget from the list of widgets.
        
        Returns:
          The method `getWidget` returns either the widget at the specified index in the `self.widgets`
        list, or `None` if the index is out of range.
        """
        if 0 <= index < len(self.widgets):
            return self.widgets[index]
        return None
    
    def count(self) -> int:
        """
        The function returns the number of widgets in a class.
        
        Returns:
          The function `count()` is returning an integer value which represents the length of the
        `widgets` list.
        """
        return len(self.widgets)

    def toggle_widget_visibility(self, widget):
        """
        This function toggles the visibility of a widget in a Python GUI.
        
        Args:
          widget: The widget parameter is a reference to a graphical user interface (GUI) widget object.
        The function toggles the visibility of this widget, i.e., if the widget is currently visible, it
        will be hidden, and if it is currently hidden, it will be made visible. The widget object could
        be
        """
        widget.setVisible(not widget.isVisible())
    
    
class CustomTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super(CustomTabWidget, self).__init__(parent)
        self.tab_order = []  # Stores the current order of tabs as strings
        self.tabBar().installEventFilter(self)
        self.wheelEvent = lambda event: None
        
    def dragMoveEvent(self, event):
        # Check if it's a tab being dragged
        if event.source() == self.tabBar():
            event.ignore()  # Ignore the drag move event
        else:
            super().dragMoveEvent(event)

    def wheelEvent(self, event):
        """
        This function ignores the wheel event.

        Args:
          event: The event parameter in this code refers to a QWheelEvent object, which is an event that
        occurs when the user rotates the mouse wheel. This function is a method of a class that inherits
        from QWidget, and it is used to handle the wheel event when it occurs on the widget.
        """
        event.ignore()
    
    def update_tab_order(self):
        """
        This function updates the tab order of a widget by creating a list of tab texts in the order
        they appear.
        """
        self.tab_order = [self.tabText(i) for i in range(self.count())]

    def get_tab_order(self) -> list[str]:
        """
        This function returns a list of strings representing the tab order of a QTabWidget.
        
        Returns:
          A list of strings representing the tab order.
        """
        self.update_tab_order()
        return self.tab_order

    def set_tab_order(self, order):
        """
        This function sets the tab order of a tab bar based on a given list of tab names.
        
        Args:
          order: A list of tab names in the desired order. The function will reorder the tabs in the tab
        bar based on this order.
        """
        for tab_name in order:
            index = self.find_tab_by_name(tab_name)
            if index != -1:
                self.tabBar().moveTab(index, order.index(tab_name))

    def find_tab_by_name(self, name: str) -> int:
        """
        This function finds the index of a tab in a tab widget by its name.
        
        Args:
          name (str): A string representing the name of the tab that needs to be found.
        
        Returns:
          an integer value which represents the index of the tab with the given name in the tab widget.
        If the tab is not found, it returns -1.
        """
        for i in range(self.count()):
            if self.tabText(i) == name:
                return i
        return -1

class PdfFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sort_order = Qt.DescendingOrder

    def filterAcceptsRow(self, row, parent):
        """
        This function filters rows based on whether they contain a file with a .pdf extension.

        Args:
          row: The row number of the item being filtered in the view.
          parent: The parent index of the current index being filtered. It represents the parent item in
        the model hierarchy.

        Returns:
          a boolean value indicating whether the row should be included in the filtered view or not.
        """
        index = self.sourceModel().index(row, 0, parent)
        if not index.isValid():
            return False
        if self.sourceModel().isDir(index):
            return any(
                file.lower().endswith('.pdf')
                for file in os.listdir(self.sourceModel().filePath(index))
            )
        filename = self.sourceModel().fileName(index)
        return filename.lower().endswith('.pdf')

    def lessThan(self, left_index, right_index):
        """
        This function overrides the lessThan method to sort a specific column in a QAbstractTableModel
        based on the sort order.

        Args:
          left_index: The QModelIndex object representing the left item being compared in the sorting
        operation.
          right_index: The index of the item on the right side of the comparison being made in the
        model. In other words, it is the index of the item that is being compared to the item at the
        left_index.

        Returns:
          The method `lessThan` is returning a boolean value indicating whether the data at the
        `left_index` is less than the data at the `right_index`. If the columns of the indices are not
        2, it calls the `lessThan` method of the parent class. If the sort order is descending, it
        returns `left_data > right_data`, otherwise it returns `left_data < right
        """
        if left_index.column() != 2 or right_index.column() != 2:
            return super().lessThan(left_index, right_index)
        left_data = self.sourceModel().data(left_index, Qt.UserRole)
        right_data = self.sourceModel().data(right_index, Qt.UserRole)
        return left_data > right_data if self.sort_order == Qt.DescendingOrder else left_data < right_data

    def sort(self, column, order):
        """
        This function sorts a table by a specified column and order, and updates the sort order
        attribute if the column is the second column.

        Args:
          column: The column number that the data should be sorted by.
          order: The order parameter specifies the sorting order, which can be either Qt.AscendingOrder
        or Qt.DescendingOrder. Qt.AscendingOrder sorts the items in ascending order, while
        Qt.DescendingOrder sorts the items in descending order.
        """
        if column == 2:
            self.sort_order = order
        super().sort(column, order)


class PdfTreeView(QTreeView):
    def __init__(self, path: str):
        super().__init__()
        self.model = QFileSystemModel()
        self.model.setRootPath('')
        self.setModel(self.model)
        self.filterModel = PdfFilterProxyModel()
        self.filterModel.setSourceModel(self.model)
        self.setModel(self.filterModel)
        self.filterModel.setFilterRegExp('')
        self.filterModel.setFilterKeyColumn(0)
        self.setRootIndex(
            self.filterModel.mapFromSource(self.model.index(path)))
        self.header().resizeSection(0, 170)
        self.setSelectionMode(4)
        self.header().hideSection(1)
        self.header().hideSection(2)
        self.expandAll()
        self.selected_indexes = []
        self.selected_items = []

        self.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def on_selection_changed(self, selected, deselected):
        self.selected_indexes = self.selectionModel().selectedIndexes()
        self.selected_items = [
            index.data() for index in self.selected_indexes if '.pdf' in index.data()
        ]


class RecutButton(QPushButton):
    def __init__(self, parent=None):
        """
        This function initializes a checkable and clickable button with the text "No Recut" and a fixed
        width of 100.
        
        Args:
          parent: The parent parameter is used to specify the parent widget of the current widget. If a
        parent widget is specified, the current widget becomes a child of the parent widget and is
        displayed within it. If no parent widget is specified, the current widget becomes a top-level
        widget and is displayed independently. In this
        """
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(False)
        self.setObjectName("recut_button")
        self.setFixedWidth(100)
        self.setFlat(True)
        self.setText("No Recut")
        self.clicked.connect(self.toggle_state)

    def toggle_state(self):
        """
        This function toggles the text of a button between "Recut" and "No Recut" based on its current
        state.
        """
        if self.isChecked():
            self.setText("Recut")
        else:
            self.setText("No Recut")


class CustomTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.editable_column_indexes = []

    def edit(self, index, trigger, event):
        """
        This function checks if a column is editable and allows editing if it is, otherwise it returns
        False.

        Args:
          index: The index of the item in the model that is being edited.
          trigger: The trigger parameter is an event that causes the editor to be opened for editing the
        cell. It can be one of the following values:
          event: The event parameter in the edit() method is an instance of QEvent class. It represents
        an event that occurred on the widget. The event parameter is used to determine the type of event
        that occurred, such as a mouse click or a key press, and to handle the event accordingly.

        Returns:
          If the column index of the given index is in the list of editable_column_indexes, then the
        super().edit() method is called and its return value is returned. Otherwise, False is returned.
        """
        if index.column() in self.editable_column_indexes:
            return super().edit(index, trigger, event)
        else:
            return False

    def set_editable_column_index(self, columns: list[int]):
        """
        This function sets the indexes of columns that are editable in a table.

        Args:
          columns (list[int]): A list of integers representing the indexes of the columns that should be
        editable in a table or spreadsheet.
        """
        self.editable_column_indexes = columns


class OrderStatusButton(QPushButton):
    def __init__(self, parent=None):
        """
        This function initializes a QPushButton with specific properties and sets its object name to
        "order_status".

        Args:
          parent: The parent widget of the QPushButton. If no parent is specified, the button will be a
        top-level window.
        """
        super(QPushButton, self).__init__(parent)
        self.setCheckable(True)
        self.setText("Order Pending")
        self.setFixedWidth(100)
        self.setObjectName("order_status")


class ItemCheckBox(QCheckBox):
    """This is a custom class that inherits from the QCheckBox class in PyQt and adds additional functionality for handling items."""

    def mousePressEvent(self, event):
        """
        This function checks if the pressed key is the Shift key and if so, calls the parent class's
        keyPressEvent method, otherwise it does nothing.

        :param event: The event parameter in this code refers to a key press event that is triggered
        when a key on the keyboard is pressed. It contains information about the key that was pressed,
        such as the key code and whether any modifier keys (such as Shift or Ctrl) were also pressed.
        The code checks if the
        """
        if event.button() == Qt.LeftButton:
            super().mousePressEvent(event)


class ItemNameComboBox(QComboBox):
    """This class is a QComboBox that is populated with the names of items in the database"""

    def __init__(self, parent, selected_item: str, items: list[str], tool_tip: str):
        """
        It's a function that creates a dropdown menu with a list of items, and the selected item is the
        one that is displayed when the dropdown menu is first created

        Args:
          parent: The parent widget
          selected_item (str): The item that is selected by default
          items (list[str]): list[str] = ['item1', 'item2', 'item3']
          tool_tip (str): str = "This is the tool tip"
        """
        QComboBox.__init__(self, parent)
        self.addItems(items)
        self.setCurrentText(selected_item)
        self.setToolTip(tool_tip)
        self.setEditable(True)
        self.wheelEvent = lambda event: None
        # self.setMinimumWidth(170)
        self.setMaximumWidth(350)


class PartNumberComboBox(QComboBox):
    """This class is a QComboBox that is populated with the names of part numbers in the database"""

    def __init__(self, parent, selected_item: str, items: list[str], tool_tip: str):
        """
        It's a function that creates a dropdown menu with a list of items, and the selected item is the
        one that is displayed when the dropdown menu is first created

        Args:
          parent: The parent widget
          selected_item (str): The item that is selected by default
          items (list[str]): list[str] = ['item1', 'item2', 'item3']
          tool_tip (str): str = "This is the tool tip"
        """
        QComboBox.__init__(self, parent)
        self.addItems(items)
        self.setCurrentText(selected_item)
        self.setToolTip(tool_tip)
        self.setEditable(True)
        self.wheelEvent = lambda event: None
        self.setFixedWidth(120)


class PriorityComboBox(QComboBox):
    """This class is a QComboBox that is populated with the names of items in the database"""

    def __init__(self, parent, selected_item: int, tool_tip: str):
        """
        It's a function that creates a dropdown menu with a list of items, and the selected item is the
        one that is displayed when the dropdown menu is first created

        Args:
          parent: The parent widget
          selected_item (str): The item that is selected by default
          tool_tip (str): str = "This is the tool tip"
        """
        QComboBox.__init__(self, parent)
        self.addItems(["Default", "Low", "Medium", "High"])
        self.setCurrentIndex(selected_item)
        self.setToolTip(tool_tip)
        self.wheelEvent = lambda event: None
        # #self.setFixedWidth(60)


class ExchangeRateComboBox(QComboBox):
    """This class is a QComboBox that is populated with the names of items in the database"""

    def __init__(self, parent, selected_item: int, tool_tip: str):
        """
        The function takes in a parent, a selected item, and a tool tip. It then creates a QComboBox
        object, adds items to the combo box, sets the current text to the selected item, sets the tool
        tip to the tool tip, sets the wheel event to a lambda function that does nothing, and sets the
        fixed width to 40.

        Args:
          parent: The parent widget
          selected_item (int): The item that is selected when the combobox is created.
          tool_tip (str): The text that will be displayed when the user hovers over the combobox.
        """
        QComboBox.__init__(self, parent)
        self.addItems(["CAD", "USD"])
        self.setCurrentText(selected_item)
        self.setToolTip(tool_tip)
        self.wheelEvent = lambda event: None
        # #self.setFixedWidth(40)


class CostLineEdit(QLineEdit):
    """This class is a subclass of QLineEdit that has a custom validator that only allows numbers and a
    decimal point"""

    def __init__(self, parent, prefix: str, text: str, suffix: str):
        """
        It takes a number, rounds it to the nearest 2 decimal places, and returns a string with the
        number rounded to 2 decimal places

        Args:
          parent: The parent widget
          prefix (str): The prefix of the text.
          text (str): The text to be displayed in the QLineEdit
          suffix (str): The suffix of the text.
        """
        QLineEdit.__init__(self, parent)
        # self.setFixedWidth(100)
        self.setReadOnly(True)

        def round_number(x, n): return eval(
            '"%.'
            + str(int(n))
            + 'f" % '
            + repr(int(x) + round(float("." + str(float(x)).split(".")[1]), n))
        )
        self.setStyleSheet(
            "border: 0.09em solid rgb(57, 57, 57); background-color: #222222;")
        try:
            self.setText(f"{prefix}{str(round_number(text, 2))} {suffix}")
        except Exception:
            self.setText(f"{prefix}{text} {suffix}")


class NotesPlainTextEdit(QPlainTextEdit):
    """It's a QPlainTextEdit that has a context menu with a "Copy" and "Paste" option"""

    def __init__(self, parent, text: str, tool_tip: str):
        """
        This function creates a QPlainTextEdit object with a minimum width of 100, a maximum width of
        200, a fixed height of 60, a plain text of text, and a tool tip of tool_tip

        Args:
          parent: The parent widget.
          text (str): The text that will be displayed in the text box.
          tool_tip (str): The text that will be displayed when the mouse hovers over the widget.
        """
        QPlainTextEdit.__init__(self, parent)
        self.setMinimumWidth(100)
        self.setMaximumWidth(200)
        self.setFixedHeight(60)
        self.setPlainText(text)
        self.setToolTip(tool_tip)


class POPushButton(QPushButton):
    """This class is a subclass of QPushButton that has a signal that emits the button's text when
    the button is clicked"""

    def __init__(self, parent):
        """
        The function is called when the button is clicked

        Args:
          parent: The parent widget.
        """
        QPushButton.__init__(self, parent)
        # self.setFixedSize(36, 26)
        self.setText("PO")
        self.setToolTip("Open a new purchase order")


class DeletePushButton(QPushButton):
    """It creates a class called DeletePushButton that inherits from QPushButton."""

    def __init__(self, parent, tool_tip: str, icon: QIcon):
        """
        It creates a button with a trash icon

        Args:
          parent: The parent widget.
        """
        QPushButton.__init__(self, parent)
        # self.setFixedSize(26, 26)
        self.setObjectName("delete_button")
        self.setIcon(icon)
        self.setToolTip(tool_tip)


class ClickableLabel(QLabel):
    clicked = pyqtSignal()  # Signal emitted when the label is clicked
    def __init__(self, parent=None):
        super(ClickableLabel, self).__init__(parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        self.clicked.emit()  # Emit the clicked signal


class RichTextPushButton(QPushButton):
    """It's a QPushButton that can display rich text"""

    def __init__(self, parent=None, text=None):
        if parent is not None:
            super().__init__(parent)
        else:
            super().__init__()
        self.__lbl = QLabel(self)
        if text is not None:
            self.__lbl.setText(text)
        self.__layout = QHBoxLayout()
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSpacing(0)
        self.setLayout(self.__layout)
        self.__lbl.setAttribute(Qt.WA_TranslucentBackground)  # type: ignore
        self.__lbl.setAlignment(
            Qt.AlignCenter | Qt.AlignVCenter)  # type: ignore
        self.__lbl.setAttribute(
            Qt.WA_TransparentForMouseEvents)  # type: ignore
        self.__lbl.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )
        self.__lbl.setTextFormat(Qt.RichText)  # type: ignore
        self.__layout.addWidget(self.__lbl)
        return

    def setText(self, text) -> None:
        """
        > Sets the text of the widget to the given text

        Args:
          text: The text to be displayed in the label.
        """
        self.__lbl.setText(text)
        self.updateGeometry()
        return

    def sizeHint(self) -> QSizePolicy:
        """
        The function returns a QSizePolicy object that is the size of the QLabel object

        Returns:
          The size of the button.
        """
        button_size = QPushButton.sizeHint(self)
        label_size = self.__lbl.sizeHint()
        button_size.setWidth(label_size.width())
        button_size.setHeight(label_size.height())
        return button_size


class HumbleDoubleSpinBox(QDoubleSpinBox):
    """It's a spin box that doesn't let you enter a value that's too close to zero."""

    def __init__(self, *args):
        """
        The function sets the focus policy of the spinbox to strong focus
        """
        super(HumbleDoubleSpinBox, self).__init__(*args)
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setFixedWidth(100)
        self.setMaximum(99999999)
        self.setMinimum(-99999999)
        self.setAccelerated(True)

    def focusInEvent(self, event):
        """
        When the user clicks on the spinbox, the focus policy is changed to allow the mouse wheel to be
        used to change the value

        Args:
          event: QFocusEvent
        """
        self.setFocusPolicy(Qt.WheelFocus)
        super(HumbleDoubleSpinBox, self).focusInEvent(event)

    def focusOutEvent(self, event):
        """
        When the user clicks on the spinbox, the focus policy is changed to StrongFocus, and then the
        focusOutEvent is called

        Args:
          event: QFocusEvent
        """
        self.setFocusPolicy(Qt.StrongFocus)
        super(HumbleDoubleSpinBox, self).focusOutEvent(event)

    def wheelEvent(self, event):
        """
        If the spinbox has focus, then it will behave as normal. If it doesn't have focus, then the
        wheel event will be ignored

        Args:
          event: The event object

        Returns:
          The super class of the HumbleSpinBox class.
        """
        if self.hasFocus():
            return super(HumbleDoubleSpinBox, self).wheelEvent(event)
        else:
            event.ignore()


class HumbleSpinBox(QSpinBox):
    """It's a spin box that doesn't let you enter a value that's too close to zero."""

    def __init__(self, *args):
        """
        The function sets the focus policy of the spinbox to strong focus
        """
        super(HumbleSpinBox, self).__init__(*args)
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setFixedWidth(60)
        self.setMaximum(99999999)
        self.setMinimum(-99999999)
        self.setAccelerated(True)

    def focusInEvent(self, event):
        """
        When the user clicks on the spinbox, the focus policy is changed to allow the mouse wheel to be
        used to change the value

        Args:
          event: QFocusEvent
        """
        self.setFocusPolicy(Qt.WheelFocus)
        super(HumbleSpinBox, self).focusInEvent(event)

    def focusOutEvent(self, event):
        """
        When the user clicks on the spinbox, the focus policy is changed to StrongFocus, and then the
        focusOutEvent is called

        Args:
          event: QFocusEvent
        """
        self.setFocusPolicy(Qt.StrongFocus)
        super(HumbleSpinBox, self).focusOutEvent(event)

    def wheelEvent(self, event):
        """
        If the spinbox has focus, then it will behave as normal. If it doesn't have focus, then the
        wheel event will be ignored

        Args:
          event: The event object

        Returns:
          The super class of the HumbleSpinBox class.
        """
        if self.hasFocus():
            return super(HumbleSpinBox, self).wheelEvent(event)
        else:
            event.ignore()


class CurrentQuantitySpinBox(QSpinBox):
    """It's a spin box that doesn't let you enter a value that's too close to zero."""

    def __init__(self, *args):
        """
        The function sets the focus policy of the spinbox to strong focus
        """
        super(CurrentQuantitySpinBox, self).__init__(*args)
        self.setFocusPolicy(Qt.StrongFocus)
        # self.setFixedWidth(100)
        self.setMaximum(99999999)
        self.setMinimum(-99999999)
        self.setAccelerated(True)
        self.lineEdit().setReadOnly(True)
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)

    def focusInEvent(self, event):
        """
        When the user clicks on the spinbox, the focus policy is changed to allow the mouse wheel to be
        used to change the value

        Args:
          event: QFocusEvent
        """
        self.setFocusPolicy(Qt.WheelFocus)
        super(CurrentQuantitySpinBox, self).focusInEvent(event)

    def focusOutEvent(self, event):
        """
        When the user clicks on the spinbox, the focus policy is changed to StrongFocus, and then the
        focusOutEvent is called

        Args:
          event: QFocusEvent
        """
        self.setFocusPolicy(Qt.StrongFocus)
        super(CurrentQuantitySpinBox, self).focusOutEvent(event)

    def wheelEvent(self, event):
        """
        ignore all wheel events
        """
        event.ignore()


class HumbleComboBox(QComboBox):
    """> A QComboBox that can be set to a default value"""

    def __init__(self, scrollWidget=None, *args, **kwargs):
        """
        It sets the focus policy to strong focus.

        Args:
          scrollWidget: The widget that will be scrolled when the combobox is opened.
        """
        super(HumbleComboBox, self).__init__(*args, **kwargs)
        self.scrollWidget = scrollWidget
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, *args, **kwargs):
        """
        If the combobox has focus, then the wheel event is handled by the combobox, otherwise the wheel
        event is handled by the scroll widget

        Returns:
          The return value is the return value of the last statement in the function.
        """
        if self.hasFocus():
            return QComboBox.wheelEvent(self, *args, **kwargs)
        else:
            return self.scrollWidget.wheelEvent(*args, **kwargs)


class PlaceholderTextComboBox(QComboBox):
    """This class is a subclass of QComboBox that allows the user to enter text into the combo box that is
    not in the list of items"""

    def paintEvent(self, event):
        """
        It draws the combobox frame, focusrect and selected etc

        Args:
          event: The event that triggered the paintEvent.
        """

        painter = QStylePainter(self)
        painter.setPen(self.palette().color(QPalette.Text))

        # draw the combobox frame, focusrect and selected etc.
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        painter.drawComplexControl(QStyle.CC_ComboBox, opt)

        if self.currentIndex() < 0:
            opt.palette.setBrush(
                QPalette.ButtonText,
                opt.palette.brush(QPalette.ButtonText).color().lighter(),
            )
            if self.placeholderText():
                opt.currentText = self.placeholderText()

        # draw the icon and text
        painter.drawControl(QStyle.CE_ComboBoxLabel, opt)


class ViewTree(QTreeWidget):
    """It's a QTreeWidget that displays a list of files and folders"""

    def __init__(self, data):
        """
        It takes a value and creates a tree widget item for it.

        If the value is a dictionary, it creates a child item for each key and value pair.

        If the value is a list or tuple, it creates a child item for each value.

        If the value is anything else, it creates a child item with the value as its text.

        The function is recursive, so if the value is a dictionary or list, it calls itself to create
        the child items.

        The function is also a nested function, so it can access the item argument of the outer
        function.

        The function is also a nested function, so it can access the item argument of the outer
        function.

        The function is also a nested function, so it can access the item argument of the outer
        function.

        The function is also a nested function, so it can access the item argument of the outer
        function.

        Args:
          value: The value to be displayed in the tree.
        """
        super().__init__()
        self.data = data
        self.setHeaderLabels(
            [
                "Name",
                "Part Number",
                "Unit Quantity",
                "Current Quantity",
                "Price",
                "Priority",
                "Notes",
            ]
        )
        self.setColumnWidth(0, 400)
        self.setColumnWidth(1, 70)
        self.setColumnWidth(2, 70)
        self.setColumnWidth(3, 90)
        self.setColumnWidth(4, 50)
        self.setColumnWidth(5, 40)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)
        self.setAlternatingRowColors(True)
        delegate = StyledItemDelegate(self)
        self.setItemDelegate(delegate)
        self.load_ui()

    def load_ui(self) -> None:
        def fill_item(item, value):
            """
            It takes a QTreeWidgetItem and a value, and if the value is a dict, list, or tuple, it
            creates a new QTreeWidgetItem for each key/value pair or list item, and recursively calls
            itself on each of those new QTreeWidgetItems

            Args:
              item: The item to fill
              value: The value to be displayed in the tree.

            Returns:
              A dictionary with a list of dictionaries.
            """

            def new_item(parent, text, val=None):
                if type(val) != dict:
                    child = QTreeWidgetItem([text, str(val)])
                else:
                    try:
                        child = QTreeWidgetItem(
                            [
                                text,
                                str(val["part_number"]),
                                str(val["unit_quantity"]),
                                str(val["current_quantity"]),
                                str(val["price"]),
                                str(val["priority"]),
                                str(val["notes"]),
                            ]
                        )
                    except KeyError:
                        child = QTreeWidgetItem([text])
                        fill_item(child, val)
                parent.addChild(child)

            if value is None:
                return
            elif isinstance(value, dict):
                for key, val in sorted(value.items()):
                    new_item(item, str(key), val)
            elif isinstance(value, (list, tuple)):
                for val in value:
                    text = (
                        f"[{type(val).__name__}]"
                        if isinstance(val, (dict, list, tuple))
                        else str(val)
                    )
                    new_item(item, text, val)

        fill_item(self.invisibleRootItem(), self.data)


class HeaderScrollArea(QScrollArea):
    """This class is a QScrollArea that has a header widget that is always visible"""

    def __init__(self, headers: dict[str:int], parent=None):
        """
        A QScrollArea with a QGridLayout inside of it. I'm then creating a QWidget with a
        QGridLayout inside of it and adding it to the QScrollArea. I'm then creating a QWidget with a
        QGridLayout inside of it and adding it to the QScrollArea.

        Args:
          headers (dict({str: int})): dict({str: int})
          parent: The parent widget.
        """
        QScrollArea.__init__(self, parent)
        self.headers: dict({str: int}) = headers

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setHorizontalSpacing(0)
        self.grid_layout.setVerticalSpacing(0)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_widget.setLayout(self.grid_layout)
        self.setWidgetResizable(True)
        self.setWidget(self.grid_widget)

        self.margins = QMargins(0, 30, 0, 0)
        self.setViewportMargins(self.margins)
        self.headings_widget = QWidget(self)
        self.headings_widget.setStyleSheet("border-bottom: 1px solid #3daee9;")
        self.headings_layout = QGridLayout()
        self.headings_layout.setAlignment(Qt.AlignLeft)
        self.headings_widget.setLayout(self.headings_layout)
        self.headings_layout.setContentsMargins(0, 0, 0, 0)
        self.headings_layout.columnStretch(0)
        for col_index, header in enumerate(list(self.headers.keys())):
            heading = QLabel(header)
            heading.setFixedWidth(self.headers[header])
            heading.setContentsMargins(0, 0, 0, 0)
            self.headings_layout.addWidget(heading, 0, col_index)
            self.headings_layout.setColumnStretch(col_index, 0)

    def resizeEvent(self, event) -> None:
        """
        The function is called when the scroll area is resized. It resizes the headings widget to match
        the width of the scroll area and positions it at the top of the scroll area

        Args:
          event: QResizeEvent
        """
        rect = self.viewport().geometry()
        self.headings_widget.setGeometry(
            rect.x(), rect.y() - self.margins.top(), rect.width(), self.margins.top()
        )
        QScrollArea.resizeEvent(self, event)


class DragableLayout(QWidget):
    """
    Generic list sorting handler.
    """

    orderChanged = pyqtSignal(list)

    def __init__(self, *args, orientation=Qt.Orientation.Vertical, **kwargs):
        super().__init__()
        self.setAcceptDrops(True)

        # Store the orientation for drag checks later.
        self.orientation = orientation

        if self.orientation == Qt.Orientation.Vertical:
            self.blayout = QVBoxLayout()
        else:
            self.blayout = QHBoxLayout()

        self.setLayout(self.blayout)

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        pos = e.pos()
        widget = e.source()

        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            if self.orientation == Qt.Orientation.Vertical:
                # Drag drop vertically.
                drop_here = pos.y() < w.y() + w.size().height() // 2
            else:
                # Drag drop horizontally.
                drop_here = pos.x() < w.x() + w.size().width() // 2

            if drop_here:
                # We didn't drag past this widget.
                # insert to the left of it.
                self.blayout.insertWidget(n - 1, widget)
                self.orderChanged.emit(self.get_item_data())
                break

        e.accept()

    def add_item(self, item):
        self.blayout.addWidget(item)

    def get_item_data(self):
        data = []
        for n in range(self.blayout.count()):
            # Get the widget at each index in turn.
            w = self.blayout.itemAt(n).widget()
            data.append(w.data)
        return data


class StyledItemDelegate(QStyledItemDelegate):
    """It's a delegate that can be used to display and edit data items from a model"""

    def sizeHint(self, option, index):
        """
        If the index is not a child of a parent, then set the height to 60

        Args:
          option: QStyleOptionViewItem
          index: The index of the item to be drawn.

        Returns:
          The size of the item.
        """
        item = super(StyledItemDelegate, self).sizeHint(option, index)
        if not index.parent().isValid():
            item.setHeight(60)
        return item


def set_default_dialog_button_stylesheet(button: QPushButton) -> None:
    """
    It sets the style sheet of the button

    Args:
        button (QPushButton): QPushButton
    """
    button.setStyleSheet(
        """
        QPushButton#default_dialog_button{
            background-color: #3daee9;
            border: 0.04em solid  #3daee9;
            border-radius: 5px;
        }
        QPushButton#default_dialog_button:hover{
            background-color: #49b3eb;
            border: 0.04em solid  #49b3eb;
            border-radius: 5px;
        }
        QPushButton#default_dialog_button:pressed{
            background-color: #5cbaed;
            color: #bae2f8;
            border: 0.04em solid  #5cbaed;
            border-radius: 5px;
        }
        QPushButton#default_dialog_button:disabled{
            background-color: #222222;
            color: gray;
            border: 0.04em solid  gray;
            border-radius: 1px;
        }
        """
    )


def set_status_button_stylesheet(button: QPushButton, color: str) -> None:
    """
    It sets the style sheet of the button

    Args:
        button (QPushButton): QPushButton
    """
    background_color = 'rgb(71, 71, 71)'
    border_color = 'rgb(71, 71, 71)'
    if color == 'lime':
        background_color = 'darkgreen'
        border_color = 'green'
    elif color == 'yellow':
        background_color = '#413C28'
        border_color = 'gold'
    elif color == 'red':
        background_color = '#3F1E25'
        border_color = 'darkred'
    elif color == '#3daee9':
        background_color = '#1E363F'
        border_color = "#3E8C99"
    button.setStyleSheet(
        """
        QPushButton#status_button:flat {
            border: none;
        }
        QPushButton#status_button{
            border: 0.04em solid  %(background_color)s;
            background-color: %(background_color)s;
            border-radius: 5px;
            color: %(color)s;
        }
        QPushButton#status_button:hover{
            border: 0.04em solid  %(border_color)s;
            border-radius: 5px;
        }
        QPushButton#status_button:pressed{
            border: 0.15em solid  %(border_color)s;
            border-radius: 5px;
        }
        """
        % {"color": color, "border_color": border_color, "background_color": background_color}
    )
