from PyQt5.QtCore import QMargins, QMimeData, Qt, pyqtSignal
from PyQt5.QtGui import QDrag, QIcon, QPalette, QPixmap
from PyQt5.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
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
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


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

class NoScrollTabWidget(QTabWidget):
    """This is a custom class that inherits from QTabWidget and disables scrolling functionality."""

    def __init__(self, parent=None):
        super(NoScrollTabWidget, self).__init__(parent)
        self.tabBar().installEventFilter(self)
        self.wheelEvent = lambda event: None

    def wheelEvent(self, event):
        """
        This function ignores the wheel event.

        Args:
          event: The event parameter in this code refers to a QWheelEvent object, which is an event that
        occurs when the user rotates the mouse wheel. This function is a method of a class that inherits
        from QWidget, and it is used to handle the wheel event when it occurs on the widget.
        """
        event.ignore()


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
        round_number = lambda x, n: eval(
            '"%.'
            + str(int(n))
            + 'f" % '
            + repr(int(x) + round(float("." + str(float(x)).split(".")[1]), n))
        )
        self.setStyleSheet("border: 0.09em solid rgb(57, 57, 57); background-color: #222222;")
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
    """It's a QLabel that emits a signal when it's clicked"""

    def __init__(self, clicked, parent=None):
        """
        The function __init__ is a constructor that initializes the class

        Args:
          clicked: a function that will be called when the label is clicked.
          parent: The parent widget.
        """
        QLabel.__init__(self, parent)
        self.__clicked = clicked

    def mouseReleaseEvent(self, event):
        """
        The function is called when the mouse is released

        Args:
          event: QMouseEvent
        """
        self.__clicked(event)


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
        self.__lbl.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)  # type: ignore
        self.__lbl.setAttribute(Qt.WA_TransparentForMouseEvents)  # type: ignore
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
    button.setStyleSheet(
        """
        QPushButton#status_button:flat {
            border: none;
        }
        QPushButton#status_button{
            border: 0.04em solid  %(color)s;
            border-radius: 5px;
        }
        QPushButton#status_button:hover{
            border: 0.04em solid  %(color)s;
            border-radius: 5px;
        }
        QPushButton#status_button:pressed{
            background-color: black;
            border: 0.04em solid  %(color)s;
            border-radius: 5px;
            color: white;
        }
        """
        % {"color": color}
    )
