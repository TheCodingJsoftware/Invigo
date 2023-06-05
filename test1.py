from utils.workspace.workspace import Workspace
from utils.workspace.assembly import Assembly
from utils.workspace.item import Item
from rich import print

# Create a workspace
workspace = Workspace("Admin")
# a = Assembly(name="Assembly 1")
# a.set_item(Item(name='Item 1', data={"quanitty": 3}))
# a.set_item(Item(name='Item 2', data={"quanitty": 3}))
# workspace.set_assembly(a)
a = workspace.get_assembly("Assembly 1")

sa = a.get_sub_assembly("Copy 1 - (Copy)")

ssa = sa.get_sub_assembly("Copy 1 - (Copy)")

new: Assembly = Assembly(name="TEST")
new.set_assembly_data("quantity", 999)
new.set_item(Item(name="NUTS AND BOLDS", data={"quantity": -1}))

ssa.set_sub_assembly(new)


workspace.save()
