from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QAbstractItemModel, QAbstractTableModel, QDate, QDateTime, QEvent, QMargins, QMimeData, QModelIndex, QPoint, QRegularExpression, QSettings, QSize, QSortFilterProxyModel, Qt, QTime, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QClipboard, QColor, QCursor, QDrag, QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent, QFileSystemModel, QIcon, QKeySequence, QMouseEvent, QPainter, QPalette, QPixmap, QRegularExpressionValidator, QStandardItem, QStandardItemModel, QTextCharFormat
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QApplication,
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplashScreen,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionComboBox,
    QStylePainter,
    QTabBar,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBox,
    QToolButton,
    QTreeView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class JobTab(QTabWidget):
    def __init__(self, parent) -> None:
        super(JobTab, self).__init__(parent)
        self.setUsesScrollButtons(True)
        self.setTabsClosable(True)
        self.setDocumentMode(True)
        self.setMovable(True)
        self.setObjectName("job_planner_tab_widget")
        self.setStyleSheet("QTabWidget#job_planner_tab_widget > QWidget { border-bottom-left-radius: 0px; }")
