# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'f:\Code\Python-Projects\Inventory Manager\dist\ui\add_item_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(453, 373)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.frame = QtWidgets.QFrame(Form)
        self.frame.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.frame.setAutoFillBackground(False)
        self.frame.setStyleSheet("")
        self.frame.setFrameShape(QtWidgets.QFrame.Box)
        self.frame.setObjectName("frame")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.lblTitle = QtWidgets.QLabel(self.frame)
        self.lblTitle.setMaximumSize(QtCore.QSize(16777215, 16777215))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lblTitle.setFont(font)
        self.lblTitle.setFrameShape(QtWidgets.QFrame.WinPanel)
        self.lblTitle.setFrameShadow(QtWidgets.QFrame.Raised)
        self.lblTitle.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.lblTitle.setObjectName("lblTitle")
        self.verticalLayout_3.addWidget(self.lblTitle)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.iconHolder = QtWidgets.QVBoxLayout()
        self.iconHolder.setSpacing(0)
        self.iconHolder.setObjectName("iconHolder")
        self.verticalLayout_2.addLayout(self.iconHolder)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.horizontalLayout_4.addLayout(self.verticalLayout_2)
        self.scrollArea = QtWidgets.QScrollArea(self.frame)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 401, 69))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.lblMessage = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblMessage.sizePolicy().hasHeightForWidth())
        self.lblMessage.setSizePolicy(sizePolicy)
        self.lblMessage.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.lblMessage.setObjectName("lblMessage")
        self.verticalLayout_4.addWidget(self.lblMessage)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.horizontalLayout_4.addWidget(self.scrollArea)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.lineEdit_part_number = QtWidgets.QLineEdit(self.frame)
        self.lineEdit_part_number.setObjectName("lineEdit_part_number")
        self.gridLayout.addWidget(self.lineEdit_part_number, 1, 2, 1, 1)
        self.doubleSpinBox_price = QtWidgets.QDoubleSpinBox(self.frame)
        self.doubleSpinBox_price.setMaximum(999999999.0)
        self.doubleSpinBox_price.setObjectName("doubleSpinBox_price")
        self.gridLayout.addWidget(self.doubleSpinBox_price, 5, 2, 1, 1)
        self.plainTextEdit_notes = QtWidgets.QPlainTextEdit(self.frame)
        self.plainTextEdit_notes.setObjectName("plainTextEdit_notes")
        self.gridLayout.addWidget(self.plainTextEdit_notes, 6, 2, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.frame)
        self.label_4.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 6, 0, 1, 1)
        self.label = QtWidgets.QLabel(self.frame)
        self.label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.frame)
        self.label_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.comboBox_priority = QtWidgets.QComboBox(self.frame)
        self.comboBox_priority.setEditable(False)
        self.comboBox_priority.setObjectName("comboBox_priority")
        self.comboBox_priority.addItem("")
        self.comboBox_priority.addItem("")
        self.comboBox_priority.addItem("")
        self.comboBox_priority.addItem("")
        self.gridLayout.addWidget(self.comboBox_priority, 2, 2, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.frame)
        self.label_5.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 5, 0, 1, 1)
        self.spinBox_current_quantity = QtWidgets.QSpinBox(self.frame)
        self.spinBox_current_quantity.setMaximum(9999999)
        self.spinBox_current_quantity.setObjectName("spinBox_current_quantity")
        self.gridLayout.addWidget(self.spinBox_current_quantity, 3, 2, 1, 1)
        self.label_7 = QtWidgets.QLabel(self.frame)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 3, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.frame)
        self.label_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 1)
        self.spinBox_unit_quantity = QtWidgets.QSpinBox(self.frame)
        self.spinBox_unit_quantity.setMaximum(9999999)
        self.spinBox_unit_quantity.setObjectName("spinBox_unit_quantity")
        self.gridLayout.addWidget(self.spinBox_unit_quantity, 4, 2, 1, 1)
        self.label_6 = QtWidgets.QLabel(self.frame)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 1, 0, 1, 1)
        self.lineEdit_name = QtWidgets.QLineEdit(self.frame)
        self.lineEdit_name.setObjectName("lineEdit_name")
        self.gridLayout.addWidget(self.lineEdit_name, 0, 2, 1, 1)
        self.comboBox_exchange_price = QtWidgets.QComboBox(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox_exchange_price.sizePolicy().hasHeightForWidth())
        self.comboBox_exchange_price.setSizePolicy(sizePolicy)
        self.comboBox_exchange_price.setMaximumSize(QtCore.QSize(50, 16777215))
        self.comboBox_exchange_price.setObjectName("comboBox_exchange_price")
        self.comboBox_exchange_price.addItem("")
        self.comboBox_exchange_price.addItem("")
        self.gridLayout.addWidget(self.comboBox_exchange_price, 5, 3, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.buttonsLayout = QtWidgets.QHBoxLayout()
        self.buttonsLayout.setObjectName("buttonsLayout")
        self.verticalLayout.addLayout(self.buttonsLayout)
        self.verticalLayout_3.addLayout(self.verticalLayout)
        self.horizontalLayout.addWidget(self.frame)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.lblTitle.setText(_translate("Form", "TextLabel"))
        self.lblMessage.setText(_translate("Form", "TextLabel"))
        self.lineEdit_part_number.setPlaceholderText(_translate("Form", "Enter part number"))
        self.doubleSpinBox_price.setPrefix(_translate("Form", "$"))
        self.doubleSpinBox_price.setSuffix(_translate("Form", " CAD"))
        self.plainTextEdit_notes.setPlainText(_translate("Form", "Vendor: \n"
"Description: "))
        self.plainTextEdit_notes.setPlaceholderText(_translate("Form", "Notes..."))
        self.label_4.setText(_translate("Form", "Notes:"))
        self.label.setText(_translate("Form", "Item name:"))
        self.label_2.setText(_translate("Form", "Priority:"))
        self.comboBox_priority.setItemText(0, _translate("Form", "Default"))
        self.comboBox_priority.setItemText(1, _translate("Form", "Low"))
        self.comboBox_priority.setItemText(2, _translate("Form", "Medium"))
        self.comboBox_priority.setItemText(3, _translate("Form", "High"))
        self.label_5.setText(_translate("Form", "Item Price:"))
        self.label_7.setText(_translate("Form", "Current Quantity:"))
        self.label_3.setText(_translate("Form", "Unit Quantity:"))
        self.label_6.setText(_translate("Form", "Part Number:"))
        self.lineEdit_name.setPlaceholderText(_translate("Form", "Enter item name"))
        self.comboBox_exchange_price.setCurrentText(_translate("Form", "CAD"))
        self.comboBox_exchange_price.setItemText(0, _translate("Form", "CAD"))
        self.comboBox_exchange_price.setItemText(1, _translate("Form", "USD"))
