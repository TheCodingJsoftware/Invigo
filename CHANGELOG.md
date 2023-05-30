# v2.0.0 The **BIG** rewrite and *mini* reset

- This update focuses on overhauling and rewriting the main functionality, that is, loading and multiple client compatablity. This brings a more intuitive and responsive feel to the software.
- Program got its own name and new logo, behold, **Invigo** (*Invi-go*)

## Loading System: rewrite

- New loading system inplace for optimal performance and effeciency. It is rewritten.
  - Everything is now using a table loading approach which is super fast and alot easier to use and manage
- A new Loading Menu has been made with the goal to match the new icon and to make it feel professional and responsive.

## New Menu: Quote Generator

- Generate Quotes/Packing Slips/Workorders with the press of a button
- You can load nests or using existing parts in inventory to create quotes, etc.
- It brings all functionality and much more from the original Laser Quote Generator project into Invigo with a more intuitive user interface.

## Update GUI

- A new update GUI has been made with a new loading animation and now showing download progress

## Bugs

- Bugs were fixed, and even more were added

## Server: Overhaul and rewrite

- New server backend written in Tornado which brings high responsiveness and speed
- Changes are always being synched and sent to all connected clients at all times
- Update inventory requires a mini reset for Parts in Inventory tab as there were too many data leaks
- This new server provides high speed communication and is capable of handling multiple clients through asynchronous programming.

# v1.6.2

- Color changes
- Fixed bug in inventroy updater for server
- Added send sheet report button

# v1.6.1

- Color changes
- Bug fixes and improvements
- Server changes
- Added order pending button for sheets

# v1.6.0

- Added an option on right-click to set a custom limit where red or yellow colors will be shown based on this limits
- Code improvements, and bugs.
- New material based dark theme.
- Main Inventory tab.
  - Way faster loading times.
  - Removed groups.
  - Changed colors.
  - If single item quantities are removed the item that was selected will remain in focus.
- Parts in Inventory tab
  - Parts are automatically put into groups based on thickness.
  - Checkboxes now work as intended.
  - Remove quantities based on which items have been checkmarked.

# v1.5.0

- Improved auto saving to cloud.
- Server is reliable and quicker.
- Added Price of Sheets menu and Parts in Inventory.
- Program works together with Laser Quote Generator with adding parts to inventory.
- Changes to tabs instead of stacked widgets.
- Alot of stuff and functionality has been added.
- Maybe some bug fixes? I know I added more...

# v1.4.10

- Added a few changes such as automatically updating stock costs when price or quantity change.
- if old price and new price are the same they are not added in history file.

# v1.4.9

- Total Stock cost for BL and Polar.

# v1.4.8

- Hovering over price shows it in USD/CAD.

# v1.4.7

- Added Price History Page.
- Fixed total stock cost formating.

# v1.4.6

- Added total stock in cost to dock menu.
- Sorting is applied automatically once new item is added.

# v1.4.5

- Items less than or equal to 10 are shown in a "Low in Quantity" group.
- Unit quantities are now as decimal numbers.
- Notes sync with all parts with the same part numbers.

# v1.4.4

- Changed some stock costs to show all categories.

# v1.4.3

- Change total category cost to total stock cost.

# v1.4.2

- Added total category costs.
- Made Total Cost in Stock be zero when negative quantity.
- Website changes and fixes.

# v1.4.1

- Fixed more bugs with Item Controls menu.
- Changed some text for clarity in Main Window.
- Fixed visual bug when removing items from category.

# v1.4.0

- Fixed bug with Item Controls menu.
- View removed quantities from the new history view menu.

# v1.3.1

- Fixed bug with autofill button.
- Fixed bug with Item Controls menu.
- Selecting an item from the Item Controls menu puts it in the middle of the screen.

# v1.3.0 More QoL

- Added autofill button.

# v1.2.9 More QoL

- Current Quantity and Prices now link together with part numbers when you change the spinbox.
- Website now supports groups.
- Create, Delete, Clone category tab buttons have been removed.
- Create, Delete, Clone category buttons have been moved under the File -> Inventory Menu.

