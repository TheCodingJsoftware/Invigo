# Form implementation generated from reading ui file 'c:\Users\Jared\Documents\Code\Python-Projects\Inventory Manager\ui\dialogs\send_jobs_to_workspace_dialog.ui'
#
# Created by: PyQt6 UI code generator 6.7.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1077, 619)
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
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.lblMessage = QtWidgets.QLabel(parent=self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblMessage.sizePolicy().hasHeightForWidth())
        self.lblMessage.setSizePolicy(sizePolicy)
        self.lblMessage.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading | QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        self.lblMessage.setWordWrap(True)
        self.lblMessage.setObjectName("lblMessage")
        self.horizontalLayout_4.addWidget(self.lblMessage)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.groupBox = QtWidgets.QGroupBox(parent=self.widget)
        self.groupBox.setMinimumSize(QtCore.QSize(0, 0))
        self.groupBox.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.groupBox.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.groupBox.setFlat(False)
        self.groupBox.setCheckable(False)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_6.setContentsMargins(3, 3, 3, 3)
        self.verticalLayout_6.setSpacing(3)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.scrollArea_2 = QtWidgets.QScrollArea(parent=self.groupBox)
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollArea_2.setObjectName("scrollArea_2")
        self.scrollAreaWidgetContents_2 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_2.setGeometry(QtCore.QRect(0, 0, 641, 457))
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.jobs_layout = QtWidgets.QVBoxLayout()
        self.jobs_layout.setObjectName("jobs_layout")
        self.verticalLayout_5.addLayout(self.jobs_layout)
        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)
        self.verticalLayout_6.addWidget(self.scrollArea_2)
        self.horizontalLayout_2.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(parent=self.widget)
        self.groupBox_2.setMinimumSize(QtCore.QSize(400, 0))
        self.groupBox_2.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.groupBox_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_7.setContentsMargins(3, 3, 3, 3)
        self.verticalLayout_7.setSpacing(3)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.label = QtWidgets.QLabel(parent=self.groupBox_2)
        font = QtGui.QFont()
        font.setItalic(False)
        self.label.setFont(font)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.verticalLayout_7.addWidget(self.label)
        self.verticalLayout_workorders = QtWidgets.QVBoxLayout()
        self.verticalLayout_workorders.setSpacing(6)
        self.verticalLayout_workorders.setObjectName("verticalLayout_workorders")
        self.verticalLayout_7.addLayout(self.verticalLayout_workorders)
        self.verticalLayout_7.setStretch(1, 1)
        self.horizontalLayout_2.addWidget(self.groupBox_2)
        self.horizontalLayout_2.setStretch(0, 1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.checkBox_update_components = QtWidgets.QCheckBox(parent=self.widget)
        self.checkBox_update_components.setCheckable(True)
        self.checkBox_update_components.setChecked(True)
        self.checkBox_update_components.setObjectName("checkBox_update_components")
        self.horizontalLayout_3.addWidget(self.checkBox_update_components)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.buttonsLayout = QtWidgets.QHBoxLayout()
        self.buttonsLayout.setObjectName("buttonsLayout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.buttonsLayout.addItem(spacerItem1)
        self.pushButton_add = QtWidgets.QPushButton(parent=self.widget)
        self.pushButton_add.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.pushButton_add.setObjectName("pushButton_add")
        self.buttonsLayout.addWidget(self.pushButton_add)
        self.pushButton_cancel = QtWidgets.QPushButton(parent=self.widget)
        self.pushButton_cancel.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.pushButton_cancel.setObjectName("pushButton_cancel")
        self.buttonsLayout.addWidget(self.pushButton_cancel)
        self.verticalLayout.addLayout(self.buttonsLayout)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout_3.addLayout(self.verticalLayout)
        self.horizontalLayout.addWidget(self.widget)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.lblMessage.setText(_translate("Form", "Select jobs and set quantity for selected jobs.\n" "\n" "Press 'Add' when finished."))
        self.groupBox.setTitle(_translate("Form", "Select Jobs"))
        self.groupBox_2.setTitle(_translate("Form", "Quantities"))
        self.label.setText(_translate("Form", "* Will add the job 𝓍 amount of times to workspace."))
        self.checkBox_update_components.setToolTip(_translate("Form", "Will remove components and update components inventory accordingly to what is in the jobs."))
        self.checkBox_update_components.setText(_translate("Form", "Update Components Quantity"))
        self.pushButton_add.setText(_translate("Form", "Send to Production Planner"))
        self.pushButton_cancel.setText(_translate("Form", "Cancel"))