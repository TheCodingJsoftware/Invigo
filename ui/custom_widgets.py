from typing import Type

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
)


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


class ViewTree(QTreeWidget):
    """It's a QTreeWidget that displays a list of files and folders"""

    def __init__(self, value):
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
        self.setHeaderLabels(["Name", "Value"])

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
                        str(val)
                        if not isinstance(val, (dict, list, tuple))
                        else "[%s]" % type(val).__name__
                    )
                    new_item(item, text, val)

        fill_item(self.invisibleRootItem(), value)
