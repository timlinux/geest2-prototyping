#!/usr/bin/env python

import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QTreeView, QMainWindow, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QHeaderView, QPushButton, QHBoxLayout, QMenu, QAction, QDialog, QLabel, QTextEdit
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt, QFileSystemWatcher, QPoint, QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QAbstractItemDelegate

class JsonTreeItem:
    """A class representing a node in the tree."""
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
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
        self.rootItem = JsonTreeItem(["Dimension/Factor/Layer", "Status", "Weighting"])
        self.loadJsonData(json_data)
        self.original_value = None  # To store the original value before editing

    def loadJsonData(self, json_data):
        """Load JSON data into the model, showing dimensions, factors, layers, and weightings."""
        self.beginResetModel()
        self.rootItem = JsonTreeItem(["Dimension/Factor/Layer", "Status", "Weighting"])

        # Process dimensions, factors, and layers
        for dimension in json_data.get("dimensions", []):
            dimension_name = dimension["name"].title()  # Show dimensions in title case
            dimension_item = JsonTreeItem([dimension_name, "🔴", ""], self.rootItem)
            self.rootItem.appendChild(dimension_item)

            for factor in dimension.get("factors", []):
                factor_item = JsonTreeItem([factor["name"], "🔴", ""], dimension_item)
                dimension_item.appendChild(factor_item)

                num_layers = len(factor.get("layers", []))
                if num_layers == 0:
                    continue

                layer_weighting = 1 / num_layers
                factor_weighting_sum = 0.0

                for layer in factor.get("layers", []):
                    for layer_name, layer_data in layer.items():
                        layer_item = JsonTreeItem([layer_name, "🔴", f"{layer_weighting:.2f}", layer_data], factor_item)
                        factor_item.appendChild(layer_item)
                        factor_weighting_sum += layer_weighting

                # Set the factor's total weighting
                factor_item.setData(2, f"{factor_weighting_sum:.2f}")
                self.update_font_color(factor_item, QColor(Qt.green if factor_weighting_sum == 1.0 else Qt.red))

        self.endResetModel()

    def update_font_color(self, item, color):
        """Update the font color of an item."""
        item.font_color = color
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
                return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
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
        new_dimension = JsonTreeItem([name, "🔴", ""], self.rootItem)
        self.rootItem.appendChild(new_dimension)
        self.layoutChanged.emit()

    def removeRow(self, row, parent=QModelIndex()):
        """Allow removing dimensions."""
        parentItem = self.rootItem if not parent.isValid() else parent.internalPointer()
        parentItem.childItems.pop(row)
        self.layoutChanged.emit()

    def clear_layer_weightings(self, factor_item):
        """Clear all layer weightings under a factor."""
        for i in range(factor_item.childCount()):
            layer_item = factor_item.child(i)
            layer_item.setData(2, "0.00")  # Set weighting to 0.00
        factor_item.setData(2, "0.00")
        self.update_font_color(factor_item, QColor(Qt.red))  # Set factor font to red (invalid)
        self.layoutChanged.emit()

    def auto_assign_layer_weightings(self, factor_item):
        """Auto-assign equal weightings across all layers under a factor."""
        num_layers = factor_item.childCount()
        if num_layers == 0:
            return
        layer_weighting = 1 / num_layers
        for i in range(num_layers):
            layer_item = factor_item.child(i)
            layer_item.setData(2, f"{layer_weighting:.2f}")  # Evenly distribute weightings
        factor_item.setData(2, "1.00")
        self.update_font_color(factor_item, QColor(Qt.green))  # Set factor font to green (valid)
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
        self.original_value = model.data(index, Qt.DisplayRole)  # Store original value before editing
        return super().edit(index, trigger, event)

    def keyPressEvent(self, event):
        """Handle Escape key to cancel editing."""
        if event.key() == Qt.Key_Escape and self.current_editing_index:
            self.model().setData(self.current_editing_index, self.original_value, Qt.EditRole)
            self.closeEditor(self.current_editor(), QAbstractItemDelegate.RevertModelCache)
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
        if hint == QAbstractItemDelegate.RevertModelCache and self.current_editing_index:
            self.model().setData(self.current_editing_index, self.original_value, Qt.EditRole)
        self.current_editing_index = None
        self.original_value = None
        super().closeEditor(editor, hint)

