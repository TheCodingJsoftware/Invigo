# Form implementation generated from reading ui file 'C:\Users\Jared\Documents\Code\Python-Projects\Inventory Manager\ui\dialogs\view_assembly_dialog.ui'
#
# Created by: PyQt6 UI code generator 6.7.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1273, 1134)
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
        self.verticalLayout_7 = QtWidgets.QVBoxLayout()
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.label_assembly_image = QtWidgets.QLabel(parent=self.widget)
        self.label_assembly_image.setObjectName("label_assembly_image")
        self.verticalLayout_7.addWidget(self.label_assembly_image)
        self.label_assembly_name = QtWidgets.QLabel(parent=self.widget)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_assembly_name.setFont(font)
        self.label_assembly_name.setObjectName("label_assembly_name")
        self.verticalLayout_7.addWidget(self.label_assembly_name)
        self.verticalLayout.addLayout(self.verticalLayout_7)
        self.files_layout = QtWidgets.QHBoxLayout()
        self.files_layout.setObjectName("files_layout")
        self.verticalLayout.addLayout(self.files_layout)
        self.scrollArea = QtWidgets.QScrollArea(parent=self.widget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1253, 1054))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout_components = QtWidgets.QVBoxLayout()
        self.verticalLayout_components.setSpacing(0)
        self.verticalLayout_components.setObjectName("verticalLayout_components")
        self.pushButton_components = QtWidgets.QPushButton(parent=self.scrollAreaWidgetContents)
        self.pushButton_components.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_components.setCheckable(True)
        self.pushButton_components.setChecked(True)
        self.pushButton_components.setObjectName("pushButton_components")
        self.verticalLayout_components.addWidget(self.pushButton_components)
        self.widget_components = QtWidgets.QWidget(parent=self.scrollAreaWidgetContents)
        self.widget_components.setObjectName("widget_components")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.widget_components)
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout()
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.tableWidget_components = QtWidgets.QTableWidget(parent=self.widget_components)
        self.tableWidget_components.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget_components.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget_components.setObjectName("tableWidget_components")
        self.tableWidget_components.setColumnCount(3)
        self.tableWidget_components.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_components.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_components.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_components.setHorizontalHeaderItem(2, item)
        self.verticalLayout_8.addWidget(self.tableWidget_components)
        self.verticalLayout_9.addLayout(self.verticalLayout_8)
        self.verticalLayout_components.addWidget(self.widget_components)
        self.verticalLayout_2.addLayout(self.verticalLayout_components)
        self.verticalLayout_laser_cut_parts = QtWidgets.QVBoxLayout()
        self.verticalLayout_laser_cut_parts.setSpacing(0)
        self.verticalLayout_laser_cut_parts.setObjectName("verticalLayout_laser_cut_parts")
        self.pushButton_laser_cut_parts = QtWidgets.QPushButton(parent=self.scrollAreaWidgetContents)
        self.pushButton_laser_cut_parts.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.pushButton_laser_cut_parts.setCheckable(True)
        self.pushButton_laser_cut_parts.setChecked(True)
        self.pushButton_laser_cut_parts.setObjectName("pushButton_laser_cut_parts")
        self.verticalLayout_laser_cut_parts.addWidget(self.pushButton_laser_cut_parts)
        self.widget_laser_cut_parts = QtWidgets.QWidget(parent=self.scrollAreaWidgetContents)
        self.widget_laser_cut_parts.setObjectName("widget_laser_cut_parts")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.widget_laser_cut_parts)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.tableWidget_laser_cut_parts = QtWidgets.QTableWidget(parent=self.widget_laser_cut_parts)
        self.tableWidget_laser_cut_parts.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget_laser_cut_parts.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget_laser_cut_parts.setObjectName("tableWidget_laser_cut_parts")
        self.tableWidget_laser_cut_parts.setColumnCount(8)
        self.tableWidget_laser_cut_parts.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_laser_cut_parts.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_laser_cut_parts.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_laser_cut_parts.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_laser_cut_parts.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_laser_cut_parts.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_laser_cut_parts.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_laser_cut_parts.setHorizontalHeaderItem(6, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_laser_cut_parts.setHorizontalHeaderItem(7, item)
        self.verticalLayout_4.addWidget(self.tableWidget_laser_cut_parts)
        self.verticalLayout_5.addLayout(self.verticalLayout_4)
        self.verticalLayout_laser_cut_parts.addWidget(self.widget_laser_cut_parts)
        self.verticalLayout_2.addLayout(self.verticalLayout_laser_cut_parts)
        self.verticalLayout_6.addLayout(self.verticalLayout_2)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_6.addItem(spacerItem)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.verticalLayout_3.addLayout(self.verticalLayout)
        self.horizontalLayout.addWidget(self.widget)

        self.retranslateUi(Form)
        self.pushButton_laser_cut_parts.clicked['bool'].connect(self.widget_laser_cut_parts.setVisible) # type: ignore
        self.pushButton_components.clicked['bool'].connect(self.widget_components.setVisible) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_assembly_image.setText(_translate("Form", "ASSEMBLY_IMAGE"))
        self.label_assembly_name.setText(_translate("Form", "ASSEMBLY_NAME"))
        self.pushButton_components.setText(_translate("Form", "Components"))
        item = self.tableWidget_components.horizontalHeaderItem(0)
        item.setText(_translate("Form", "Image"))
        item = self.tableWidget_components.horizontalHeaderItem(1)
        item.setText(_translate("Form", "Name"))
        item = self.tableWidget_components.horizontalHeaderItem(2)
        item.setText(_translate("Form", "Quantity"))
        self.pushButton_laser_cut_parts.setText(_translate("Form", "Laser Cut Parts"))
        item = self.tableWidget_laser_cut_parts.horizontalHeaderItem(0)
        item.setText(_translate("Form", "Image"))
        item = self.tableWidget_laser_cut_parts.horizontalHeaderItem(1)
        item.setText(_translate("Form", "Name"))
        item = self.tableWidget_laser_cut_parts.horizontalHeaderItem(2)
        item.setText(_translate("Form", "Material"))
        item = self.tableWidget_laser_cut_parts.horizontalHeaderItem(3)
        item.setText(_translate("Form", "Files"))
        item = self.tableWidget_laser_cut_parts.horizontalHeaderItem(4)
        item.setText(_translate("Form", "Quantity"))
        item = self.tableWidget_laser_cut_parts.horizontalHeaderItem(5)
        item.setText(_translate("Form", "Process"))
        item = self.tableWidget_laser_cut_parts.horizontalHeaderItem(6)
        item.setText(_translate("Form", "Recut"))
        item = self.tableWidget_laser_cut_parts.horizontalHeaderItem(7)
        item.setText(_translate("Form", "Recoat"))
