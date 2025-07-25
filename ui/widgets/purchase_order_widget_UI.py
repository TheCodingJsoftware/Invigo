# Form implementation generated from reading ui file '/mnt/SafeHaven/Forge/Inventory Manager/ui/widgets/purchase_order_widget.ui'
#
# Created by: PyQt6 UI code generator 6.9.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(996, 930)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label_5 = QtWidgets.QLabel(parent=Form)
        self.label_5.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 1, 0, 1, 1)
        self.label = QtWidgets.QLabel(parent=Form)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.doubleSpinBox_po_number = QtWidgets.QDoubleSpinBox(parent=Form)
        self.doubleSpinBox_po_number.setDecimals(0)
        self.doubleSpinBox_po_number.setMaximum(99999999999999.0)
        self.doubleSpinBox_po_number.setObjectName("doubleSpinBox_po_number")
        self.gridLayout.addWidget(self.doubleSpinBox_po_number, 2, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(parent=Form)
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setContentsMargins(-1, -1, 0, -1)
        self.horizontalLayout_5.setSpacing(6)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.comboBox_vendor = QtWidgets.QComboBox(parent=Form)
        self.comboBox_vendor.setObjectName("comboBox_vendor")
        self.horizontalLayout_5.addWidget(self.comboBox_vendor)
        self.pushButton_edit_vendor = QtWidgets.QPushButton(parent=Form)
        self.pushButton_edit_vendor.setMaximumSize(QtCore.QSize(32, 32))
        self.pushButton_edit_vendor.setText("")
        icon = QtGui.QIcon.fromTheme("edit")
        self.pushButton_edit_vendor.setIcon(icon)
        self.pushButton_edit_vendor.setObjectName("pushButton_edit_vendor")
        self.horizontalLayout_5.addWidget(self.pushButton_edit_vendor)
        self.horizontalLayout_5.setStretch(0, 1)
        self.gridLayout.addLayout(self.horizontalLayout_5, 0, 1, 1, 1)
        self.comboBox = QtWidgets.QComboBox(parent=Form)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.gridLayout.addWidget(self.comboBox, 1, 1, 1, 1)
        self.lineEdit_authorized_by = QtWidgets.QLineEdit(parent=Form)
        self.lineEdit_authorized_by.setObjectName("lineEdit_authorized_by")
        self.gridLayout.addWidget(self.lineEdit_authorized_by, 4, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(parent=Form)
        self.label_3.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 1)
        self.label_6 = QtWidgets.QLabel(parent=Form)
        self.label_6.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 3, 0, 1, 1)
        self.dateEdit_order_date = QtWidgets.QDateEdit(parent=Form)
        self.dateEdit_order_date.setCalendarPopup(True)
        self.dateEdit_order_date.setObjectName("dateEdit_order_date")
        self.gridLayout.addWidget(self.dateEdit_order_date, 3, 1, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_4 = QtWidgets.QLabel(parent=Form)
        self.label_4.setObjectName("label_4")
        self.gridLayout_2.addWidget(self.label_4, 0, 0, 1, 1)
        self.textEdit = QtWidgets.QTextEdit(parent=Form)
        self.textEdit.setObjectName("textEdit")
        self.gridLayout_2.addWidget(self.textEdit, 1, 0, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout_2)
        self.horizontalLayout.setStretch(0, 1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.pushButton_components = QtWidgets.QPushButton(parent=Form)
        self.pushButton_components.setCheckable(True)
        self.pushButton_components.setObjectName("pushButton_components")
        self.verticalLayout_3.addWidget(self.pushButton_components)
        self.widget_components = QtWidgets.QWidget(parent=Form)
        self.widget_components.setObjectName("widget_components")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.widget_components)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 3)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.layout_components = QtWidgets.QVBoxLayout()
        self.layout_components.setObjectName("layout_components")
        self.verticalLayout_5.addLayout(self.layout_components)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButton = QtWidgets.QPushButton(parent=self.widget_components)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_2.addWidget(self.pushButton)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.verticalLayout_5.addLayout(self.horizontalLayout_2)
        self.verticalLayout_5.setStretch(0, 1)
        self.verticalLayout_3.addWidget(self.widget_components)
        self.pushButton_sheets = QtWidgets.QPushButton(parent=Form)
        self.pushButton_sheets.setCheckable(True)
        self.pushButton_sheets.setObjectName("pushButton_sheets")
        self.verticalLayout_3.addWidget(self.pushButton_sheets)
        self.widget_sheets = QtWidgets.QWidget(parent=Form)
        self.widget_sheets.setObjectName("widget_sheets")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.widget_sheets)
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 3)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.layout_sheets = QtWidgets.QVBoxLayout()
        self.layout_sheets.setObjectName("layout_sheets")
        self.verticalLayout_7.addLayout(self.layout_sheets)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.pushButton_2 = QtWidgets.QPushButton(parent=self.widget_sheets)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_4.addWidget(self.pushButton_2)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.verticalLayout_7.addLayout(self.horizontalLayout_4)
        self.verticalLayout_7.setStretch(0, 1)
        self.verticalLayout_3.addWidget(self.widget_sheets)
        self.verticalLayout_3.setStretch(1, 1)
        self.verticalLayout_3.setStretch(3, 1)
        self.verticalLayout.addLayout(self.verticalLayout_3)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.label.setBuddy(self.doubleSpinBox_po_number)
        self.label_2.setBuddy(self.comboBox_vendor)
        self.label_3.setBuddy(self.lineEdit_authorized_by)
        self.label_4.setBuddy(self.textEdit)

        self.retranslateUi(Form)
        self.pushButton_components.clicked['bool'].connect(self.widget_components.setVisible) # type: ignore
        self.pushButton_sheets.clicked['bool'].connect(self.widget_sheets.setVisible) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_5.setText(_translate("Form", "Status:"))
        self.label.setText(_translate("Form", "PO number:"))
        self.label_2.setText(_translate("Form", "Vendor:"))
        self.comboBox.setItemText(0, _translate("Form", "Purchase Order"))
        self.comboBox.setItemText(1, _translate("Form", "Quote"))
        self.lineEdit_authorized_by.setText(_translate("Form", "Lynden Gross"))
        self.lineEdit_authorized_by.setPlaceholderText(_translate("Form", "Authorized by..."))
        self.label_3.setText(_translate("Form", "Authorized by:"))
        self.label_6.setText(_translate("Form", "Order date:"))
        self.label_4.setText(_translate("Form", "Ship to:"))
        self.textEdit.setHtml(_translate("Form", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:\'Noto Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:16pt; font-weight:700;\">Piney Mfg.</span></p>\n"
"<p align=\"center\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">1113 RD 67 East</p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Hwy 89 South</p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Piney, MB. R0A 1K0</p>\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">+1 (204) 371-1209</p></body></html>"))
        self.pushButton_components.setText(_translate("Form", "Components"))
        self.pushButton.setText(_translate("Form", "Add Component"))
        self.pushButton_sheets.setText(_translate("Form", "Sheets"))
        self.pushButton_2.setText(_translate("Form", "Add Sheet"))
