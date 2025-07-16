import re
from datetime import datetime, timezone
from typing import Callable, Literal

import numpy as np
import pyqtgraph as pg
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QTreeWidget, QTreeWidgetItem

from ui.dialogs.view_item_history_dialog_UI import Ui_Form
from ui.theme import theme_var
from utils.workers.history.get_item_order_history import GetItemOrderHistoryWorker
from utils.workers.history.get_item_price_history import GetItemPriceHistoryWorker
from utils.workers.history.get_item_quantity_history import GetItemQuantityHistoryWorker
from utils.workers.runnable_chain import RunnableChain


class Graph(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(500)
        self.setMinimumWidth(500)
        self.setBackground(theme_var("background"))


class ViewItemHistoryDialog(QDialog, Ui_Form):
    def __init__(
        self,
        parent,
        item_type: Literal["sheet", "component", "structural_steel_item", "laser_cut_part"],
        item_id: int,
    ):
        super().__init__(parent)
        self.setupUi(self)
        self._parent_widget = parent
        self.item_type = item_type
        self.item_id = item_id

        if self.item_type == "laser_cut_part":
            self.tabWidget.tabBar().setTabVisible(1, False)
            self.tabWidget.tabBar().setTabVisible(2, False)

        self.resize(1200, 900)
        self.get_history()

    def load_order_pending_history_tree(self, data: dict[str, list[dict]]):
        tree_widget = QTreeWidget()
        tree_widget.setColumnCount(4)
        tree_widget.setHeaderLabels(["Created At", "Event Type", "Modified By", "Version"])

        for entry in data.get("history_entries", []):
            color = theme_var("disabled")
            # Root-level item for this event/version
            tree_item = QTreeWidgetItem(tree_widget)
            tree_item.setText(0, entry["created_at_formatted"])
            tree_item.setText(1, entry["event_type"].replace("_", " ").title())
            tree_item.setText(2, entry["modified_by"])
            tree_item.setText(3, str(entry["version"]))

            # Add "Details" child
            details_item = QTreeWidgetItem(tree_item)
            details_item.setText(0, "Details")

            details = entry.get("details", {})

            if "new_orders" in details:
                color = theme_var("primary-green")
                for order in details["new_orders"]:
                    order_pending_quantity = order.get("order_pending_quantity")
                    order_pending_date = order.get("order_pending_date")
                    expected_arrival_time = order.get("expected_arrival_time")
                    notes = order.get("notes", "")

                    if order_pending_quantity is not None:
                        qty_widget = QTreeWidgetItem(details_item)
                        qty_widget.setText(0, f"Order Pending Quantity: {order_pending_quantity}")
                        details_item.addChild(qty_widget)

                    if order_pending_date:
                        date_widget = QTreeWidgetItem(details_item)
                        date_widget.setText(0, f"Order Pending Date: {order_pending_date}")
                        details_item.addChild(date_widget)

                    if expected_arrival_time:
                        expected_widget = QTreeWidgetItem(details_item)
                        expected_widget.setText(0, f"Expected Arrival Time: {expected_arrival_time}")
                        details_item.addChild(expected_widget)

                    if notes:
                        notes_widget = QTreeWidgetItem(details_item)
                        notes_widget.setText(0, f"Notes: {notes}")
                        details_item.addChild(notes_widget)
            elif "removed_orders" in details:
                color = theme_var("primary-red")
                for order in details["removed_orders"]:
                    order_pending_quantity = order.get("order_pending_quantity")
                    order_pending_date = order.get("order_pending_date")
                    expected_arrival_time = order.get("expected_arrival_time")
                    notes = order.get("notes", "")

                    if order_pending_quantity is not None:
                        qty_widget = QTreeWidgetItem(details_item)
                        qty_widget.setText(
                            0,
                            f"Order Pending Quantity (Removed): {order_pending_quantity}",
                        )
                        details_item.addChild(qty_widget)

                    if order_pending_date:
                        date_widget = QTreeWidgetItem(details_item)
                        date_widget.setText(0, f"Order Pending Date (Removed): {order_pending_date}")
                        details_item.addChild(date_widget)

                    if expected_arrival_time:
                        expected_widget = QTreeWidgetItem(details_item)
                        expected_widget.setText(
                            0,
                            f"Expected Arrival Time (Removed): {expected_arrival_time}",
                        )
                        details_item.addChild(expected_widget)

                    if notes:
                        notes_widget = QTreeWidgetItem(details_item)
                        notes_widget.setText(0, f"Notes (Removed): {notes}")
                        details_item.addChild(notes_widget)

            elif "from" in details and "to" in details:
                color = theme_var("primary-yellow")

                from_order = details["from"][0] if details["from"] else {}
                to_order = details["to"][0] if details["to"] else {}

                from_qty = from_order.get("order_pending_quantity")
                to_qty = to_order.get("order_pending_quantity")
                from_date = from_order.get("order_pending_date")
                to_date = to_order.get("order_pending_date")
                from_expected = from_order.get("expected_arrival_time")
                to_expected = to_order.get("expected_arrival_time")
                from_notes = from_order.get("notes")
                to_notes = to_order.get("notes")

                if from_qty != to_qty:
                    qty_widget = QTreeWidgetItem(details_item)
                    qty_widget.setText(0, f"Order Pending Quantity: {from_qty} → {to_qty}")
                    details_item.addChild(qty_widget)

                if from_date != to_date:
                    date_widget = QTreeWidgetItem(details_item)
                    date_widget.setText(0, f"Order Pending Date: {from_date} → {to_date}")
                    details_item.addChild(date_widget)

                if from_expected != to_expected:
                    expected_widget = QTreeWidgetItem(details_item)
                    expected_widget.setText(0, f"Expected Arrival Time: {from_expected} → {to_expected}")
                    details_item.addChild(expected_widget)

                if from_notes != to_notes:
                    notes_widget = QTreeWidgetItem(details_item)
                    notes_widget.setText(0, f"Notes: {from_notes} → {to_notes}")
                    details_item.addChild(notes_widget)

            tree_item.addChild(details_item)

            # Add quantity change if exists
            quantity_change = entry.get("quantity_change")
            if quantity_change:
                qty_item = QTreeWidgetItem(tree_item)
                qty_item.setText(
                    0,
                    f"{self.item_type.title()} Quantity Change: {quantity_change['from_quantity']} → {quantity_change['to_quantity']}",
                )
                tree_item.addChild(qty_item)

            tree_widget.addTopLevelItem(tree_item)
            self.set_tree_widget_item_foreground(tree_item, QColor(color))

        tree_widget.expandAll()

        for i in range(tree_widget.columnCount()):
            tree_widget.resizeColumnToContents(i)

        self.order_pending_history_tree_layout.addWidget(tree_widget)

    def load_order_pending_history_graph(self, response: dict[str, list[dict[str, str]]]):
        dates = []
        pending_quantities = []
        tooltips = []
        timestamps = []
        colors = []

        for entry in reversed(response.get("history_entries", [])):
            event_type = entry["event_type"]
            details = entry["details"]

            try:
                dt = datetime.fromisoformat(entry["created_at"])

                # Determine pending quantity and color
                if "new_orders" in details:
                    qty = details["new_orders"][0]["order_pending_quantity"]
                    color = theme_var("primary-green")
                elif "removed_orders" in details:
                    qty = 0
                    color = theme_var("primary-red")
                elif "from" in details and "to" in details:
                    qty = details["to"][0]["order_pending_quantity"]
                    color = theme_var("primary-yellow")
                else:
                    continue

                dates.append(dt)
                timestamps.append(dt.timestamp())
                pending_quantities.append(qty)
                tooltips.append(f"{event_type.replace('_', ' ').title()}: {qty}")
                colors.append(color)

            except Exception as e:
                continue

        # Create plot
        plot_widget = Graph(self)
        plot_widget.setTitle(
            "Order Pending Quantity Over Time",
            color=theme_var("on-surface"),
            size="14pt",
        )
        plot_widget.setLabel("left", "Pending Quantity")
        plot_widget.setLabel("bottom", "Time")

        # Add legend
        legend = plot_widget.addLegend(offset=(30, 30))
        pen_green = pg.mkPen(theme_var("primary-green"), width=2)
        pen_red = pg.mkPen(theme_var("primary-red"), width=2)
        pen_yellow = pg.mkPen(theme_var("primary-yellow"), width=2)

        legend.addItem(pg.PlotDataItem(pen=pen_green), "Order Added")
        legend.addItem(pg.PlotDataItem(pen=pen_red), "Order Removed")
        legend.addItem(pg.PlotDataItem(pen=pen_yellow), "Order Modified")

        for i in range(len(timestamps) - 1):
            x_segment = [timestamps[i], timestamps[i + 1]]
            y_segment = [pending_quantities[i], pending_quantities[i + 1]]
            segment_color = colors[i + 1]
            seg_pen = pg.mkPen(segment_color, width=2)
            plot_widget.plot(x_segment, y_segment, pen=seg_pen)

        # Create scatter plot item with per-node colors
        spots = []
        for ts, qty, tip, col in zip(timestamps, pending_quantities, tooltips, colors):
            spots.append(
                {
                    "pos": (ts, qty),
                    "data": tip,
                    "brush": pg.mkBrush(col),
                    "pen": pg.mkPen(col),
                    "symbol": "o",
                    "size": 10,
                }
            )

        scatter = pg.ScatterPlotItem(size=10, hoverable=True, hoverSymbol="s")
        scatter.addPoints(spots)
        plot_widget.addItem(scatter)

        # Format x-axis ticks
        axis = plot_widget.getAxis("bottom")
        axis.enableAutoSIPrefix(False)
        axis.setTicks([[(ts, self.format_datetime_with_relative(dt)) for ts, dt in zip(timestamps, dates)]])

        self.order_pending_history_graph_layout.addWidget(plot_widget)

    def load_quantity_history_tree(self, data: dict[str, list[dict]]):
        tree_widget = QTreeWidget()
        tree_widget.setColumnCount(4)
        tree_widget.setHeaderLabels(["Created At", "Event Type", "Modified By", "Version"])

        for entry in data.get("history_entries", []):
            if entry["event_type"] == "quantity_added":
                color = theme_var("primary-green")
            elif entry["event_type"] == "quantity_removed":
                color = theme_var("primary-red")
            # Root-level item for this event/version
            tree_item = QTreeWidgetItem(tree_widget)
            tree_item.setText(0, entry["created_at_formatted"])
            tree_item.setText(1, entry["event_type"].replace("_", " ").title())
            tree_item.setText(2, entry["modified_by"])
            tree_item.setText(3, str(entry["version"]))

            # Add "Details" child
            quantity_change = QTreeWidgetItem(tree_item)

            quantity_change.setText(
                0,
                f"Quantity Change: {entry['from_quantity']} → {entry['to_quantity']}",
            )

            quantity_change.setText(1, entry["details"]["modification_reason"])

            tree_item.addChild(quantity_change)

            tree_widget.addTopLevelItem(tree_item)
            self.set_tree_widget_item_foreground(tree_item, QColor(color))

        tree_widget.expandAll()

        for i in range(tree_widget.columnCount()):
            tree_widget.resizeColumnToContents(i)

        self.quantity_history_tree_layout.addWidget(tree_widget)

    def load_quantity_history_graph(self, response: dict[str, list[dict[str, str]]]):
        # Prepare data
        dates = []
        quantities = []
        tooltips = []
        timestamps = []
        colors = []

        for entry in reversed(response.get("history_entries", [])):
            event_type = entry["event_type"]
            try:
                dt = datetime.fromisoformat(entry["created_at"])
                dates.append(dt)
                timestamps.append(dt.timestamp())
                quantities.append(entry["to_quantity"])
                tooltips.append(f"{entry['from_quantity']} → {entry['to_quantity']}\n{entry['details']['modification_reason']}")

                # Color coding
                if event_type == "quantity_added":
                    color = theme_var("primary-green")
                elif event_type == "quantity_removed":
                    color = theme_var("primary-red")
                else:
                    color = theme_var("primary-yellow")  # fallback for others if needed
                colors.append(color)

            except ValueError:
                continue

        # Create plot
        plot_widget = Graph(self)
        plot_widget.setTitle("Quantity Change Over Time", color=theme_var("on-surface"), size="14pt")
        plot_widget.setLabel("left", "Quantity")
        plot_widget.setLabel("bottom", "Time")

        # Add legend
        legend = plot_widget.addLegend(offset=(30, 30))
        pen_green = pg.mkPen(theme_var("primary-green"), width=2)
        pen_red = pg.mkPen(theme_var("primary-red"), width=2)

        # Add fake plots to legend
        legend.addItem(pg.PlotDataItem(pen=pen_green), "Quantity Added")
        legend.addItem(pg.PlotDataItem(pen=pen_red), "Quantity Removed")

        # Draw line segments colored individually
        for i in range(len(timestamps) - 1):
            x_segment = [timestamps[i], timestamps[i + 1]]
            y_segment = [quantities[i], quantities[i + 1]]
            seg_color = colors[i + 1]  # use "to" color of next point
            seg_pen = pg.mkPen(seg_color, width=2)
            plot_widget.plot(x_segment, y_segment, pen=seg_pen)

        # Create colored scatter points
        spots = []
        for ts, qty, tip, col in zip(timestamps, quantities, tooltips, colors):
            spots.append(
                {
                    "pos": (ts, qty),
                    "data": tip,
                    "brush": pg.mkBrush(col),
                    "pen": pg.mkPen(col),
                    "symbol": "o",
                    "size": 10,
                }
            )

        scatter = pg.ScatterPlotItem(size=10, hoverable=True, hoverSymbol="s")
        scatter.addPoints(spots)
        plot_widget.addItem(scatter)

        # Format x-axis ticks
        axis = plot_widget.getAxis("bottom")
        axis.enableAutoSIPrefix(False)
        axis.setTicks([[(ts, self.format_datetime_with_relative(dt)) for ts, dt in zip(timestamps, dates)]])

        self.quantity_history_graph_layout.addWidget(plot_widget)

    def load_price_history_tree(self, data: dict[str, list[dict]]):
        tree_widget = QTreeWidget()
        tree_widget.setColumnCount(4)
        tree_widget.setHeaderLabels(["Created At", "Event Type", "Modified By", "Version"])

        for entry in data.get("history_entries", []):
            if entry["event_type"] == "price_increased":
                color = theme_var("primary-green")
            elif entry["event_type"] == "price_decreased":
                color = theme_var("primary-red")
            else:
                color = theme_var("primary-yellow")

            # Root-level item for this event/version
            tree_item = QTreeWidgetItem(tree_widget)
            tree_item.setText(0, entry["created_at_formatted"])
            tree_item.setText(1, entry["event_type"].replace("_", " ").title())
            tree_item.setText(2, entry["modified_by"])
            tree_item.setText(3, str(entry["version"]))

            # Add "Details" child
            price_change = QTreeWidgetItem(tree_item)
            price_change.setText(0, f"Price Change: {entry['from_price']} → {entry['to_price']}")
            price_change.setText(1, entry["details"]["modification_reason"])

            tree_item.addChild(price_change)
            tree_widget.addTopLevelItem(tree_item)
            self.set_tree_widget_item_foreground(tree_item, QColor(color))

        tree_widget.expandAll()

        for i in range(tree_widget.columnCount()):
            tree_widget.resizeColumnToContents(i)

        self.price_history_tree_layout.addWidget(tree_widget)

    def load_price_history_graph(self, response: dict[str, list[dict[str, str]]]):
        dates = []
        prices = []
        tooltips = []
        timestamps = []
        colors = []

        for entry in reversed(response.get("history_entries", [])):
            event_type = entry["event_type"]

            try:
                dt = datetime.fromisoformat(entry["created_at"])
                dates.append(dt)
                timestamps.append(dt.timestamp())
                prices.append(entry["to_price"])
                tooltips.append(f"{entry['from_price']} → {entry['to_price']}\n{entry['details']['modification_reason']}")

                if event_type == "price_increased":
                    color = theme_var("primary-green")
                elif event_type == "price_decreased":
                    color = theme_var("primary-red")
                else:
                    color = theme_var("primary-yellow")
                colors.append(color)

            except ValueError:
                continue

        # Create plot
        plot_widget = Graph(self)
        plot_widget.setTitle("Price Change Over Time", color=theme_var("on-surface"), size="14pt")
        plot_widget.setLabel("left", "Price")
        plot_widget.setLabel("bottom", "Time")

        # Add legend
        legend = plot_widget.addLegend(offset=(30, 30))
        pen_green = pg.mkPen(theme_var("primary-green"), width=2)
        pen_red = pg.mkPen(theme_var("primary-red"), width=2)

        legend.addItem(pg.PlotDataItem(pen=pen_green), "Price Increased")
        legend.addItem(pg.PlotDataItem(pen=pen_red), "Price Decreased")

        # Draw colored segments
        for i in range(len(timestamps) - 1):
            x_segment = [timestamps[i], timestamps[i + 1]]
            y_segment = [prices[i], prices[i + 1]]
            seg_color = colors[i + 1]
            seg_pen = pg.mkPen(seg_color, width=2)
            plot_widget.plot(x_segment, y_segment, pen=seg_pen)

        # Create scatter points
        spots = []
        for ts, price, tip, col in zip(timestamps, prices, tooltips, colors):
            spots.append(
                {
                    "pos": (ts, price),
                    "data": tip,
                    "brush": pg.mkBrush(col),
                    "pen": pg.mkPen(col),
                    "symbol": "o",
                    "size": 10,
                }
            )

        scatter = pg.ScatterPlotItem(size=10, hoverable=True, hoverSymbol="s")
        scatter.addPoints(spots)
        plot_widget.addItem(scatter)

        # Add linear regression line
        if len(timestamps) >= 2:
            x = np.array(timestamps)
            y = np.array(prices)
            slope, intercept = np.polyfit(x, y, 1)
            x_line = np.linspace(min(x), max(x), 500)
            y_line = slope * x_line + intercept
            reg_pen = pg.mkPen(
                theme_var("primary-yellow"),
                style=pg.QtCore.Qt.PenStyle.DashLine,
                width=2,
            )
            plot_widget.plot(x_line, y_line, pen=reg_pen, name="Linear Regression")

        # Format x-axis ticks
        axis = plot_widget.getAxis("bottom")
        axis.enableAutoSIPrefix(False)
        axis.setTicks([[(ts, dt.strftime("%b %d\n%I:%M %p")) for ts, dt in zip(timestamps, dates)]])

        self.price_layout_graph_layout.addWidget(plot_widget)

    def format_datetime_with_relative(self, dt: datetime) -> str:
        # Ensure timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        delta = now - dt

        # Calculate days difference
        days_ago = delta.days
        if days_ago == 0:
            rel = "today"
        elif days_ago == 1:
            rel = "1 day ago"
        else:
            rel = f"{days_ago} days ago"

        # Format date: Month day, year (Weekday) at HH:MM AM/PM
        formatted = dt.strftime("%B %-d, %Y (%A) at %-I:%M %p")
        return f"{formatted} ({rel})"

    def clean_datetime_string(self, date_str: str) -> str:
        # Remove all parenthesis content
        no_parens = re.sub(r"\s*\([^)]*\)", "", date_str)
        # Remove 'at' word
        cleaned = no_parens.replace("at", "").strip()
        # Remove double spaces if any left
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned

    def set_tree_widget_item_foreground(self, item: QTreeWidgetItem, color: QColor):
        for i in range(item.columnCount()):
            item.setForeground(i, color)

        for i in range(item.childCount()):
            for j in range(item.child(i).columnCount()):
                item.child(i).setForeground(j, color)
                if item.child(i).childCount():
                    self.set_tree_widget_item_foreground(item.child(i), color)

    def get_history(self):
        chain = RunnableChain(self)
        get_quantity_history_worker = GetItemQuantityHistoryWorker(self.item_type, self.item_id)
        chain.add(get_quantity_history_worker, self.get_quantity_history_response)
        if self.item_type in ["sheet", "component"]:
            get_price_history_worker = GetItemPriceHistoryWorker(self.item_type, self.item_id)
            chain.add(get_price_history_worker, self.get_price_history_response)
        if self.item_type in ["sheet", "component"]:
            get_order_history_worker = GetItemOrderHistoryWorker(self.item_type, self.item_id)
            chain.add(get_order_history_worker, self.get_order_history_response)
        chain.start()

    def get_order_history_response(self, response: dict[str, list[dict[str, str]]], next_step: Callable):
        self.load_order_pending_history_tree(response)
        self.load_order_pending_history_graph(response)
        next_step()

    def get_quantity_history_response(self, response: dict[str, list[dict[str, str]]], next_step: Callable):
        self.load_quantity_history_tree(response)
        self.load_quantity_history_graph(response)
        next_step()

    def get_price_history_response(self, response: dict[str, list[dict[str, str]]], next_step: Callable):
        self.load_price_history_tree(response)
        self.load_price_history_graph(response)
        next_step()
