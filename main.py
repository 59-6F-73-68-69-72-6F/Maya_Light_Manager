"""
Lighting Manager Tool for Maya

Provides a PySide widget to manage lights within a Maya scene.
Allows users to create, delete, modify (visibility, intensity, color),
solo.
"""

from shiboken2 import wrapInstance
from PySide2 import QtWidgets, QtCore
from PySide2.QtCore import QSize
from maya import OpenMayaUI as omui
import pymel.core as pm
from functools import partial


# --- Light Widget ---
class LightWidget(QtWidgets.QWidget):
    
    onSolo = QtCore.Signal(bool)

    def __init__(self, light):
        
        super(LightWidget, self).__init__()   
        self.light = light
        self.buildUI()



    def buildUI(self):
        
        """Creates the UI elements within the LightWidget."""
        layout = QtWidgets.QGridLayout(self)

        # Checkbox for light name and visibility toggle
        name = QtWidgets.QCheckBox(str(self.light.getTransform()))
        self.name = name
        
        # Set initial checked state based on light's visibility
        name.setChecked(self.light.visibility.get())
        
        # Connect the checkbox toggle signal to the light's visibility attribute
        name.toggled.connect(lambda val: self.light.visibility.set(val))
        layout.addWidget(name, 0, 0)

        # Solo button
        solo = QtWidgets.QPushButton('Solo')
        solo.setCheckable(True)
        
        # Emit the onSolo signal when the solo button is toggled
        solo.toggled.connect(lambda val: self.onSolo.emit(val))
        layout.addWidget(solo, 0, 1)

        # Delete button
        delete = QtWidgets.QPushButton('X')
        delete.clicked.connect(self.deleteLight)
        delete.setMaximumWidth(20)
        layout.addWidget(delete, 0, 2)

        # Light Intensity
        intensity = QtWidgets.QLineEdit(self, text=str(self.light.aiExposure.get()))
        intensity.setMaximumWidth(110)
        intensity.returnPressed.connect(lambda: self.light.aiExposure.set(float(intensity.text())))
        
        layout.addWidget(intensity, 1, 0, 1, 2)

        # Color picker button
        self.colorBtn = QtWidgets.QPushButton()
        self.colorBtn.setMaximumWidth(60)
        self.colorBtn.setMaximumHeight(20)
        self.setButtonColor()
        self.colorBtn.clicked.connect(self.setColor)
        layout.addWidget(self.colorBtn, 1, 2)

        # Set the size policy to prevent the widget from expanding unnecessarily
        self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)


    # Disables or enables the light's visibility checkbox.
    def disableLight(self, val):
        self.name.setChecked(not bool(val))


    def deleteLight(self):
        """Deletes the light from the scene and removes the widget."""
        
        self.setParent(None)
        self.setVisible(False) # Hide the widget
        self.deleteLater() # Schedule the widget for deletion
        pm.delete(self.light.getTransform()) # Delete the corresponding light node (transform) in Maya

    def setColor(self):
        """Opens the Maya color editor to set the light's color."""
        # Get the current color of the light
        lightColor = self.light.color.get()
        # Open Maya's color editor, pre-filled with the current color
        color = pm.colorEditor(rgbValue=lightColor)
        # Parse the returned color string
        r, g, b, a = [float(c) for c in color.split()]
        color = (r, g, b)
        self.light.color.set(color)
        self.setButtonColor(color)

    def setButtonColor(self, color=None):
        # sets the color on the color picker button
        # If no color is provided, get the color from the light
        if not color:
            color = self.light.color.get()

        assert len(color) == 3, "You must provide a list of 3 colors"
        # Convert normalized color values (0-1) to 0-255 range for CSS
        r, g, b = [c * 255 for c in color]

        # Set the button's background color using a CSS stylesheet
        self.colorBtn.setStyleSheet(f"background-color: rgba({r},{g},{b}, 1.0)")


