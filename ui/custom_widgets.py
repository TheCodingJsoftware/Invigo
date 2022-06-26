from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy


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
