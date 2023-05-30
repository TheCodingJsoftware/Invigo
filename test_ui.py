import sys

from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QTextEdit, QWidget


class SplitTerminal(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        self.left_text_edit = QTextEdit(self)
        self.right_text_edit = QTextEdit(self)

        layout.addWidget(self.left_text_edit)
        layout.addWidget(self.right_text_edit)

        self.left_text_edit.setReadOnly(True)
        self.right_text_edit.setReadOnly(True)

        sys.stdout = TerminalWriter(self.left_text_edit)
        self.right_text_edit.append("Connected Clients:")


class TerminalWriter:
    def __init__(self, text_edit):
        self.text_edit = text_edit

    def write(self, text):
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()

    def flush(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = QMainWindow()
    terminal = SplitTerminal(window)
    window.setCentralWidget(terminal)

    window.show()

    print("This is a print statement")
    print("Another print statement")

    sys.exit(app.exec_())
