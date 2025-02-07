from utils.inventory.category import Category
from utils.inventory.round_tube import RoundTube
from utils.inventory.structural_profile import ProfilesTypes


class Pipe(RoundTube):
    def __init__(self, data: dict, structural_steel_inventory):
        super().__init__(data, structural_steel_inventory)
        self.PROFILE_TYPE = ProfilesTypes.PIPE
        self.load_data(data)

    def remove_from_category(self, category: Category):
        super().remove_from_category(category)
        if len(self.categories) == 0:
            self.structural_steel_inventory.remove_pipe(self)