class MainWindow(QMainWindow):
    def __init__(self, json_file):
        super().__init__()

        self.json_file = json_file
        self.setWindowTitle("JSON Model Viewer with Editable Weightings")
        layout = QVBoxLayout()

        # Load JSON data
        self.load_json()

        # Create a CustomTreeView widget to handle editing and reverts
        self.treeView = CustomTreeView()
        self.treeView.setDragDropMode(QTreeView.InternalMove)
        self.treeView.setDefaultDropAction(Qt.MoveAction)

        # Create a model for the QTreeView using custom JsonTreeModel
        self.model = JsonTreeModel(self.json_data)
        self.treeView.setModel(self.model)

        self.treeView.setEditTriggers(QTreeView.DoubleClicked)  # Only allow editing on double-click

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

        # Set layout
        layout.addWidget(self.treeView)

        # Add a button bar at the bottom with a Close button and Add Dimension button
        button_bar = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)

        add_dimension_button = QPushButton("Add Dimension")
        add_dimension_button.clicked.connect(self.add_dimension)

        button_bar.addWidget(add_dimension_button)
        button_bar.addStretch()
        button_bar.addWidget(close_button)
        layout.addLayout(button_bar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Maximize the window on start
        self.showMaximized()

        # Set up QFileSystemWatcher to monitor changes in the JSON file
        self.file_watcher = QFileSystemWatcher([self.json_file])
        self.file_watcher.fileChanged.connect(self.on_file_changed)

    def load_json(self):
        """Load the JSON data from the file."""
        with open(self.json_file, 'r') as f:
            self.json_data = json.load(f)

    def on_file_changed(self):
        """Reload the JSON data when the file changes and update the model."""
        print(f"Detected change in {self.json_file}. Reloading model...")
        self.load_json()
        self.model.loadJsonData(self.json_data)
        self.treeView.expandAll()

    def add_dimension(self):
        """Add a new dimension to the model."""
        self.model.add_dimension()

    def open_context_menu(self, position: QPoint):
        """Handle right-click context menu."""
        index = self.treeView.indexAt(position)
        if not index.isValid():
            return

        item = index.internalPointer()

        # Check if item is a factor or layer
        is_factor = item.parent() is not None and item.childCount() > 0  # Factors have children
        is_layer = item.parent() is not None and item.childCount() == 0  # Layers are leaf nodes

        menu = QMenu(self)

        if is_factor:
            # Context menu for factors
            clear_action = QAction("Clear Layer Weightings", self)
            auto_assign_action = QAction("Auto Assign Layer Weightings", self)
            add_to_map_action = QAction("Add Factor Layers to Map", self)

            # Connect actions
            clear_action.triggered.connect(lambda: self.model.clear_layer_weightings(item))
            auto_assign_action.triggered.connect(lambda: self.model.auto_assign_layer_weightings(item))
            add_to_map_action.triggered.connect(lambda: QMessageBox.information(self, "Info", "Feature not implemented yet."))

            # Add actions to menu
            menu.addAction(clear_action)
            menu.addAction(auto_assign_action)
            menu.addAction(add_to_map_action)

        elif is_layer:
            # Context menu for layers
            show_properties_action = QAction("Show Properties", self)
            balance_weighting_action = QAction("Balance Weighting", self)

            # Connect actions
            show_properties_action.triggered.connect(lambda: self.show_layer_properties(item))
            balance_weighting_action.triggered.connect(lambda: self.model.balance_weighting(item))

            # Add actions to menu
            menu.addAction(show_properties_action)
            menu.addAction(balance_weighting_action)

        # Show the menu at the cursor's position
        menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def show_layer_properties(self, item):
        """Open a dialog showing layer properties."""
        layer_name = item.data(0)
        layer_data = item.data(3)  # Assumes layer details are stored in position 3
        dialog = LayerDetailDialog(layer_name, layer_data, self)
        dialog.exec_()

class LayerDetailDialog(QDialog):
    """Dialog to show layer properties."""
    def __init__(self, layer_name, layer_data, parent=None):
        super().__init__(parent)

        self.setWindowTitle(layer_name)

        layout = QVBoxLayout()

        # Heading for the dialog
        heading_label = QLabel(layer_name)
        layout.addWidget(heading_label)

        # Description for the dialog
        description_text = QTextEdit(layer_data)
        description_text.setReadOnly(True)
        layout.addWidget(description_text)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)

# Main function to run the application
def main():
    app = QApplication(sys.argv)

    # Set default JSON path
    cwd = os.getcwd()
    default_json_file = os.path.join(cwd, 'model.json')

    # Check if model.json exists, otherwise prompt for a JSON file
    json_file = default_json_file if os.path.exists(default_json_file) else None
    if not json_file:
        json_file, _ = QFileDialog.getOpenFileName(None, "Open JSON File", cwd, "JSON Files (*.json);;All Files (*)")
        if not json_file:
            QMessageBox.critical(None, "Error", "No JSON file selected!")
            return

    # Set the application style to "kvantum" after QApplication instance
    app.setStyle("kvantum")

    # Launch the main window
    window = MainWindow(json_file)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
