#!/usr/bin/env python

import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QTreeView, QMainWindow, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QHeaderView
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt, QFileSystemWatcher

class JsonTreeItem:
    """A class representing a node in the tree."""
    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

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

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0

class JsonTreeModel(QAbstractItemModel):
    """Custom QAbstractItemModel to manage JSON data."""
    def __init__(self, json_data, parent=None):
        super(JsonTreeModel, self).__init__(parent)
        self.rootItem = JsonTreeItem(["Dimension/Factor/Layer", "Status"])
        self.loadJsonData(json_data)

    def loadJsonData(self, json_data):
        """Load JSON data into the model, only showing dimensions, factors, and layers."""
        self.beginResetModel()
        self.rootItem = JsonTreeItem(["Dimension/Factor/Layer", "Status"])  # Reset root

        # Only add dimensions, factors, and layers to the tree
        for dimension in json_data.get("dimensions", []):
            dimension_item = JsonTreeItem([dimension["name"], "🔴"], self.rootItem)
            self.rootItem.appendChild(dimension_item)
            for factor in dimension.get("factors", []):
                factor_item = JsonTreeItem([factor["name"], "🔴"], dimension_item)
                dimension_item.appendChild(factor_item)
                for layer in factor.get("layers", []):
                    # Assuming layers are stored as dictionaries with a single key (layer name)
                    for layer_name, layer_data in layer.items():
                        layer_item = JsonTreeItem([layer_name, "🔴"], factor_item)
                        factor_item.appendChild(layer_item)

        self.endResetModel()

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

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)

        return None

    def index(self, row, column, parent=QModelIndex()):
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
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

class MainWindow(QMainWindow):
    def __init__(self, json_file):
        super().__init__()

        self.json_file = json_file
        self.setWindowTitle("JSON Model Viewer with Dimensions, Factors, and Layers")
        layout = QVBoxLayout()

        # Load JSON data
        self.load_json()

        # Create a QTreeView widget
        self.treeView = QTreeView()

        # Create a model for the QTreeView using custom JsonTreeModel
        self.model = JsonTreeModel(self.json_data)
        self.treeView.setModel(self.model)

        # Expand the whole tree by default
        self.treeView.expandAll()

        # Set the second column to the exact width of the 🔴 character
        self.treeView.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.treeView.setColumnWidth(1, 25)  # Approximate width for the 🔴 character

        # Expand the first column to use the remaining space and resize with the dialog
        self.treeView.header().setSectionResizeMode(0, QHeaderView.Stretch)

        # Set layout
        layout.addWidget(self.treeView)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

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

# Main function to run the application
def main():
    # Set default JSON path
    cwd = os.getcwd()
    default_json_file = os.path.join(cwd, 'model.json')

    # Check if model.json exists, otherwise prompt for a JSON file
    json_file = default_json_file if os.path.exists(default_json_file) else None
    if not json_file:
        app = QApplication(sys.argv)
        json_file, _ = QFileDialog.getOpenFileName(None, "Open JSON File", cwd, "JSON Files (*.json);;All Files (*)")
        if not json_file:
            QMessageBox.critical(None, "Error", "No JSON file selected!")
            return

    # Launch the main window
    app = QApplication(sys.argv)
    window = MainWindow(json_file)
    window.show()
    sys.exit(app.exec_())

# Script execution entry point
if __name__ == "__main__":
    main()

