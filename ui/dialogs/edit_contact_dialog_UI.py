# Form implementation generated from reading ui file '/mnt/SafeHaven/Forge/Inventory Manager/ui/dialogs/edit_contact_dialog.ui'
#
# Created by: PyQt6 UI code generator 6.9.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(359, 292)
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
        self.label_4 = QtWidgets.QLabel(parent=self.widget)
        self.label_4.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.label_4.setWordWrap(True)
        self.label_4.setOpenExternalLinks(True)
        self.label_4.setObjectName("label_4")
        self.verticalLayout.addWidget(self.label_4)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.lineEdit_email = QtWidgets.QLineEdit(parent=self.widget)
        self.lineEdit_email.setObjectName("lineEdit_email")
        self.gridLayout.addWidget(self.lineEdit_email, 2, 3, 1, 1)
        self.label_2 = QtWidgets.QLabel(parent=self.widget)
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.label_7 = QtWidgets.QLabel(parent=self.widget)
        self.label_7.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 2, 0, 1, 1)
        self.lineEdit_name = QtWidgets.QLineEdit(parent=self.widget)
        self.lineEdit_name.setObjectName("lineEdit_name")
        self.gridLayout.addWidget(self.lineEdit_name, 0, 3, 1, 1)
        self.label = QtWidgets.QLabel(parent=self.widget)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.lineEdit_phone = QtWidgets.QLineEdit(parent=self.widget)
        self.lineEdit_phone.setObjectName("lineEdit_phone")
        self.gridLayout.addWidget(self.lineEdit_phone, 1, 3, 1, 1)
        self.label_3 = QtWidgets.QLabel(parent=self.widget)
        self.label_3.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)
        self.lineEdit_password = QtWidgets.QLineEdit(parent=self.widget)
        self.lineEdit_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.lineEdit_password.setObjectName("lineEdit_password")
        self.gridLayout.addWidget(self.lineEdit_password, 3, 3, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.buttonsLayout = QtWidgets.QHBoxLayout()
        self.buttonsLayout.setObjectName("buttonsLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.buttonsLayout.addItem(spacerItem)
        self.pushButton_save = QtWidgets.QPushButton(parent=self.widget)
        self.pushButton_save.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.pushButton_save.setObjectName("pushButton_save")
        self.buttonsLayout.addWidget(self.pushButton_save)
        self.pushButton_cancel = QtWidgets.QPushButton(parent=self.widget)
        self.pushButton_cancel.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.pushButton_cancel.setObjectName("pushButton_cancel")
        self.buttonsLayout.addWidget(self.pushButton_cancel)
        self.verticalLayout.addLayout(self.buttonsLayout)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout_3.addLayout(self.verticalLayout)
        self.horizontalLayout.addWidget(self.widget)
        self.label_2.setBuddy(self.lineEdit_phone)
        self.label_7.setBuddy(self.lineEdit_email)
        self.label.setBuddy(self.lineEdit_name)
        self.label_3.setBuddy(self.lineEdit_password)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.lineEdit_name, self.lineEdit_phone)
        Form.setTabOrder(self.lineEdit_phone, self.lineEdit_email)
        Form.setTabOrder(self.lineEdit_email, self.pushButton_save)
        Form.setTabOrder(self.pushButton_save, self.pushButton_cancel)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_4.setText(_translate("Form", "<html><head/><body><p><span style=\" font-weight:700;\">Your Email and Password are used only to send Purchase Orders through </span><a href=\"http://invi.go\"><span style=\" text-decoration: underline; color:#bdc5e4;\">invi.go</span></a><span style=\" font-weight:700;\">.<br/></span><br/>They are securely encrypted and used exclusively when sending Purchase Orders from the print view.</p></body></html>"))
        self.lineEdit_email.setPlaceholderText(_translate("Form", "Email..."))
        self.label_2.setText(_translate("Form", "Phone:"))
        self.label_7.setText(_translate("Form", "Email:"))
        self.lineEdit_name.setPlaceholderText(_translate("Form", "Name..."))
        self.label.setText(_translate("Form", "Name:"))
        self.lineEdit_phone.setPlaceholderText(_translate("Form", "Phone number..."))
        self.label_3.setText(_translate("Form", "Password:"))
        self.lineEdit_password.setPlaceholderText(_translate("Form", "Password..."))
        self.pushButton_save.setText(_translate("Form", "Save"))
        self.pushButton_cancel.setText(_translate("Form", "Cancel"))
