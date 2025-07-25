# Form implementation generated from reading ui file '/mnt/SafeHaven/Forge/Inventory Manager/ui/dialogs/purchase_order_dialog.ui'
#
# Created by: PyQt6 UI code generator 6.9.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.setWindowModality(QtCore.Qt.WindowModality.NonModal)
        Dialog.resize(1356, 636)
        Dialog.setSizeGripEnabled(False)
        Dialog.setModal(False)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.splitter = QtWidgets.QSplitter(parent=Dialog)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.splitter.setObjectName("splitter")
        self.layoutWidget = QtWidgets.QWidget(parent=self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.comboBox_status = QtWidgets.QComboBox(parent=self.layoutWidget)
        self.comboBox_status.setObjectName("comboBox_status")
        self.gridLayout.addWidget(self.comboBox_status, 1, 2, 1, 1)
        self.label = QtWidgets.QLabel(parent=self.layoutWidget)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 4, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(parent=self.layoutWidget)
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(parent=self.layoutWidget)
        self.label_3.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)
        self.doubleSpinBox_po_number = QtWidgets.QDoubleSpinBox(parent=self.layoutWidget)
        self.doubleSpinBox_po_number.setDecimals(0)
        self.doubleSpinBox_po_number.setMaximum(99999999999999.0)
        self.doubleSpinBox_po_number.setObjectName("doubleSpinBox_po_number")
        self.gridLayout.addWidget(self.doubleSpinBox_po_number, 4, 2, 1, 1)
        self.comboBox_shipping_method = QtWidgets.QComboBox(parent=self.layoutWidget)
        self.comboBox_shipping_method.setObjectName("comboBox_shipping_method")
        self.gridLayout.addWidget(self.comboBox_shipping_method, 2, 2, 1, 1)
        self.label_6 = QtWidgets.QLabel(parent=self.layoutWidget)
        self.label_6.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 5, 0, 1, 1)
        self.label_5 = QtWidgets.QLabel(parent=self.layoutWidget)
        self.label_5.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 1, 0, 1, 1)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setContentsMargins(-1, -1, 0, -1)
        self.horizontalLayout_5.setSpacing(6)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.pushButton_autofill = QtWidgets.QPushButton(parent=self.layoutWidget)
        self.pushButton_autofill.setObjectName("pushButton_autofill")
        self.horizontalLayout_5.addWidget(self.pushButton_autofill)
        self.comboBox_vendor = QtWidgets.QComboBox(parent=self.layoutWidget)
        self.comboBox_vendor.setObjectName("comboBox_vendor")
        self.horizontalLayout_5.addWidget(self.comboBox_vendor)
        self.pushButton_edit_vendor = QtWidgets.QPushButton(parent=self.layoutWidget)
        self.pushButton_edit_vendor.setMaximumSize(QtCore.QSize(32, 32))
        self.pushButton_edit_vendor.setText("")
        self.pushButton_edit_vendor.setFlat(True)
        self.pushButton_edit_vendor.setObjectName("pushButton_edit_vendor")
        self.horizontalLayout_5.addWidget(self.pushButton_edit_vendor)
        self.horizontalLayout_5.setStretch(1, 1)
        self.gridLayout.addLayout(self.horizontalLayout_5, 0, 2, 1, 1)
        self.dateEdit_expected_arrival = QtWidgets.QDateEdit(parent=self.layoutWidget)
        self.dateEdit_expected_arrival.setCalendarPopup(True)
        self.dateEdit_expected_arrival.setObjectName("dateEdit_expected_arrival")
        self.gridLayout.addWidget(self.dateEdit_expected_arrival, 5, 2, 1, 1)
        self.label_8 = QtWidgets.QLabel(parent=self.layoutWidget)
        self.label_8.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_8.setObjectName("label_8")
        self.gridLayout.addWidget(self.label_8, 2, 0, 1, 1)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.comboBox_shipping_address = QtWidgets.QComboBox(parent=self.layoutWidget)
        self.comboBox_shipping_address.setObjectName("comboBox_shipping_address")
        self.horizontalLayout_7.addWidget(self.comboBox_shipping_address)
        self.pushButton_edit_shipping_address = QtWidgets.QPushButton(parent=self.layoutWidget)
        self.pushButton_edit_shipping_address.setMaximumSize(QtCore.QSize(32, 32))
        self.pushButton_edit_shipping_address.setText("")
        self.pushButton_edit_shipping_address.setFlat(True)
        self.pushButton_edit_shipping_address.setObjectName("pushButton_edit_shipping_address")
        self.horizontalLayout_7.addWidget(self.pushButton_edit_shipping_address)
        self.gridLayout.addLayout(self.horizontalLayout_7, 3, 2, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.label_7 = QtWidgets.QLabel(parent=self.layoutWidget)
        self.label_7.setObjectName("label_7")
        self.gridLayout_4.addWidget(self.label_7, 0, 0, 1, 1)
        self.textEdit_notes = QtWidgets.QTextEdit(parent=self.layoutWidget)
        self.textEdit_notes.setObjectName("textEdit_notes")
        self.gridLayout_4.addWidget(self.textEdit_notes, 1, 0, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout_4)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.scrollArea = QtWidgets.QScrollArea(parent=self.layoutWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 908, 322))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.pushButton_components = QtWidgets.QPushButton(parent=self.scrollAreaWidgetContents)
        self.pushButton_components.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_components.setCheckable(True)
        self.pushButton_components.setObjectName("pushButton_components")
        self.verticalLayout_4.addWidget(self.pushButton_components)
        self.widget_components = QtWidgets.QWidget(parent=self.scrollAreaWidgetContents)
        self.widget_components.setObjectName("widget_components")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.widget_components)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.layout_components = QtWidgets.QVBoxLayout()
        self.layout_components.setObjectName("layout_components")
        self.verticalLayout_5.addLayout(self.layout_components)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(3, 3, 3, 3)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pushButto_add_component = QtWidgets.QPushButton(parent=self.widget_components)
        self.pushButto_add_component.setObjectName("pushButto_add_component")
        self.horizontalLayout_2.addWidget(self.pushButto_add_component)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.verticalLayout_5.addLayout(self.horizontalLayout_2)
        self.verticalLayout_5.setStretch(0, 1)
        self.verticalLayout_4.addWidget(self.widget_components)
        self.verticalLayout_3.addLayout(self.verticalLayout_4)
        self.verticalLayout_6 = QtWidgets.QVBoxLayout()
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.pushButton_sheets = QtWidgets.QPushButton(parent=self.scrollAreaWidgetContents)
        self.pushButton_sheets.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_sheets.setCheckable(True)
        self.pushButton_sheets.setObjectName("pushButton_sheets")
        self.verticalLayout_6.addWidget(self.pushButton_sheets)
        self.widget_sheets = QtWidgets.QWidget(parent=self.scrollAreaWidgetContents)
        self.widget_sheets.setObjectName("widget_sheets")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.widget_sheets)
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.layout_sheets = QtWidgets.QVBoxLayout()
        self.layout_sheets.setObjectName("layout_sheets")
        self.verticalLayout_7.addLayout(self.layout_sheets)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setContentsMargins(3, 3, 3, 3)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.pushButton_add_sheet = QtWidgets.QPushButton(parent=self.widget_sheets)
        self.pushButton_add_sheet.setObjectName("pushButton_add_sheet")
        self.horizontalLayout_4.addWidget(self.pushButton_add_sheet)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.verticalLayout_7.addLayout(self.horizontalLayout_4)
        self.verticalLayout_7.setStretch(0, 1)
        self.verticalLayout_6.addWidget(self.widget_sheets)
        self.verticalLayout_3.addLayout(self.verticalLayout_6)
        self.verticalLayout_8.addLayout(self.verticalLayout_3)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_8.addItem(spacerItem2)
        self.verticalLayout_8.setStretch(1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayoutWidget = QtWidgets.QWidget(parent=self.splitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_9.setContentsMargins(9, 9, 9, 9)
        self.verticalLayout_9.setSpacing(9)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.label_9 = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_6.addWidget(self.label_9)
        self.pushButton_refresh_purchase_orders = QtWidgets.QPushButton(parent=self.verticalLayoutWidget)
        self.pushButton_refresh_purchase_orders.setMaximumSize(QtCore.QSize(35, 35))
        self.pushButton_refresh_purchase_orders.setText("")
        self.pushButton_refresh_purchase_orders.setFlat(True)
        self.pushButton_refresh_purchase_orders.setObjectName("pushButton_refresh_purchase_orders")
        self.horizontalLayout_6.addWidget(self.pushButton_refresh_purchase_orders)
        self.verticalLayout_9.addLayout(self.horizontalLayout_6)
        self.treeWidget_purchase_orders = QtWidgets.QTreeWidget(parent=self.verticalLayoutWidget)
        self.treeWidget_purchase_orders.setObjectName("treeWidget_purchase_orders")
        self.treeWidget_purchase_orders.headerItem().setText(0, "1")
        self.verticalLayout_9.addWidget(self.treeWidget_purchase_orders)
        self.verticalLayout_2.addWidget(self.splitter)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem3)
        self.pushButton_duplicate = QtWidgets.QPushButton(parent=Dialog)
        self.pushButton_duplicate.setObjectName("pushButton_duplicate")
        self.horizontalLayout_3.addWidget(self.pushButton_duplicate)
        self.pushButton_save_and_apply_orders = QtWidgets.QPushButton(parent=Dialog)
        self.pushButton_save_and_apply_orders.setObjectName("pushButton_save_and_apply_orders")
        self.horizontalLayout_3.addWidget(self.pushButton_save_and_apply_orders)
        self.pushButton_apply_orders = QtWidgets.QPushButton(parent=Dialog)
        self.pushButton_apply_orders.setObjectName("pushButton_apply_orders")
        self.horizontalLayout_3.addWidget(self.pushButton_apply_orders)
        self.pushButton_save = QtWidgets.QPushButton(parent=Dialog)
        self.pushButton_save.setObjectName("pushButton_save")
        self.horizontalLayout_3.addWidget(self.pushButton_save)
        self.pushButton_print = QtWidgets.QPushButton(parent=Dialog)
        self.pushButton_print.setObjectName("pushButton_print")
        self.horizontalLayout_3.addWidget(self.pushButton_print)
        self.pushButton_delete = QtWidgets.QPushButton(parent=Dialog)
        self.pushButton_delete.setObjectName("pushButton_delete")
        self.horizontalLayout_3.addWidget(self.pushButton_delete)
        self.pushButton_close = QtWidgets.QPushButton(parent=Dialog)
        self.pushButton_close.setObjectName("pushButton_close")
        self.horizontalLayout_3.addWidget(self.pushButton_close)
        self.verticalLayout_2.addLayout(self.horizontalLayout_3)
        self.verticalLayout_2.setStretch(0, 1)
        self.label.setBuddy(self.doubleSpinBox_po_number)
        self.label_2.setBuddy(self.comboBox_vendor)
        self.label_6.setBuddy(self.dateEdit_expected_arrival)
        self.label_5.setBuddy(self.comboBox_status)
        self.label_7.setBuddy(self.textEdit_notes)

        self.retranslateUi(Dialog)
        self.pushButton_components.clicked['bool'].connect(self.widget_components.setVisible) # type: ignore
        self.pushButton_sheets.clicked['bool'].connect(self.widget_sheets.setVisible) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Edit Purchase Order"))
        self.label.setText(_translate("Dialog", "PO number:"))
        self.label_2.setText(_translate("Dialog", "Vendor:"))
        self.label_3.setText(_translate("Dialog", "Shipping address:"))
        self.label_6.setText(_translate("Dialog", "Expected Arrival:"))
        self.label_5.setText(_translate("Dialog", "Status:"))
        self.pushButton_autofill.setText(_translate("Dialog", "Autofill"))
        self.label_8.setText(_translate("Dialog", "Shipping method:"))
        self.label_7.setText(_translate("Dialog", "Notes:"))
        self.textEdit_notes.setPlaceholderText(_translate("Dialog", "Notes..."))
        self.pushButton_components.setText(_translate("Dialog", "Components"))
        self.pushButto_add_component.setText(_translate("Dialog", "Add Component"))
        self.pushButton_sheets.setText(_translate("Dialog", "Sheets"))
        self.pushButton_add_sheet.setText(_translate("Dialog", "Add Sheet"))
        self.label_9.setText(_translate("Dialog", "Purchase Orders\n"
"Double click to load."))
        self.pushButton_duplicate.setText(_translate("Dialog", "Duplicate && Increase PO Number"))
        self.pushButton_save_and_apply_orders.setText(_translate("Dialog", "Apply Orders && Save"))
        self.pushButton_apply_orders.setText(_translate("Dialog", "Apply Orders"))
        self.pushButton_save.setText(_translate("Dialog", "Save"))
        self.pushButton_print.setText(_translate("Dialog", "Open Printout"))
        self.pushButton_print.setShortcut(_translate("Dialog", "Ctrl+P"))
        self.pushButton_delete.setText(_translate("Dialog", "Delete"))
        self.pushButton_close.setText(_translate("Dialog", "Close"))
