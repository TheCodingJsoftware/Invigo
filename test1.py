from utils.workspace.workspace import Workspace
from utils.workspace.batch import Batch
from utils.workspace.item import Item
from rich import print

# Create a workspace
workspace = Workspace("Admin")


batch1 = Batch("Batch1")
batch2 = Batch("BL 2i9")
workspace.set_batch(batch1)
workspace.set_batch(batch2)

# Create items and add them to the batch
item1 = Item("Bolt")
item2 = Item("Item 2")

# Set values for items
item1.set_data({"quantity": 2, "unit_quantity": 1})
item2.set_data(20)

batch1.set_item(item1)
batch2.set_item(item2)

batch1.rename("TEST ")
item2.rename("I AM NEW NAME")

# Add the batch to the workspace

b: Batch = workspace.copy_batch("TEST ")
b.rename("asdhjfcsdFNlasnfiodsnj")
t: Item = b.get_item("Bolt")
t.rename("ashjiashdnjsiodjasiojd")

workspace.save()
# workspace.save_data()
# print(workspace.get_batch("Batch1").get_item("Item 1").get_value('num'))