# v1.2.8

Version 1.2.8 QoL.

- Bug fixes.
- Printing inventory now considers groups.
- When pressing an item from the Item Controls it scrolls to it.

# v1.2.7

Version 1.2.7 Hotfix.

- Bug fixes.
- UI buttons added and changes to status tips.

# v1.2.6

Version 1.2.6 Hotfix.

- Bug fixes.

# v1.2.5

Version 1.2.5 Printing inventory.

- Print inventory, generats an excel sheet summary.
- View total unit cost for each category.
- View total units available to make in each category.

# v1.2.4

Version 1.2.4 performance improvements.

- adding or removing quantities had major issues which are now fixed.
- Further code optimizations and improved stability with json loading, parsing and threading.

# v1.2.3

Version 1.2.3 big performance improvements.

- Removing quantites is now multi-threaded with a progressbar, and made alot more speed.
- This is a hotfix for the v1.2.2 as it was bad update.

# v1.2.2

Version 1.2.2 performance improvements.

- Removing quantites is now multi-threaded with a progressbar, this has a slight performance drop, however its more stable.
- Added some wrap text to dialogs.

# v1.2.1

Version 1.2.1 fixed PO bugs.

# v1.2.0

Version 1.2.0 introduces many visual changes and features. With a side of many bug fixes.

## Purchase Orders

- Add purchase orders templates via the menu bar or dragging your excel templates onto the program.
- Remove purchase order templates via the menu bar.
- Opening a new purchase order generates a purchase order with an opdated PO number and date, and saves it inside its corresponding folder in the "PO's" directory of the program

## Backups

- Backups don't generate whenever you close the program, as uploading the inventory to the database is better.
- Drag a backup onto the program to load said backup, no idea why, but its an option that I thought would be cool to add.

## Website

- Read-only website for inventory viewing, works for mobile too.
<a style='text-decoration:none;color:cyan'href='<https://piney-manufacturing-inventory.herokuapp.com'><https://piney-manufacturing-inventory.herokuapp.com>></a>

## Design

- Buttons have been given a new and refreshing look.
- Each window has been redesigned with a new and pleasing look.
- Lightmode is not actively supported.
- Update manager has gotten a new revamped UI.
- Widgets have gotten a new background color, and border color fixes.
- Quantity goes red when under 1.
- Priority border changes color.

<h3>Inventory Menu</h3>
- Selecting items from the item controls menu are recolered, and optimized.
- Inventory changes now utilize threading when saving.
- Items now load one sequentially so the program does not appear to freeze, this introduce no performance drop what so ever, it merely is just a visual feature.
- Status button has gotten a new, flatter look.
- Progress bar to show when inventory is done loading.
- Added total unit cost.
- Added new permanent headers.
- You can add or remove items to groups.

<h3>View Menu</h3>
- Remade with a cleaner, compact and readable design.
- Also now deprecated (no more officialy supported), use the website for viewing the inventory, as it can sort the columns.

## Sorting

- Sorting items category wise is now possible.
  - You can sort items by priority, current quantity in stock, and alphabatical.

## Trusted Users

- You can now allow a select group of people to edit the inventory database.
  - Usernames are defined by the computers username.
  - To add or remove users from the trusted list, add their name to the "trusted_users" list in the settings config file.
    - This is purposefully not made clear.

## Settings

- The inventory now gets uploaded to the online database whenever a change in the inventory has been made. This can be enabled or disabled via the menu bar.

## Other

- Many bug fixes and crashes have been fixed.
- Server reliablity and improvements have been made.
- Drag a backup into the program to load that backup.
- There have been very very many code changes and optimizations to improve reliablity, readability, and maintainability and other ...abilitiy.
  - All dialogs have been tuned up.
  - Custom threads have been optimized.
  - All UI dialogs have had changes.
  - Added many custom widgets for ease of use.
  - Utilities have been slightly modified.
  - The main program has gotten a massive overhaul on every level concievable...
- Implemented a changelog (What your reading right now)

:)
