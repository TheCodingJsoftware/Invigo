# Form implementation generated from reading ui file 'C:\Users\Jared\Documents\Code\Python-Projects\Inventory Manager\ui\widgets\workspace_widget.ui'
#
# Created by: PyQt6 UI code generator 6.7.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1075, 804)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout()
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.scrollArea = QtWidgets.QScrollArea(parent=Form)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1071, 800))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_11.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout()
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.workspace_layout = QtWidgets.QHBoxLayout()
        self.workspace_layout.setObjectName("workspace_layout")
        self.parts_widget = QtWidgets.QWidget(parent=self.scrollAreaWidgetContents)
        self.parts_widget.setObjectName("parts_widget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.parts_widget)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.recut_parts_widget = QtWidgets.QGroupBox(parent=self.parts_widget)
        self.recut_parts_widget.setObjectName("recut_parts_widget")
        self.verticalLayout_12 = QtWidgets.QVBoxLayout(self.recut_parts_widget)
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.recut_parts_layout = QtWidgets.QVBoxLayout()
        self.recut_parts_layout.setObjectName("recut_parts_layout")
        self.verticalLayout_12.addLayout(self.recut_parts_layout)
        self.verticalLayout_4.addWidget(self.recut_parts_widget)
        self.recoat_parts_widget = QtWidgets.QGroupBox(parent=self.parts_widget)
        self.recoat_parts_widget.setObjectName("recoat_parts_widget")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.recoat_parts_widget)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.recoat_parts_layout = QtWidgets.QVBoxLayout()
        self.recoat_parts_layout.setObjectName("recoat_parts_layout")
        self.verticalLayout_6.addLayout(self.recoat_parts_layout)
        self.verticalLayout_4.addWidget(self.recoat_parts_widget)
        self.parts_layout = QtWidgets.QVBoxLayout()
        self.parts_layout.setObjectName("parts_layout")
        self.verticalLayout_4.addLayout(self.parts_layout)
        self.verticalLayout_4.setStretch(2, 1)
        self.verticalLayout_2.addLayout(self.verticalLayout_4)
        self.workspace_layout.addWidget(self.parts_widget)
        self.assembly_widget = QtWidgets.QWidget(parent=self.scrollAreaWidgetContents)
        self.assembly_widget.setObjectName("assembly_widget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.assembly_widget)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout()
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.assembly_layout = QtWidgets.QVBoxLayout()
        self.assembly_layout.setObjectName("assembly_layout")
        self.verticalLayout_9.addLayout(self.assembly_layout)
        self.verticalLayout_3.addLayout(self.verticalLayout_9)
        self.workspace_layout.addWidget(self.assembly_widget)
        self.verticalLayout_10.addLayout(self.workspace_layout)
        self.verticalLayout_11.addLayout(self.verticalLayout_10)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_7.addWidget(self.scrollArea)
        self.verticalLayout.addLayout(self.verticalLayout_7)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.recut_parts_widget.setTitle(_translate("Form", "Recut Parts"))
        self.recoat_parts_widget.setTitle(_translate("Form", "Recoat Parts"))
