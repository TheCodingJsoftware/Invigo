# Form implementation generated from reading ui file 'C:\Users\Jared\Documents\Code\Python-Projects\Inventory Manager\ui\dialogs\set_component_order_pending_dialog.ui'
#
# Created by: PyQt6 UI code generator 6.7.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(320, 600)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.widget = QtWidgets.QWidget(parent=Form)
        self.widget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.ActionsContextMenu)
        self.widget.setAutoFillBackground(False)
        self.widget.setStyleSheet("")
        self.widget.setObjectName("widget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lblMessage = QtWidgets.QLabel(parent=self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblMessage.sizePolicy().hasHeightForWidth())
        self.lblMessage.setSizePolicy(sizePolicy)
        self.lblMessage.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignTop)
        self.lblMessage.setWordWrap(True)
        self.lblMessage.setObjectName("lblMessage")
        self.verticalLayout.addWidget(self.lblMessage)
        self.calendarWidget = QtWidgets.QCalendarWidget(parent=self.widget)
        self.calendarWidget.setGridVisible(False)
        self.calendarWidget.setVerticalHeaderFormat(QtWidgets.QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendarWidget.setObjectName("calendarWidget")
        self.verticalLayout.addWidget(self.calendarWidget)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(parent=self.widget)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.doubleSpinBox_sheets_ordered = QtWidgets.QDoubleSpinBox(parent=self.widget)
        self.doubleSpinBox_sheets_ordered.setWrapping(False)
        self.doubleSpinBox_sheets_ordered.setFrame(True)
        self.doubleSpinBox_sheets_ordered.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.doubleSpinBox_sheets_ordered.setSpecialValueText("")
        self.doubleSpinBox_sheets_ordered.setProperty("showGroupSeparator", False)
        self.doubleSpinBox_sheets_ordered.setMaximum(999999.0)
        self.doubleSpinBox_sheets_ordered.setObjectName("doubleSpinBox_sheets_ordered")
        self.horizontalLayout_2.addWidget(self.doubleSpinBox_sheets_ordered)
        self.horizontalLayout_2.setStretch(1, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.label_2 = QtWidgets.QLabel(parent=self.widget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.textEdit_notes = QtWidgets.QTextEdit(parent=self.widget)
        self.textEdit_notes.setObjectName("textEdit_notes")
        self.verticalLayout.addWidget(self.textEdit_notes)
        self.buttonsLayout = QtWidgets.QHBoxLayout()
        self.buttonsLayout.setObjectName("buttonsLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.buttonsLayout.addItem(spacerItem)
        self.pushButton_set = QtWidgets.QPushButton(parent=self.widget)
        self.pushButton_set.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.pushButton_set.setObjectName("pushButton_set")
        self.buttonsLayout.addWidget(self.pushButton_set)
        self.pushButton_cancel = QtWidgets.QPushButton(parent=self.widget)
        self.pushButton_cancel.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.pushButton_cancel.setObjectName("pushButton_cancel")
        self.buttonsLayout.addWidget(self.pushButton_cancel)
        self.verticalLayout.addLayout(self.buttonsLayout)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout_3.addLayout(self.verticalLayout)
        self.horizontalLayout.addWidget(self.widget)
        self.label.setBuddy(self.doubleSpinBox_sheets_ordered)
        self.label_2.setBuddy(self.textEdit_notes)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.calendarWidget, self.doubleSpinBox_sheets_ordered)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.lblMessage.setText(_translate("Form", "TextLabel"))
        self.label.setText(_translate("Form", "Parts ordered:"))
        self.doubleSpinBox_sheets_ordered.setToolTip(_translate("Form", "You will see this number in the order pending button."))
        self.label_2.setText(_translate("Form", "Notes:"))
        self.textEdit_notes.setToolTip(_translate("Form", "You will see these notes when you hover over the order pending button"))
        self.textEdit_notes.setPlaceholderText(_translate("Form", "Enter notes for this order..."))
        self.pushButton_set.setText(_translate("Form", "Set"))
        self.pushButton_cancel.setText(_translate("Form", "Cancel"))
