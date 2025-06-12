

from ui.dialogs.add_new_structural_steel_item_dialog import AddStructuralSteelItemDialog


class EditStructuralSteelItemDialog(AddStructuralSteelItemDialog):
    def __init__(self, category, structural_steel_inventory, structural_steel_settings, workspace_settings, structural_steel_item, parent=None):
        super().__init__(category, structural_steel_inventory, structural_steel_settings, workspace_settings, structural_steel_item, parent)
        self.setWindowTitle("Edit structural steel item")
        self.lblMessage.setText(f"Editing {self.structural_steel_item.get_name()} {self.structural_steel_item.part_number}")
        self.pushButton_add.setText("Save")