# --- Main Lighting Manager Window ---
class LightingManager(QtWidgets.QWidget):
    """
    Main widget for the Lighting Manager tool.
    Displays a list of LightWidgets, allows creation of new lights,
    and provides save/import/refresh functionality.
    """
    
    lightTypes = {
        "Point Light": pm.pointLight,
        "Spot Light": pm.spotLight,
        "Area Light": partial(pm.shadingNode, 'areaLight', asLight=True),
        "Directional Light": pm.directionalLight,
        "Volume Light": partial(pm.shadingNode, 'volumeLight', asLight=True)
    }

    def __init__(self, dock=False):
            
        parent = None
        
        # Initialize the QWidget part of this class
        super(LightingManager, self).__init__(parent=parent)

        # Build the main UI elements
        self.buildUI()
        self.populate()
        
    def buildUI(self):
        """Creates the main UI elements for the Lighting Manager window."""
        layout = QtWidgets.QGridLayout(self)

        # Dropdown for selecting light type to create
        self.lightTypeCB = QtWidgets.QComboBox()
        for lightType in sorted(self.lightTypes):
            self.lightTypeCB.addItem(lightType)
        layout.addWidget(self.lightTypeCB, 0, 0, 1, 2)

        # Button to create a new light
        createBtn = QtWidgets.QPushButton('Create')
        createBtn.clicked.connect(self.createLight)
        layout.addWidget(createBtn, 0, 2)

        # Scroll area setup for holding the LightWidgets
        scrollWidget = QtWidgets.QWidget()
        scrollWidget.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.scrollLayout = QtWidgets.QVBoxLayout(scrollWidget) # vertical layout
        
        # The scroll area itself
        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(scrollWidget)
        layout.addWidget(scrollArea, 1, 0, 1, 3)
        
        # Button to refresh the list of lights from the scene
        refreshBtn = QtWidgets.QPushButton('Refresh')
        refreshBtn.clicked.connect(self.refresh)
        layout.addWidget(refreshBtn, 2, 2)


    def refresh(self):
       
        # Clear existing LightWidgets from the scroll layout
        while self.scrollLayout.count():
            widget = self.scrollLayout.takeAt(0).widget()
            if widget:
                widget.setVisible(False)
                widget.deleteLater()
        self.populate()


    def populate(self):
        """Finds all lights in the current scene and adds LightWidgets for them."""
        # List all nodes of the specified light types in the scene
        for light in pm.ls(type=["areaLight", "spotLight", "pointLight", "directionalLight", "volumeLight"]):
            # Add a corresponding LightWidget for each found light
            self.addLight(light)

    def createLight(self, lightType=None, add=True):
        actual_light_type_key = lightType
        
        # # If lightType is not provided (e.g., when called by button click),
        # # get the currently selected type from the ComboBox.
        if actual_light_type_key is None or not isinstance(actual_light_type_key, str):
            actual_light_type_key = self.lightTypeCB.currentText()

        if actual_light_type_key not in self.lightTypes:
            print(f"Error: Light type '{actual_light_type_key}' is invalid or not selected in the ComboBox.")
            return None  # Or handle error more gracefully
            
        func = self.lightTypes[actual_light_type_key]
        light = func()
        self.refresh()

    def addLight(self, light):
        widget = LightWidget(light)
        widget.onSolo.connect(self.isolate)
        self.scrollLayout.addWidget(widget)

    def isolate(self, val):
        """
        Handles the soloing of a light. When a light is soloed, all other lights are temporarily hidden.
        """
        # Find all LightWidget instances within this manager
        lightWidgets = self.findChildren(LightWidget)
        for widget in lightWidgets:
            if widget != self.sender():
                # Disable (uncheck) its visibility checkbox if soloing (val is True)
                widget.disableLight(val)


# --- Maya Integration Utilities ---
ui = None

def getMayaMainWindow():
    global ui
    ui = LightingManager()
    ui.show()
    return ui


        
getMayaMainWindow()
