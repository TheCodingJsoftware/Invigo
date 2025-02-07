from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from ui.dialogs.add_new_structural_steel_item_dialog_UI import Ui_Form
from ui.icons import Icons
from utils.inventory.category import Category
from utils.inventory.structural_profile import ProfilesTypes, StructuralProfile
from utils.inventory.round_bar import RoundBar
from utils.inventory.round_tube import RoundTube
from utils.inventory.rectangular_bar import RectangularBar
from utils.inventory.rectangular_tube import RectangularTube
from utils.inventory.angle_bar import AngleBar
from utils.inventory.flat_bar import FlatBar
from utils.inventory.pipe import Pipe
from utils.inventory.dom_round_tube import DOMRoundTube
from utils.inventory.structural_steel_inventory import StructuralSteelInventory
from utils.structural_steel_settings.structural_steel_settings import StructuralSteelSettings
from utils.workspace.workspace_settings import WorkspaceSettings


class AddStructuralSteelItemDialog(QDialog, Ui_Form):
    def __init__(
        self,
        category: Category,
        structural_steel_inventory: StructuralSteelInventory,
        structural_steel_settings: StructuralSteelSettings,
        workspace_settings: WorkspaceSettings,
        structural_steel_item: RoundBar | RectangularBar | AngleBar | RectangularTube | RoundTube | DOMRoundTube | Pipe | FlatBar | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.category = category
        self.structural_steel_inventory = structural_steel_inventory
        self.structural_steel_settings = structural_steel_settings
        self.workspace_settings = workspace_settings
        self.structural_steel_item = structural_steel_item

        self.profile = ProfilesTypes.RECTANGULAR_BAR

        if self.structural_steel_item:
            self.profile = self.structural_steel_item.PROFILE_TYPE

        self.setWindowTitle("Add structural steel item")
        self.lblMessage.setText("Add a new item to the inventory.")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.load_ui()

    def load_ui(self):
        self.pushButton_add.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

        self.comboBox_categories.addItems(
            [category.name for category in self.structural_steel_inventory.get_categories()]
        )
        if self.category:
            self.comboBox_categories.setCurrentText(self.category.name)

        self.comboBox_material.addItems(self.structural_steel_settings.get_materials())
        for profile in ProfilesTypes:
            self.comboBox_profile.addItem(profile.value, profile)
        self.comboBox_profile.setCurrentText(self.profile.value)

        if self.structural_steel_item:
            self.load_values_from_item()

        self.comboBox_material.currentTextChanged.connect(self.update_name)
        self.comboBox_profile.currentTextChanged.connect(self.profile_changed)

        self.doubleSpinBox_outside_diameter.valueChanged.connect(self.diameter_changed)
        self.doubleSpinBox_inside_diameter.valueChanged.connect(self.diameter_changed)
        self.doubleSpinBox_wall_thickness.valueChanged.connect(self.wall_thickness_changed)

        self.doubleSpinBox_leg_a_length.valueChanged.connect(self.update_name)
        self.doubleSpinBox_leg_b_length.valueChanged.connect(self.update_name)
        self.doubleSpinBox_length.valueChanged.connect(self.update_name)
        self.doubleSpinBox_outside_height.valueChanged.connect(self.update_name)
        self.doubleSpinBox_outside_width.valueChanged.connect(self.update_name)

        self.update_profile_widgets()
        self.update_name()

    def diameter_changed(self):
        if self.profile in [ProfilesTypes.ROUND_BAR]:
            return
        self.doubleSpinBox_wall_thickness.blockSignals(True)
        self.doubleSpinBox_wall_thickness.setValue(self.doubleSpinBox_outside_diameter.value() - self.doubleSpinBox_inside_diameter.value())
        self.doubleSpinBox_wall_thickness.blockSignals(False)
        self.update_name()

    def wall_thickness_changed(self):
        if self.profile in [ProfilesTypes.ROUND_BAR]:
            return
        self.doubleSpinBox_outside_diameter.blockSignals(True)
        self.doubleSpinBox_outside_diameter.setValue(self.doubleSpinBox_wall_thickness.value() + self.doubleSpinBox_inside_diameter.value())
        self.doubleSpinBox_outside_diameter.blockSignals(False)
        self.update_name()

    def profile_changed(self):
        self.profile = ProfilesTypes(self.comboBox_profile.currentData())
        self.update_profile_widgets()
        self.update_name()

    def load_values_from_item(self):
        self.comboBox_profile.setCurrentText(self.structural_steel_item.PROFILE_TYPE.value)
        self.comboBox_material.setCurrentText(self.structural_steel_item.material)
        self.lineEdit_part_number.setText(self.structural_steel_item.part_number)
        self.doubleSpinBox_length.setValue(self.structural_steel_item.length)
        self.doubleSpinBox_wall_thickness.setValue(self.structural_steel_item.wall_thickness)
        self.comboBox_categories.setCurrentText(self.category.name)
        self.plainTextEdit_notes.setPlainText(self.structural_steel_item.notes)
        self.spinBox_current_quantity.setValue(self.structural_steel_item.quantity)

        if self.profile == ProfilesTypes.RECTANGULAR_BAR:
            self.doubleSpinBox_outside_width.setValue(self.structural_steel_item.width)
            self.doubleSpinBox_outside_height.setValue(self.structural_steel_item.height)
        elif self.profile == ProfilesTypes.ROUND_BAR:
            self.doubleSpinBox_outside_diameter.setValue(self.structural_steel_item.outside_diameter)
            self.doubleSpinBox_inside_diameter.setValue(self.structural_steel_item.inside_diameter)
        elif self.profile == ProfilesTypes.FLAT_BAR:
            self.doubleSpinBox_outside_height.setValue(self.structural_steel_item.width)
            self.doubleSpinBox_outside_width.setValue(self.structural_steel_item.height)
        elif self.profile == ProfilesTypes.ANGLE_BAR:
            self.doubleSpinBox_leg_a_length.setValue(self.structural_steel_item.leg_a)
            self.doubleSpinBox_leg_b_length.setValue(self.structural_steel_item.leg_b)
        elif self.profile == ProfilesTypes.RECTANGULAR_TUBE:
            self.doubleSpinBox_outside_width.setValue(self.structural_steel_item.outer_width)
            self.doubleSpinBox_outside_height.setValue(self.structural_steel_item.outer_height)
        elif self.profile == ProfilesTypes.ROUND_TUBE:
            self.doubleSpinBox_outside_diameter.setValue(self.structural_steel_item.outside_diameter)
            self.doubleSpinBox_inside_diameter.setValue(self.structural_steel_item.inside_diameter)
        elif self.profile == ProfilesTypes.DOM_ROUND_TUBE:
            self.doubleSpinBox_outside_diameter.setValue(self.structural_steel_item.outside_diameter)
            self.doubleSpinBox_inside_diameter.setValue(self.structural_steel_item.inside_diameter)
        elif self.profile == ProfilesTypes.PIPE:
            self.doubleSpinBox_outside_diameter.setValue(self.structural_steel_item.outside_diameter)
            self.doubleSpinBox_inside_diameter.setValue(self.structural_steel_item.inside_diameter)

    def update_profile_widgets(self):
        if self.profile == ProfilesTypes.RECTANGULAR_BAR:
            self.inside_outside_widget.setHidden(True)
            self.height_width_outer_widget.setHidden(False)
            self.leg_widget.setHidden(True)

            self.doubleSpinBox_wall_thickness.setEnabled(True)
        elif self.profile == ProfilesTypes.ROUND_BAR:
            self.inside_outside_widget.setHidden(False)
            self.height_width_outer_widget.setHidden(True)
            self.leg_widget.setHidden(True)

            self.doubleSpinBox_inside_diameter.setEnabled(False)
            self.doubleSpinBox_inside_diameter.setValue(0)
            self.doubleSpinBox_wall_thickness.setEnabled(False)
            self.doubleSpinBox_wall_thickness.setValue(0)
        elif self.profile == ProfilesTypes.FLAT_BAR:
            self.inside_outside_widget.setHidden(True)
            self.height_width_outer_widget.setHidden(False)
            self.leg_widget.setHidden(True)

            self.doubleSpinBox_wall_thickness.setEnabled(True)
        elif self.profile == ProfilesTypes.ANGLE_BAR:
            self.inside_outside_widget.setHidden(True)
            self.height_width_outer_widget.setHidden(True)
            self.leg_widget.setHidden(False)

            self.doubleSpinBox_wall_thickness.setEnabled(True)
        elif self.profile == ProfilesTypes.RECTANGULAR_TUBE:
            self.inside_outside_widget.setHidden(True)
            self.height_width_outer_widget.setHidden(False)
            self.leg_widget.setHidden(True)

            self.doubleSpinBox_wall_thickness.setEnabled(True)
        elif self.profile == ProfilesTypes.ROUND_TUBE:
            self.inside_outside_widget.setHidden(False)
            self.height_width_outer_widget.setHidden(True)
            self.leg_widget.setHidden(True)

            self.doubleSpinBox_inside_diameter.setEnabled(True)
            self.doubleSpinBox_wall_thickness.setEnabled(True)
        elif self.profile == ProfilesTypes.DOM_ROUND_TUBE:
            self.inside_outside_widget.setHidden(False)
            self.height_width_outer_widget.setHidden(True)
            self.leg_widget.setHidden(True)

            self.doubleSpinBox_inside_diameter.setEnabled(True)
            self.doubleSpinBox_wall_thickness.setEnabled(True)
        elif self.profile == ProfilesTypes.PIPE:
            self.inside_outside_widget.setHidden(False)
            self.height_width_outer_widget.setHidden(True)
            self.leg_widget.setHidden(True)

            self.doubleSpinBox_inside_diameter.setEnabled(True)
            self.doubleSpinBox_wall_thickness.setEnabled(True)

    def update_name(self):
        self.lineEdit_name.setText(self.get_item().get_name())

    def get_item(self):
        if self.profile == ProfilesTypes.RECTANGULAR_BAR:
            item = RectangularBar(
                {
                    "width": self.doubleSpinBox_outside_width.value(),
                    "height": self.doubleSpinBox_outside_height.value(),
                },
                self.structural_steel_inventory,
            )
        elif self.profile == ProfilesTypes.ROUND_BAR:
            item = RoundBar(
                {
                    "outside_diameter": self.doubleSpinBox_outside_diameter.value(),
                },
                self.structural_steel_inventory,
            )
        elif self.profile == ProfilesTypes.FLAT_BAR:
            item = FlatBar(
                {
                    "width": self.doubleSpinBox_outside_width.value(),
                },
                self.structural_steel_inventory,
            )
        elif self.profile == ProfilesTypes.ANGLE_BAR:
            item = AngleBar(
                {
                    "leg_a": self.doubleSpinBox_leg_a_length.value(),
                    "leg_b": self.doubleSpinBox_leg_b_length.value(),
                },
                self.structural_steel_inventory,
            )
        elif self.profile == ProfilesTypes.RECTANGULAR_TUBE:
            item = RectangularTube(
                {
                    "outer_width": self.doubleSpinBox_outside_width.value(),
                    "outer_height": self.doubleSpinBox_outside_height.value(),
                },
                self.structural_steel_inventory,
            )
        elif self.profile == ProfilesTypes.ROUND_TUBE:
            item = RoundTube(
                {
                    "outside_diameter": self.doubleSpinBox_outside_diameter.value(),
                    "inside_diameter": self.doubleSpinBox_inside_diameter.value(),
                },
                self.structural_steel_inventory,
            )
        elif self.profile == ProfilesTypes.DOM_ROUND_TUBE:
            item = DOMRoundTube(
                {
                    "outside_diameter": self.doubleSpinBox_outside_diameter.value(),
                    "inside_diameter": self.doubleSpinBox_inside_diameter.value(),
                },
                self.structural_steel_inventory,
            )
        elif self.profile == ProfilesTypes.PIPE:
            item = Pipe(
                {
                    "outside_diameter": self.doubleSpinBox_outside_diameter.value(),
                    "inside_diameter": self.doubleSpinBox_inside_diameter.value(),
                },
                self.structural_steel_inventory,
            )
        else:
            return None

        item.part_number = self.lineEdit_part_number.text()
        item.material = self.comboBox_material.currentText()
        item.notes = self.plainTextEdit_notes.toPlainText()
        item.quantity = self.spinBox_current_quantity.value()
        item.length = self.doubleSpinBox_length.value()
        item.wall_thickness = self.doubleSpinBox_wall_thickness.value()
        item.add_to_category(self.structural_steel_inventory.get_category(self.comboBox_categories.currentText()))

        return item


