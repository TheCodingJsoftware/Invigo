# Form implementation generated from reading ui file '/mnt/SafeHaven/Forge/Inventory Manager/ui/dialogs/edit_workspace_settings.ui'
#
# Created by: PyQt6 UI code generator 6.9.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        Form.resize(1251, 808)
        Form.setSizeGripEnabled(True)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget = QtWidgets.QWidget(parent=Form)
        self.widget.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.ActionsContextMenu)
        self.widget.setAutoFillBackground(False)
        self.widget.setStyleSheet("")
        self.widget.setObjectName("widget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.splitter = QtWidgets.QSplitter(parent=self.widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.splitter.setObjectName("splitter")
        self.verticalLayoutWidget = QtWidgets.QWidget(parent=self.splitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 9)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_2 = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_3.addWidget(self.label_2)
        self.textEdit_notes = QtWidgets.QTextEdit(parent=self.verticalLayoutWidget)
        self.textEdit_notes.setObjectName("textEdit_notes")
        self.verticalLayout_3.addWidget(self.textEdit_notes)
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(parent=self.splitter)
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.tabWidget = QtWidgets.QTabWidget(parent=self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.tab_3)
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.verticalLayout_18 = QtWidgets.QVBoxLayout()
        self.verticalLayout_18.setObjectName("verticalLayout_18")
        self.scrollArea_2 = QtWidgets.QScrollArea(parent=self.tab_3)
        self.scrollArea_2.setMinimumSize(QtCore.QSize(0, 0))
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollArea_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter|QtCore.Qt.AlignmentFlag.AlignTop)
        self.scrollArea_2.setObjectName("scrollArea_2")
        self.scrollAreaWidgetContents_2 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_2.setGeometry(QtCore.QRect(0, 0, 1209, 20))
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.assemblies_flow_tag_layout = QtWidgets.QVBoxLayout()
        self.assemblies_flow_tag_layout.setObjectName("assemblies_flow_tag_layout")
        spacerItem = QtWidgets.QSpacerItem(20, 500, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.assemblies_flow_tag_layout.addItem(spacerItem)
        self.verticalLayout_5.addLayout(self.assemblies_flow_tag_layout)
        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)
        self.verticalLayout_18.addWidget(self.scrollArea_2)
        self.verticalLayout_6.addLayout(self.verticalLayout_18)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.pushButton_create_new_assembly_group = QtWidgets.QPushButton(parent=self.tab_3)
        self.pushButton_create_new_assembly_group.setMinimumSize(QtCore.QSize(0, 0))
        self.pushButton_create_new_assembly_group.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.pushButton_create_new_assembly_group.setObjectName("pushButton_create_new_assembly_group")
        self.horizontalLayout_5.addWidget(self.pushButton_create_new_assembly_group)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem1)
        self.verticalLayout_6.addLayout(self.horizontalLayout_5)
        self.tabWidget.addTab(self.tab_3, "")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.tab)
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout()
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.scrollArea = QtWidgets.QScrollArea(parent=self.tab)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1209, 20))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_13 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_13.setObjectName("verticalLayout_13")
        self.laser_cut_parts_flow_tag_layout = QtWidgets.QVBoxLayout()
        self.laser_cut_parts_flow_tag_layout.setObjectName("laser_cut_parts_flow_tag_layout")
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.laser_cut_parts_flow_tag_layout.addItem(spacerItem2)
        self.verticalLayout_13.addLayout(self.laser_cut_parts_flow_tag_layout)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_11.addWidget(self.scrollArea)
        self.verticalLayout_8.addLayout(self.verticalLayout_11)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.pushButton_create_new_laser_cut_part_group = QtWidgets.QPushButton(parent=self.tab)
        self.pushButton_create_new_laser_cut_part_group.setObjectName("pushButton_create_new_laser_cut_part_group")
        self.horizontalLayout_7.addWidget(self.pushButton_create_new_laser_cut_part_group)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_7.addItem(spacerItem3)
        self.verticalLayout_8.addLayout(self.horizontalLayout_7)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.tab_2)
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.verticalLayout_15 = QtWidgets.QVBoxLayout()
        self.verticalLayout_15.setObjectName("verticalLayout_15")
        self.scrollArea_3 = QtWidgets.QScrollArea(parent=self.tab_2)
        self.scrollArea_3.setWidgetResizable(True)
        self.scrollArea_3.setObjectName("scrollArea_3")
        self.scrollAreaWidgetContents_3 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_3.setGeometry(QtCore.QRect(0, 0, 1209, 20))
        self.scrollAreaWidgetContents_3.setObjectName("scrollAreaWidgetContents_3")
        self.verticalLayout_17 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_3)
        self.verticalLayout_17.setObjectName("verticalLayout_17")
        self.components_flow_tag_layout = QtWidgets.QVBoxLayout()
        self.components_flow_tag_layout.setObjectName("components_flow_tag_layout")
        spacerItem4 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.components_flow_tag_layout.addItem(spacerItem4)
        self.verticalLayout_17.addLayout(self.components_flow_tag_layout)
        self.scrollArea_3.setWidget(self.scrollAreaWidgetContents_3)
        self.verticalLayout_15.addWidget(self.scrollArea_3)
        self.verticalLayout_7.addLayout(self.verticalLayout_15)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.pushButton_create_new_components_group = QtWidgets.QPushButton(parent=self.tab_2)
        self.pushButton_create_new_components_group.setObjectName("pushButton_create_new_components_group")
        self.horizontalLayout_8.addWidget(self.pushButton_create_new_components_group)
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_8.addItem(spacerItem5)
        self.verticalLayout_7.addLayout(self.horizontalLayout_8)
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout_4.addWidget(self.tabWidget)
        self.groupBox_2 = QtWidgets.QGroupBox(parent=self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_2.sizePolicy().hasHeightForWidth())
        self.groupBox_2.setSizePolicy(sizePolicy)
        self.groupBox_2.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.groupBox_2.setObjectName("groupBox_2")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.groupBox_2)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.groupBox_3 = QtWidgets.QGroupBox(parent=self.groupBox_2)
        self.groupBox_3.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_12 = QtWidgets.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.label = QtWidgets.QLabel(parent=self.groupBox_3)
        self.label.setObjectName("label")
        self.verticalLayout_12.addWidget(self.label)
        self.listWidget_select_tag = QtWidgets.QListWidget(parent=self.groupBox_3)
        self.listWidget_select_tag.setLayoutMode(QtWidgets.QListView.LayoutMode.SinglePass)
        self.listWidget_select_tag.setObjectName("listWidget_select_tag")
        self.verticalLayout_12.addWidget(self.listWidget_select_tag)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_add_tag = QtWidgets.QPushButton(parent=self.groupBox_3)
        self.pushButton_add_tag.setAutoDefault(False)
        self.pushButton_add_tag.setFlat(True)
        self.pushButton_add_tag.setObjectName("pushButton_add_tag")
        self.horizontalLayout.addWidget(self.pushButton_add_tag)
        self.pushButton_delete_tag = QtWidgets.QPushButton(parent=self.groupBox_3)
        self.pushButton_delete_tag.setAutoDefault(False)
        self.pushButton_delete_tag.setFlat(True)
        self.pushButton_delete_tag.setObjectName("pushButton_delete_tag")
        self.horizontalLayout.addWidget(self.pushButton_delete_tag)
        self.verticalLayout_12.addLayout(self.horizontalLayout)
        self.horizontalLayout_2.addWidget(self.groupBox_3)
        self.groupBox_4 = QtWidgets.QGroupBox(parent=self.groupBox_2)
        self.groupBox_4.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.groupBox_4)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.tableWidget_statuses = QtWidgets.QTableWidget(parent=self.groupBox_4)
        self.tableWidget_statuses.setGridStyle(QtCore.Qt.PenStyle.NoPen)
        self.tableWidget_statuses.setObjectName("tableWidget_statuses")
        self.tableWidget_statuses.setColumnCount(4)
        self.tableWidget_statuses.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_statuses.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_statuses.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_statuses.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget_statuses.setHorizontalHeaderItem(3, item)
        self.verticalLayout_9.addWidget(self.tableWidget_statuses)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.pushButton_add_status = QtWidgets.QPushButton(parent=self.groupBox_4)
        self.pushButton_add_status.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.pushButton_add_status.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.pushButton_add_status.setAutoDefault(False)
        self.pushButton_add_status.setDefault(True)
        self.pushButton_add_status.setFlat(False)
        self.pushButton_add_status.setObjectName("pushButton_add_status")
        self.horizontalLayout_6.addWidget(self.pushButton_add_status)
        spacerItem6 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem6)
        self.verticalLayout_9.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_2.addWidget(self.groupBox_4)
        self.groupBox_5 = QtWidgets.QGroupBox(parent=self.groupBox_2)
        self.groupBox_5.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.groupBox_5.setObjectName("groupBox_5")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.groupBox_5)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_4 = QtWidgets.QLabel(parent=self.groupBox_5)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_9.addWidget(self.label_4)
        self.verticalLayout_expected_time_to_complete = QtWidgets.QVBoxLayout()
        self.verticalLayout_expected_time_to_complete.setObjectName("verticalLayout_expected_time_to_complete")
        self.horizontalLayout_9.addLayout(self.verticalLayout_expected_time_to_complete)
        self.horizontalLayout_9.setStretch(1, 1)
        self.verticalLayout_10.addLayout(self.horizontalLayout_9)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label_3 = QtWidgets.QLabel(parent=self.groupBox_5)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)
        self.plainTextEdit_next_flow_tag_message = QtWidgets.QPlainTextEdit(parent=self.groupBox_5)
        self.plainTextEdit_next_flow_tag_message.setObjectName("plainTextEdit_next_flow_tag_message")
        self.gridLayout.addWidget(self.plainTextEdit_next_flow_tag_message, 2, 0, 1, 1)
        self.verticalLayout_10.addLayout(self.gridLayout)
        self.horizontalLayout_2.addWidget(self.groupBox_5)
        self.horizontalLayout_2.setStretch(1, 2)
        self.horizontalLayout_2.setStretch(2, 1)
        self.horizontalLayout_3.addLayout(self.horizontalLayout_2)
        self.verticalLayout_2.addWidget(self.splitter)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        spacerItem7 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem7)
        self.pushButton_save = QtWidgets.QPushButton(parent=self.widget)
        self.pushButton_save.setAutoDefault(False)
        self.pushButton_save.setDefault(True)
        self.pushButton_save.setObjectName("pushButton_save")
        self.horizontalLayout_4.addWidget(self.pushButton_save)
        self.pushButton_save_and_close = QtWidgets.QPushButton(parent=self.widget)
        self.pushButton_save_and_close.setAutoDefault(False)
        self.pushButton_save_and_close.setDefault(True)
        self.pushButton_save_and_close.setObjectName("pushButton_save_and_close")
        self.horizontalLayout_4.addWidget(self.pushButton_save_and_close)
        self.pushButton_cancel = QtWidgets.QPushButton(parent=self.widget)
        self.pushButton_cancel.setAutoDefault(False)
        self.pushButton_cancel.setDefault(True)
        self.pushButton_cancel.setObjectName("pushButton_cancel")
        self.horizontalLayout_4.addWidget(self.pushButton_cancel)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.verticalLayout.addWidget(self.widget)

        self.retranslateUi(Form)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_2.setText(_translate("Form", "Notes:"))
        self.textEdit_notes.setHtml(_translate("Form", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:\'Segoe UI\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt;\">Create and edit flow tags, set attributes and statuses.</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'MS Shell Dlg 2\'; font-size:8.25pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt;\">If a tag box is left as \'None\' it will not be part of the flow.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt;\">&quot;Starts Timer&quot; starts the timer if the flow tag has a timer enabled, timers will be stop automatically when flow tag is changed.</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt;\">Tags such as, &quot;Staging&quot;, &quot;Editing&quot;, and &quot;Planning&quot; cannot be used as flow tags, nothing will be checked if you use them, it could break everything, so, don\'t use them.</span></p></body></html>"))
        self.pushButton_create_new_assembly_group.setText(_translate("Form", "Create New Group"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("Form", "Assembly Flow Tags"))
        self.pushButton_create_new_laser_cut_part_group.setText(_translate("Form", "Create New Group"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("Form", "Laser Cut Part Flow Tags"))
        self.pushButton_create_new_components_group.setText(_translate("Form", "Create New Group"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("Form", "Component Flow Tags"))
        self.groupBox_2.setTitle(_translate("Form", "Edit Tags"))
        self.groupBox_3.setTitle(_translate("Form", "Select Tag"))
        self.label.setText(_translate("Form", "Double-click to rename"))
        self.pushButton_add_tag.setText(_translate("Form", "Add Tag"))
        self.pushButton_delete_tag.setText(_translate("Form", "Delete Tag"))
        self.groupBox_4.setTitle(_translate("Form", "Statuses"))
        item = self.tableWidget_statuses.horizontalHeaderItem(0)
        item.setText(_translate("Form", "Name"))
        item = self.tableWidget_statuses.horizontalHeaderItem(1)
        item.setText(_translate("Form", "Moves Tag Forward"))
        item = self.tableWidget_statuses.horizontalHeaderItem(2)
        item.setText(_translate("Form", "Starts Timer"))
        item = self.tableWidget_statuses.horizontalHeaderItem(3)
        item.setText(_translate("Form", "DEL"))
        self.pushButton_add_status.setText(_translate("Form", "Add New Status"))
        self.groupBox_5.setTitle(_translate("Form", "Attributes"))
        self.label_4.setText(_translate("Form", "Default Exp. Dur.:"))
        self.label_3.setText(_translate("Form", "Next flow tag message:"))
        self.plainTextEdit_next_flow_tag_message.setToolTip(_translate("Form", "This message will show when it is the next tag in the flow tag."))
        self.pushButton_save.setText(_translate("Form", "Save"))
        self.pushButton_save_and_close.setText(_translate("Form", "Save and Close"))
        self.pushButton_cancel.setText(_translate("Form", "Cancel"))
