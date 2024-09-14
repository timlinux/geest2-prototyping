#!/usr/bin/env python

import sys
import os
import json
# Change to this when implementing in QGIS
#from qgis.PyQt.QtWidgets import (
from qgis.PyQt.QtWidgets import (
    QAbstractItemDelegate,
    QApplication,
    QTreeView,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QMessageBox,
    QHeaderView,
    QPushButton,
    QHBoxLayout,
    QTableWidget, 
    QTableWidgetItem,
    QMenu,
    QAction,
    QDialog,
    QLabel,
    QTextEdit,
)
# Change to this when implementing in QGIS
#from qgis.PyQt.QtCore import (
from PyQt5.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    Qt,
    QFileSystemWatcher,
    QPoint,
    QEvent,
    QTimer,
    pyqtSignal, 
    Qt
)
# Change to this when implementing in QGIS
#from qgis.PyQt.QtGui import (
from PyQt5.QtGui import QColor, QColor, QMovie



class JsonTreeItem:
    """A class representing a node in the tree."""

    def __init__(self, data, role, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.role = role  # Stores whether an item is a dimension, factor, or layer
        self.font_color = QColor(Qt.black)  # Default font color

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        if column < len(self.itemData):
            return self.itemData[column]
        return None

    def setData(self, column, value):
        if column < len(self.itemData):
            self.itemData[column] = value
            return True
        return False

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0


class JsonTreeModel(QAbstractItemModel):
    """Custom QAbstractItemModel to manage JSON data."""

    def __init__(self, json_data, parent=None):
        super().__init__(parent)
        self.rootItem = JsonTreeItem(["GEEST2", "Status", "Weight"], "root")
        self.loadJsonData(json_data)
        self.original_value = None  # To store the original value before editing

    def loadJsonData(self, json_data):
        """Load JSON data into the model, showing dimensions, factors, layers, and weightings."""
        self.beginResetModel()
        self.rootItem = JsonTreeItem(["GEEST2", "Status", "Weight"], "root")

        # Process dimensions, factors, and layers
        for dimension in json_data.get("dimensions", []):
            dimension_name = dimension["name"].title()  # Show dimensions in title case
            dimension_item = JsonTreeItem(
                [dimension_name, "🔴", ""], "dimension", self.rootItem
            )
            self.rootItem.appendChild(dimension_item)

            for factor in dimension.get("factors", []):
                factor_item = JsonTreeItem(
                    [factor["name"], "🔴", ""], "factor", dimension_item
                )
                dimension_item.appendChild(factor_item)

                num_layers = len(factor.get("layers", []))
                if num_layers == 0:
                    continue

                layer_weighting = 1 / num_layers
                factor_weighting_sum = 0.0

                for layer in factor.get("layers", []):
                    try:
                        weight = layer.get("weighting", "")
                    except:
                        weight = 0.0
                    layer_item = JsonTreeItem(
                        # We store the whole json layer object in the last column
                        # so that we can pull out any of the additional properties
                        # from it later
                        [layer["layer"], "🔴", f"{layer_weighting:.2f}", weight, layer],
                        "layer",
                        factor_item,
                    )
                    factor_item.appendChild(layer_item)
                    factor_weighting_sum += layer_weighting

                # Set the factor's total weighting
                factor_item.setData(2, f"{factor_weighting_sum:.2f}")
                self.update_font_color(
                    factor_item,
                    QColor(Qt.green if factor_weighting_sum == 1.0 else Qt.red),
                )

        self.endResetModel()

    def setData(self, index, value, role=Qt.EditRole):
        """Handle editing of values in the tree."""
        if role == Qt.EditRole:
            item = index.internalPointer()
            column = index.column()

            # Allow editing for the weighting column (index 2)
            if column == 2:
                try:
                    # Ensure the value is a valid floating-point number
                    value = float(value)
                    # Update the weighting value
                    return item.setData(column, f"{value:.2f}")
                except ValueError:
                    # Show an error if the value is not valid
                    QMessageBox.critical(
                        None,
                        "Invalid Value",
                        "Please enter a valid number for the weighting.",
                    )
                    return False

            # For other columns (like the name), we allow regular editing
            return item.setData(column, value)
        return False

    def flags(self, index):
        """Allow editing of the name and weighting columns."""
        item = index.internalPointer()
        if index.column() == 0 or index.column() == 2:
            # Allow editing for the first column (name) and third column (weighting)
            return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def update_font_color(self, item, color):
        """Update the font color of an item."""
        item.font_color = color
        self.layoutChanged.emit()

    def to_json(self):
        """Convert the tree structure back into a JSON document."""

        def recurse_tree(item):
            if item.role == "dimension":
                return {
                    "name": item.data(0).lower(),
                    "factors": [recurse_tree(child) for child in item.childItems],
                }
            elif item.role == "factor":
                return {
                    "name": item.data(0),
                    "layers": [recurse_tree(child) for child in item.childItems],
                }
            elif item.role == "layer":
                # TODO: Add more layer details here
                # like weighting etc.
                return {
                    "layer": item.data(0),
                    "Text": item.data(4)["Text"],
                    "Default Weighting": item.data(4)["Default Weighting"],
                    "Use Aggregate": item.data(4)["Use Aggregate"],
                    "Default Index Score": item.data(4)["Default Index Score"],
                    "Index Score": item.data(4)["Index Score"],
                    "Use default Idex Score": item.data(4)["Use default Idex Score"],
                    "Rasterise Raster": item.data(4)["Rasterise Raster"],
                    "Rasterise Polygon": item.data(4)["Rasterise Polygon"],
                    "Rasterise Polyline": item.data(4)["Rasterise Polyline"],
                    "Rasterise Point": item.data(4)["Rasterise Point"],
                    "Default Buffer Distances": item.data(4)["Default Buffer Distances"],
                    "Use Buffer point": item.data(4)["Use Buffer point"],
                    "Default pixel": item.data(4)["Default pixel"],
                    "Use Create Grid": item.data(4)["Use Create Grid"],
                    "Default Mode": item.data(4)["Default Mode"],
                    "Default Measurement": item.data(4)["Default Measurement"],
                    "Default Increments": item.data(4)["Default Increments"],
                    "Use Mode of Travel": item.data(4)["Use Mode of Travel"],
                    "source": item.data(4)["source"],
                    "indicator": item.data(4)["indicator"],
                    "query": item.data(4)["query"],
                }

        json_data = {
            "dimensions": [recurse_tree(child) for child in self.rootItem.childItems]
        }
        return json_data

    def clear_layer_weightings(self, factor_item):
        """Clear all weightings for layers under the given factor."""
        for i in range(factor_item.childCount()):
            layer_item = factor_item.child(i)
            layer_item.setData(2, "0.00")
        # After clearing, update the factor's total weighting
        factor_item.setData(2, "0.00")
        self.update_font_color(factor_item, QColor(Qt.red))
        self.layoutChanged.emit()

    def auto_assign_layer_weightings(self, factor_item):
        """Auto-assign weightings evenly across all layers under the factor."""
        num_layers = factor_item.childCount()
        if num_layers == 0:
            return
        layer_weighting = 1 / num_layers
        for i in range(num_layers):
            layer_item = factor_item.child(i)
            layer_item.setData(2, f"{layer_weighting:.2f}")
        # Update the factor's total weighting
        factor_item.setData(2, "1.00")
        self.update_font_color(factor_item, QColor(Qt.green))
        self.layoutChanged.emit()

    def add_factor(self, dimension_item):
        """Add a new factor under the given dimension."""
        new_factor = JsonTreeItem(["New Factor", "🔴", ""], "factor", dimension_item)
        dimension_item.appendChild(new_factor)
        self.layoutChanged.emit()

    def add_layer(self, factor_item):
        """Add a new layer under the given factor."""
        new_layer = JsonTreeItem(["New Layer", "🔴", "1.00"], "layer", factor_item)
        factor_item.appendChild(new_layer)
        self.layoutChanged.emit()

    def remove_item(self, item):
        """Remove the given item from its parent."""
        parent = item.parent()
        if parent:
            parent.childItems.remove(item)
        self.layoutChanged.emit()

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        return parentItem.childCount()

    def columnCount(self, parent=QModelIndex()):
        return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.DisplayRole:
            return item.data(index.column())
        elif role == Qt.ForegroundRole and index.column() == 2:
            return item.font_color  # Return the custom font color

        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            item = index.internalPointer()
            return item.setData(index.column(), value)
        return False

    def flags(self, index):
        """Allow editing and drag/drop reordering of dimensions."""
        item = index.internalPointer()

        if index.column() == 0:
            if item.parentItem is None:  # Top-level dimensions
                return (
                    Qt.ItemIsSelectable
                    | Qt.ItemIsEditable
                    | Qt.ItemIsEnabled
                    | Qt.ItemIsDragEnabled
                    | Qt.ItemIsDropEnabled
                )
            else:  # Factors and layers
                return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def index(self, row, column, parent=QModelIndex()):
        """Create a QModelIndex for the specified row and column."""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        return QModelIndex()

    def parent(self, index):
        """Return the parent of the QModelIndex."""
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)
        return None

    def add_dimension(self, name="New Dimension"):
        """Add a new dimension to the root and allow editing."""
        new_dimension = JsonTreeItem([name, "🔴", ""], "dimension", self.rootItem)
        self.rootItem.appendChild(new_dimension)
        self.layoutChanged.emit()

    def removeRow(self, row, parent=QModelIndex()):
        """Allow removing dimensions."""
        parentItem = self.rootItem if not parent.isValid() else parent.internalPointer()
        parentItem.childItems.pop(row)
        self.layoutChanged.emit()


