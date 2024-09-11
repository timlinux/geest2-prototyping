#!/usr/bin/env python

import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QTreeView, QMainWindow, QVBoxLayout, QWidget, QFileDialog, QMessageBox, QHeaderView, QPushButton, QHBoxLayout, QDialog, QLabel, QLineEdit, QTextEdit
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt, QFileSystemWatcher, pyqtSlot

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
        super().__init__(parent)  # Updated initialization
        self.rootItem = JsonTreeItem(["Dimension/Factor/Layer", "Status", "Weighting"])
        self.json_data = json_data
        self.loadJsonData(json_data)

    def loadJsonData(self, json_data):
        """Load JSON data into the model, showing dimensions, factors, layers, and weightings."""
        self.beginResetModel()
        self.rootItem = JsonTreeItem(["Dimension/Factor/Layer", "Status", "Weighting"])  # Reset root

        # Only add dimensions, factors, and layers to the tree
        for dimension in json_data.get("dimensions", []):
            # Ensure dimensions are shown in Title Case
            dimension_name = dimension["name"].title()
            dimension_item = JsonTreeItem([dimension_name, "🔴", ""], self.rootItem)
            self.rootItem.appendChild(dimension_item)

            for factor in dimension.get("factors", []):
                factor_item = JsonTreeItem([factor["name"], "🔴", ""], dimension_item)
                dimension_item.appendChild(factor_item)

                # Calculate weighting for each layer
                num_layers = len(factor.get("layers", []))
                if num_layers == 0:
                    continue  # Skip factors without layers
                
                layer_weighting = 1 / num_layers  # Default weighting for each layer
                factor_weighting_sum = 0.0

                for layer in factor.get("layers", []):
                    for layer_name, layer_data in layer.items():
                        layer_item = JsonTreeItem([layer_name, "🔴", f"{layer_weighting:.2f}", layer_data], factor_item)  # Store layer_data
                        factor_item.appendChild(layer_item)
                        factor_weighting_sum += layer_weighting

                # Update factor weighting sum and style
                factor_weighting_text = f"{factor_weighting_sum:.2f}"
                factor_item.setData(2, factor_weighting_text)

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

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole and index.column() == 2:
            item = index.internalPointer()
            try:
                new_weighting = float(value)
                item.setData(2, f"{new_weighting:.2f}")

                # Recalculate factor sum if this is a layer's weighting
                parent_item = item.parent()
                if parent_item:
                    total_weighting = sum(
                        float(parent_item.child(i).data(2)) if parent_item.child(i).data(2) else 0.0
                        for i in range(parent_item.childCount())
                    )
                    parent_item.setData(2, f"{total_weighting:.2f}")
                    self.dataChanged.emit(index, index)

                return True
            except ValueError:
                return False

        return False

    def flags(self, index):
        """Make the layer weighting column editable."""
        if index.column() == 2 and index.internalPointer().parent():  # Only layers are editable
            return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

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

class LayerDetailDialog(QDialog):
    """Modal dialog that shows layer details."""
    def __init__(self, layer_name, layer_data, parent=None):
        super().__init__(parent)

        self.setWindowTitle(layer_name)
        self.setModal(True)

        layout = QVBoxLayout()

        # Heading
        heading = QLabel(f"Layer: {layer_name}")
        heading.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(heading)

        # Description (indicator text from JSON)
        description_label = QLabel("Description:")
        layout.addWidget(description_label)
        description = QTextEdit()
        description.setPlainText(layer_data.get('indicator', 'No description available.'))
        description.setReadOnly(True)
        layout.addWidget(description)

        # Source, aligned to the right
        source_label = QLabel(f"Source: {layer_data.get('source', 'Unknown')}")
        source_label.setAlignment(Qt.AlignRight)
        layout.addWidget(source_label)

        # Button bar with a close button
        button_bar = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_bar.addStretch()
        button_bar.addWidget(close_button)
        layout.addLayout(button_bar)

        self.setLayout(layout)
        self.resize(400, 300)

class MainWindow(QMainWindow):
    def __init__(self, json_file):
        super().__init__()

        self.json_file = json_file
        self.setWindowTitle("JSON Model Viewer with Editable Weightings")
        layout = QVBoxLayout()

        # Load JSON data
        self.load_json()

        # Create a QTreeView widget
        self.treeView = QTreeView()

        # Create a model for the QTreeView using custom JsonTreeModel
        self.model = JsonTreeModel(self.json_data)
        self.treeView.setModel(self.model)

        # Connect double-click signal to open the dialog
        self.treeView.doubleClicked.connect(self.on_item_double_clicked)

        # Expand the whole tree by default
        self.treeView.expandAll()

        # Set the second and third columns to the exact width of the 🔴 character and weighting
        self.treeView.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.treeView.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        # Expand the first column to use the remaining space and resize with the dialog
        self.treeView.header().setSectionResizeMode(0, QHeaderView.Stretch)

        # Set layout
        layout.addWidget(self.treeView)

        # Add a button bar at the bottom with a Close button
        button_bar = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
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

    @pyqtSlot(QModelIndex)
    def on_item_double_clicked(self, index):
        """Handle double-click on layer items to open the modal dialog."""
        item = index.internalPointer()
        if item and len(item.itemData) > 3:
            # The item contains the layer data (assumed to be stored in position 3)
            layer_name = item.data(0)
            layer_data = item.itemData[3]

            # Open the dialog with layer details
            dialog = LayerDetailDialog(layer_name, layer_data, self)
            dialog.exec_()

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

