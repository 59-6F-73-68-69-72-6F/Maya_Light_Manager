"""
Lighting Manager Tool for Maya

Provides a PyQt widget to manage lights within a Maya scene.
Allows users to create, delete, modify (visibility, intensity, color),
solo, save, and import light setups.
"""

import json
import os
import time
import PyQt6
from numpy import long
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import pyqtSignal as Signal
from maya import OpenMayaUI as omui
import pymel.core as pm
import logging
from functools import partial
from sip import wrapinstance as wrapInstance


# Configure logging for the tool
logging.basicConfig()
logger = logging.getLogger('LightingManager')
logger.setLevel(logging.DEBUG)
logger.debug('Using sip')


# --- Light Widget ---
class LightWidget(QtWidgets.QWidget):
    
    onSolo = Signal(bool)

    def __init__(self, light):
        
        super(LightWidget, self).__init__()

        # Ensure 'light' is a PyNode object
        # If it's a string, convert it to a PyNode
        if isinstance(light,str):
            logger.debug('Converting node to a PyNode')
            light = pm.PyNode(light)
            
        if isinstance(light, pm.nodetypes.Transform):
            light = light.getShape()

        # Store the light shape node
        self.light = light
        # Build the UI elements for this light widget
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
        delete.setMaximumWidth(10)
        layout.addWidget(delete, 0, 2)

        # Intensity slider
        intensity = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        intensity.setMinimum(1)
        intensity.setMaximum(1000)
        # Set initial slider value based on light's intensity
        intensity.setValue(self.light.intensity.get())
        # Connect the slider's valueChanged signal to the light's intensity attribute
        intensity.valueChanged.connect(lambda val: self.light.intensity.set(val))
        layout.addWidget(intensity, 1, 0, 1, 2)

        # Color picker button
        self.colorBtn = QtWidgets.QPushButton()
        self.colorBtn.setMaximumWidth(20)
        self.colorBtn.setMaximumHeight(20)
        self.setButtonColor()
        self.colorBtn.clicked.connect(self.setColor)
        layout.addWidget(self.colorBtn, 1, 2)

        # Set the size policy to prevent the widget from expanding unnecessarily
        self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)


    def disableLight(self, val):
        # Disables or enables the light's visibility checkbox.
        self.name.setChecked(not bool(val))


    def deleteLight(self):
        """Deletes the light from the scene and removes the widget."""
        # Remove the widget from its parent layout
        self.setParent(None)
        # Hide the widget
        self.setVisible(False)
        # Schedule the widget for deletion
        self.deleteLater()
        # Delete the corresponding light node (transform) in Maya
        pm.delete(self.light.getTransform())

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
        # Determine the parent widget based on the dock flag
        if dock:
            parent = getDock()
        else:
            # If not docking, ensure any existing dock is deleted
            deleteDock()
            
            # Try to delete any existing standalone window with the same name
            try:
                pm.deleteUI('lightingManager')
            except:
                logger.debug('No previous UI exists')

            parent = QtWidgets.QDialog(parent=getMayaMainWindow())
            parent.setObjectName('lightingManager')
            # Set window properties if it's a standalone dialog
            parent.setWindowTitle('Lighting Manager')
            dlgLayout = QtWidgets.QVBoxLayout(parent)

        # Initialize the QWidget part of this class
        super(LightingManager, self).__init__(parent=parent)

        # Build the main UI elements
        self.buildUI()
        self.populate()
        self.parent().layout().addWidget(self)

        # If not docked, show parent
        if not dock:
            parent.show()

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


    def saveLights(self):
        """Saves the properties of all managed lights to a JSON file."""
        # Dictionary to store properties for each light
        properties = {}

        for lightWidget in self.findChildren(LightWidget):
            light = lightWidget.light
            transform = light.getTransform()

            properties[str(transform)] = {
                # Store transform attributes
                'translate': list(transform.translate.get()),
                'rotation': list(transform.rotate.get()),
                'lightType': pm.objectType(light),
                'intensity': light.intensity.get(),
                'color': light.color.get()
            }
        directory = self.getDirectory()
        
        # Construct the filename with a timestamp
        lightFile = os.path.join(directory, 'lightFile_%s.json' % time.strftime('%m%d'))


        with open(lightFile, 'w') as f:
            json.dump(properties, f, indent=4)

        logger.info('Saving file to %s' % lightFile)


    def getDirectory(self):
        
        # Gets or creates the directory for saving/loading light files.
        directory = os.path.join(pm.internalVar(userAppDir=True), 'lightManager')
        if not os.path.exists(directory):
            os.mkdir(directory)
        return directory


    def importLights(self):
        """Imports light properties from a JSON file."""
        
        directory = self.getDirectory()
        fileName = QtWidgets.QFileDialog.getOpenFileName(self, "Light Browser", directory)

        with open(fileName[0], 'r') as f:
            properties = json.load(f)

        # Iterate through the lights defined in the file
        for light, info in properties.items():
            lightType = info.get('lightType')
            
            # Find the corresponding creation function based on the stored lightType string
            for lt in self.lightTypes:
                if ('%sLight' % lt.split()[0].lower()) == lightType:
                    break
            else:
                logger.info('Cannot find a corresponding light type for %s (%s)' % (light, lightType))
                continue

            # Create a new light of the determined type, but don't add a widget yet
            light = self.createLight(lightType=lt)
            light.intensity.set(info.get('intensity'))
            light.color.set(info.get('color'))

            transform = light.getTransform()
            transform.translate.set(info.get('translate'))
            transform.rotate.set(info.get('rotation'))

        # Refresh the UI to show the newly imported lights
        self.populate()


    def createLight(self, lightType=None, add=True):

        if not lightType:
            lightType = self.lightTypeCB.currentText()

        func = self.lightTypes[lightType]
        light = func()
        
        # If requested, add a widget for the new light to the UI
        if add:
            self.addLight(light)

        return light

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
def getMayaMainWindow():
    win = omui.MQtUtil_mainWindow()
    ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr


def getDock(name='LightingManagerDock'):

    deleteDock(name)
    ctrl = pm.workspaceControl(name, dockToMainWindow=('right', 1), label="Lighting Manager")
    qtCtrl = omui.MQtUtil_findControl(ctrl)
    ptr = wrapInstance(long(qtCtrl), QtWidgets.QWidget)
    return ptr

def deleteDock(name='LightingManagerDock'):

    if pm.workspaceControl(name, query=True, exists=True):
        pm.deleteUI(name)
