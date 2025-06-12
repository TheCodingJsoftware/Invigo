from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QTreeWidgetItem

from ui.dialogs.add_assembly_dialog_UI import Ui_Form
from ui.icons import Icons
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job


class AddAssemblyDialog(QDialog, Ui_Form):
    def __init__(self, all_jobs: list[Job], parent):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.all_jobs = all_jobs
        self.all_assemblies = self.get_all_assemblies(self.all_jobs)

        self.setWindowTitle("Add Assembly")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.populate_tree_widget()
        self.treeWidget_assemblies.expandAll()

        self.pushButton_add.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

    def get_all_assemblies(self, jobs: list[Job]) -> dict[Assembly, str]:
        assemblies: dict[Assembly, str] = {}
        for job in jobs:
            for assembly in job.get_all_assemblies():
                assemblies.update({assembly: assembly.name})
        return assemblies

    def populate_tree_widget(self):
        self.treeWidget_assemblies.clear()
        for job in self.all_jobs:
            job_item = QTreeWidgetItem([job.name])
            self.treeWidget_assemblies.addTopLevelItem(job_item)
            self.add_assemblies_to_tree(job_item, job.assemblies)

    def add_assemblies_to_tree(
        self, parent_item: QTreeWidgetItem, assemblies: list[Assembly]
    ):
        for assembly in assemblies:
            assembly_item = QTreeWidgetItem([assembly.name])
            parent_item.addChild(assembly_item)
            if assembly.sub_assemblies:
                self.add_assemblies_to_tree(assembly_item, assembly.sub_assemblies)

    def get_selected_assemblies(self) -> list[Assembly]:
        selected_assemblies: list[Assembly] = []
        selected_items = self.treeWidget_assemblies.selectedItems()
        selected_names = [item.text(0) for item in selected_items]

        for assembly, name in self.all_assemblies.items():
            if name in selected_names:
                selected_assemblies.append(assembly)

        return selected_assemblies