class CustomTreeView(QTreeView):
    """Custom QTreeView to handle editing and reverting on Escape or focus loss."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_editing_index = None

    def edit(self, index, trigger, event):
        """Start editing the item at the given index."""
        self.current_editing_index = index
        model = self.model()
        self.original_value = model.data(
            index, Qt.DisplayRole
        )  # Store original value before editing
        return super().edit(index, trigger, event)

    def keyPressEvent(self, event):
        """Handle Escape key to cancel editing."""
        if event.key() == Qt.Key_Escape and self.current_editing_index:
            self.model().setData(
                self.current_editing_index, self.original_value, Qt.EditRole
            )
            if self.hasCurrentEditor():
                self.closeEditor(
                    self.current_editor(), QAbstractItemDelegate.RevertModelCache
                )
        else:
            super().keyPressEvent(event)

    def commitData(self, editor):
        """Handle commit data, reverting if needed."""
        if self.current_editing_index:
            super().commitData(editor)
            self.current_editing_index = None
            self.original_value = None

    def closeEditor(self, editor, hint):
        """Handle closing the editor and reverting the value on Escape or clicking elsewhere."""
        if (
            hint == QAbstractItemDelegate.RevertModelCache
            and self.current_editing_index
        ):
            self.model().setData(
                self.current_editing_index, self.original_value, Qt.EditRole
            )
        self.current_editing_index = None
        self.original_value = None
        super().closeEditor(editor, hint)


class MainWindow(QMainWindow):
    def __init__(self, json_file=None):
        super().__init__()

        self.json_file = json_file
        self.setWindowTitle("JSON Model Viewer with Editable Weightings")
        layout = QVBoxLayout()

        if json_file:
            # Load JSON data
            self.load_json()
        else:
            self.json_data = {"dimensions": []}

        # Create a CustomTreeView widget to handle editing and reverts
        self.treeView = CustomTreeView()
        self.treeView.setDragDropMode(QTreeView.InternalMove)
        self.treeView.setDefaultDropAction(Qt.MoveAction)

        # Create a model for the QTreeView using custom JsonTreeModel
        self.model = JsonTreeModel(self.json_data)
        self.treeView.setModel(self.model)

        self.treeView.setEditTriggers(
            QTreeView.DoubleClicked
        )  # Only allow editing on double-click

        # Enable custom context menu
        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.open_context_menu)

        # Expand the whole tree by default
        self.treeView.expandAll()

        # Set the second and third columns to the exact width of the 🔴 character and weighting
        self.treeView.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.treeView.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        # Expand the first column to use the remaining space and resize with the dialog
        self.treeView.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.treeView.header().setStretchLastSection(False)
        # Set layout
        layout.addWidget(self.treeView)

        # Add a button bar at the bottom with a Close button and Add Dimension button
        button_bar = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        add_dimension_button = QPushButton("⭐️ Add Dimension")
        add_dimension_button.clicked.connect(self.add_dimension)

        load_json_button = QPushButton("📂 Load Template")
        load_json_button.clicked.connect(self.load_json_from_file)

        export_json_button = QPushButton("📦️ Save Template")
        export_json_button.clicked.connect(self.export_json_to_file)

        button_bar.addWidget(add_dimension_button)
        button_bar.addStretch()
        
        prepare_button = QPushButton("🛸 Prepare")
        prepare_button.clicked.connect(self.process_leaves)
        button_bar.addWidget(prepare_button)
        button_bar.addStretch()
        
        button_bar.addWidget(load_json_button)
        button_bar.addWidget(export_json_button)
        button_bar.addStretch()
        button_bar.addWidget(close_button)
        layout.addLayout(button_bar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Maximize the window on start
        self.showMaximized()

    def load_json(self):
        """Load the JSON data from the file."""
        with open(self.json_file, "r") as f:
            self.json_data = json.load(f)

    def load_json_from_file(self):
        """Prompt the user to load a JSON file and update the tree."""
        json_file, _ = QFileDialog.getOpenFileName(
            self, "Open JSON File", os.getcwd(), "JSON Files (*.json);;All Files (*)"
        )
        if json_file:
            self.json_file = json_file
            self.load_json()
            self.model.loadJsonData(self.json_data)
            self.treeView.expandAll()

    def export_json_to_file(self):
        """Export the current tree data to a JSON file."""
        json_data = self.model.to_json()
        with open("export.json", "w") as f:
            json.dump(json_data, f, indent=4)
        QMessageBox.information(self, "Export Success", "Tree exported to export.json")

    def add_dimension(self):
        """Add a new dimension to the model."""
        self.model.add_dimension()

    def open_context_menu(self, position: QPoint):
        """Handle right-click context menu."""
        index = self.treeView.indexAt(position)
        if not index.isValid():
            return

        item = index.internalPointer()

        # Check the role of the item directly from the stored role
        if item.role == "dimension":
            # Context menu for dimensions
            add_factor_action = QAction("Add Factor", self)
            remove_dimension_action = QAction("Remove Dimension", self)

            # Connect actions
            add_factor_action.triggered.connect(lambda: self.model.add_factor(item))
            remove_dimension_action.triggered.connect(
                lambda: self.model.remove_item(item)
            )

            # Add actions to menu
            menu = QMenu(self)
            menu.addAction(add_factor_action)
            menu.addAction(remove_dimension_action)

        elif item.role == "factor":
            # Context menu for factors
            add_layer_action = QAction("Add Layer", self)
            remove_factor_action = QAction("Remove Factor", self)
            clear_action = QAction("Clear Layer Weightings", self)
            auto_assign_action = QAction("Auto Assign Layer Weightings", self)

            # Connect actions
            add_layer_action.triggered.connect(lambda: self.model.add_layer(item))
            remove_factor_action.triggered.connect(lambda: self.model.remove_item(item))
            clear_action.triggered.connect(
                lambda: self.model.clear_layer_weightings(item)
            )
            auto_assign_action.triggered.connect(
                lambda: self.model.auto_assign_layer_weightings(item)
            )

            # Add actions to menu
            menu = QMenu(self)
            menu.addAction(add_layer_action)
            menu.addAction(remove_factor_action)
            menu.addAction(clear_action)
            menu.addAction(auto_assign_action)

        elif item.role == "layer":
            # Context menu for layers
            show_properties_action = QAction("🔘 Show Properties", self)
            remove_layer_action = QAction("❌ Remove Layer", self)

            # Connect actions
            show_properties_action.triggered.connect(
                lambda: self.show_layer_properties(item)
            )
            remove_layer_action.triggered.connect(lambda: self.model.remove_item(item))

            # Add actions to menu
            menu = QMenu(self)
            menu.addAction(show_properties_action)
            menu.addAction(remove_layer_action)

        # Show the menu at the cursor's position
        menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def show_layer_properties(self, item):
        """Open a dialog showing layer properties."""
        layer_name = item.data(0)
        layer_data = item.data(4)  # The 4th column stores the whole layer data dict
        dialog = LayerDetailDialog(layer_name, layer_data, self)
        dialog.exec_()

    def process_leaves(self):
        """
        This function processes all the leaf nodes in the QTreeView.
        Each leaf node is processed by changing its text to red, showing an animated icon, 
        waiting for 2 seconds, and then reverting the text color back to black.
        """
        model = self.treeView.model()  # Get the model from the tree_view

        # Find all leaf nodes
        leaf_nodes = []
        
        def find_leaves(index):
            """Recursively find all leaf nodes starting from the given index."""
            if model.hasChildren(index):
                for row in range(model.rowCount(index)):
                    child_index = model.index(row, 0, index)
                    find_leaves(child_index)
            else:
                leaf_nodes.append(index)

        # Populate the leaf_nodes list
        # Start from the root index of the model
        root_index = model.index(0, 0)
        for row in range(model.rowCount()):
            find_leaves(model.index(row, 0, root_index))

        # Process each leaf node
        self.process_each_leaf(leaf_nodes, 0)

    def process_each_leaf(self, leaf_nodes, index):
        """
        Processes each leaf node by changing the text to red, showing an animated icon,
        waiting for 2 seconds, and then reverting the text color to black.
        """
        # Base case: if all nodes are processed, return
        if index >= len(leaf_nodes):
            return

        # Get the current leaf node index
        node_index = leaf_nodes[index]
        model = self.treeView.model()

        # Change text color to red to indicate processing
        model.setData(node_index, QColor(Qt.red), Qt.ForegroundRole)

        # Set an animated icon (using a QLabel and QMovie to simulate animation)
        movie = QMovie("throbber.gif")  # Use a valid path to an animated gif
        # Get the height of the current row
        row_height = self.treeView.rowHeight(node_index)
        # Scale the movie to the row height
        movie.setScaledSize(movie.currentPixmap().size().scaled(row_height, row_height, Qt.KeepAspectRatio))
        
        label = QLabel()
        label.setMovie(movie)
        movie.start()

        # Set the animated icon in the first column of the node
        self.treeView.setIndexWidget(node_index, label)

        # Wait for 2 seconds to simulate processing
        QTimer.singleShot(2000, lambda: self.finish_processing(
            node_index, leaf_nodes, index, movie))


    def finish_processing(self, node_index, leaf_nodes, index, movie):
        """
        Finishes processing by reverting text color to black and removing the animated icon.
        Then it proceeds to the next node.
        """
        model = self.treeView.model()
        # Stop the animation and remove the animated icon
        movie.stop()
        self.treeView.setIndexWidget(node_index, None)

        # Change text color back to black after processing
        model.setData(node_index, QColor(Qt.black), Qt.ForegroundRole)

        # Move to the next node
        self.process_each_leaf(leaf_nodes, index + 1)


class LayerDetailDialog(QDialog):
    """Dialog to show layer properties."""
    
    # Signal to emit the updated data as a dictionary
    dataUpdated = pyqtSignal(dict)
    
    def __init__(self, layer_name, layer_data, parent=None):
        super().__init__(parent)

        self.setWindowTitle(layer_name)

        layout = QVBoxLayout()

        # Heading for the dialog
        heading_label = QLabel(layer_name)
        layout.addWidget(heading_label)

        # Description for the dialog
        description_text = QTextEdit(
            layer_data["indicator"] if "indicator" in layer_data else "")
        description_text.setReadOnly(True)
        layout.addWidget(description_text)

        # Create the QTableWidget
        self.table = QTableWidget()
        self.table.setColumnCount(2)  # Two columns (Key and Value)
        self.table.setHorizontalHeaderLabels(["Key", "Value"])

        # Set the number of rows equal to the number of key-value pairs
        self.table.setRowCount(len(layer_data))

        # Populate the table with key-value pairs
        for row, (key, value) in enumerate(layer_data.items()):
            # Column 1: Key (read-only)
            key_item = QTableWidgetItem(str(key))
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)  # Make it read-only
            self.table.setItem(row, 0, key_item)
            
            # Column 2: Value (editable)
            value_item = QTableWidgetItem(str(value))
            self.table.setItem(row, 1, value_item)

        # Set column resize mode to stretch to fill the layout
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Key column
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Value column

        # Add the table to the layout
        layout.addWidget(self.table)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.on_close)  # Connect close button to custom close handler
        layout.addWidget(close_button)

        self.setLayout(layout)

    def on_close(self):
        """Handle the dialog close event by emitting the updated data."""
        updated_data = self.get_updated_data_from_table()
        self.dataUpdated.emit(updated_data)  # Emit the updated data as a dictionary
        self.close()

    def get_updated_data_from_table(self):
        """Convert the table back into a dictionary with any changes made."""
        updated_data = {}
        for row in range(self.table.rowCount()):
            key = self.table.item(row, 0).text()  # Get the key (read-only)
            value = self.table.item(row, 1).text()  # Get the updated value
            updated_data[key] = value  # Update the dictionary
        return updated_data


# Main function to run the application
def main():
    app = QApplication(sys.argv)

    # Fetch the value of GEEST_DEBUG from an environment variable
    debug_mode = int(os.getenv("GEEST_DEBUG", 0))
    if debug_mode:
        import multiprocessing  # pylint: disable=import-outside-toplevel

        if multiprocessing.current_process().pid > 1:
            import debugpy  # pylint: disable=import-outside-toplevel

            debugpy.listen(("0.0.0.0", 9000))
            debugpy.wait_for_client()

    # Set default JSON path
    cwd = os.getcwd()
    default_json_file = os.path.join(cwd, "model.json")

    # Check if model.json exists, otherwise prompt for a JSON file
    json_file = default_json_file if os.path.exists(default_json_file) else None
    if not json_file:
        json_file, _ = QFileDialog.getOpenFileName(
            None, "Open JSON File", cwd, "JSON Files (*.json);;All Files (*)"
        )
        if not json_file:
            QMessageBox.critical(None, "Error", "No JSON file selected!")
            return
    # Set the application style to "kvantum" after QApplication instance
    app.setStyle("kvantum")  # Launch the main window
    window = MainWindow(json_file)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
