######################################################
# - MAYA LIGHT MANAGER -
# AUTHOR : RUDY LETI
# DATE : 06/26/2025
# DESIGNED TO SPEED UP LIGHTING PRODUCTION PROCESS
#
# .LIST THE MOST COMMON LIGHTS USED IN PRODUCTION (ARNOLD ORIENTED) IN THE SCENE ( CREATE,GATHER , RENAME AND DELETE LIGHTS)
# . NAMING CONVENTION INTEGRATED
# . LIGHTS SELECTABLE FROM THE UI
# . ALLOW TO MUTE OR SOLO LIGHTS
# . ALLOW QUICK MODIFICATION OF LIGHT COLOR,EXPOSURE
# . FILTERS LIGHTS BY TYPE (MAYA LIGHT, ARNOLD)
# . CLEAR AND EASY SAMPLES MANAGMENT
######################################################

from PySide2.QtWidgets import QWidget,QTableWidget,QTableWidgetItem,QComboBox,QLabel,QLineEdit,QPushButton,QVBoxLayout,QHBoxLayout,QCheckBox,QAbstractItemView,QMessageBox
from PySide2.QtGui import QFont,QPixmap
from PySide2.QtCore import Qt
from functools import partial
from maya import cmds as m
import mtoa.utils as ad

TABLE_HEADER = ["Name","M","S","LightType","Color","Exposure","Samples"]
HEADER_SIZE = [180,20,20,100,55,75,75]
FONT = "Nimbus Sans, Bold"
COLOR = "#c7c7c5"
FONT_WEIGHT = 600
FONT_SIZE = 11


class LightManager(QWidget):
    lightTypes = {
        "aiPhotometricLight":None,
        "aiSkyDomeLight": None,
        "aiAreaLight": None,
        "directionalLight": m.directionalLight,
        "pointLight": m.pointLight,
        "spotLight": m.spotLight,
        }

    def __init__(self):
        super().__init__()
        self.buildUI()
        self.script_jobs = [] # JOB ID COLLECTOR

    # SET WINDOW --------------------------------------------
    def buildUI(self):
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # KEEP WINDOW ON TOP
        self.setWindowTitle("Maya Light Manager")
        self.setMinimumSize(600,800)
        self.setMaximumSize(600,1000)
        layoutV = QVBoxLayout(self)
        
        self.Qlabel = QLabel()
        img = QPixmap("/img/logo.png")
        self.Qlabel.setPixmap(img)
        
        title_lightName = self.label_text("Light Name:")
        self.entry_lightName = self.bar_text("name your light  (key,rim...etc")
        title_lightType = self.label_text("Light Type:")
        self.combo_lightType = self.combo_list(self.lightTypes) # COMBO BOX DRIVEN BY DICT
        
        button_createlight = self.push_button("Create Light")
        button_createlight.clicked.connect(self.create_light)
        button_createlight.setStyleSheet(" background-color: #2a9d8f ; color: black;")
        
        button_refresh = self.push_button("Refresh")
        button_refresh.clicked.connect(self.refresh)
        button_refresh.setStyleSheet(" background-color: #8ecae6 ; color: black;")
        
        button_renamer = self.push_button("Light Renamer")
        button_renamer.clicked.connect(self.rename_light)
        button_renamer.setStyleSheet(" background-color: #D17D98 ; color: white;")
        
        button_delete = self.push_button("Delete")
        button_delete.clicked.connect(self.delete)
        button_delete.setStyleSheet(" background-color: #c1121f ; color: white;")
        
        title_lightList = self.label_text("Light List:")
        
        self.lightTable = QTableWidget()
        self.lightTable.setSelectionMode(QAbstractItemView.SingleSelection) #SELECT ONLY ONE ROW AT A TIME
        self.lightTable.setEditTriggers(QAbstractItemView.NoEditTriggers) # MAKE CELLS NON-EDITABLE
        self.lightTable.setStyleSheet("QTableWidget { background-color: #222b33 ; color: white; }")
        for y in range(7):
            self.lightTable.setColumnCount(y+1)
            self.lightTable.setHorizontalHeaderLabels(TABLE_HEADER)
            header = self.lightTable.horizontalHeader()
            header.resizeSection(y,HEADER_SIZE[y])
        self.lightTable.itemSelectionChanged.connect(self.lightTable_selection)
        
        layoutV.addWidget(self.Qlabel)
        layoutV.addWidget(title_lightName)
        layoutV.addWidget(self.entry_lightName)
        layoutV.addWidget(button_renamer)
        layoutV.addWidget(title_lightType)
        layoutV.addWidget(self.combo_lightType)
        layoutV.addWidget(title_lightList)
        layoutV.addWidget(button_createlight)
        layoutV.addWidget(self.lightTable)
        layoutV.addWidget(button_refresh)
        layoutV.addWidget(button_delete)
        
    # GENERIC WIDGETS --------------------------------------------
    def label_text(self,text):
        label = QLabel(text=text)
        label.setFont(QFont(FONT,FONT_SIZE))
        label.setStyleSheet(f"color:{COLOR}")
        return label

    def bar_text(self,text=None):
        line_edit = QLineEdit(placeholderText=text)
        line_edit.setFont(QFont(FONT,FONT_SIZE))
        return line_edit

    def combo_list(self,light_list):
        combo_box = QComboBox()
        for light in sorted(light_list):
            combo_box.addItem(light)
            combo_box.setFont(QFont(FONT,FONT_SIZE))
        return combo_box

    def push_button(self,text):
        button = QPushButton(text)
        button.setFont(QFont(FONT,FONT_SIZE))
        return button

    # FUNCTIONS --------------------------------------------

    def rename_light(self):
        if self.lightTable.selectedItems():
            selection = m.ls(selection=True)[0]
            try:
                new_name = self.entry_lightName.text()
                m.rename(selection, "LGT_"+new_name+"_000") # RENAME WITH A NANING CONVENTION
                self.entry_lightName.clear()
                self.refresh()
            except RuntimeError as e:
                pass

    def refresh(self):
        # KILL ALL EXISTING SCRIPTS JOB TO PREVENT ERRORS WITH DELETED WIDGETS
        for job_id in self.script_jobs:
            if m.scriptJob(exists=job_id):
                m.scriptJob(kill=job_id, force=True)
        self.script_jobs.clear()
        self.lightTable.setRowCount(0) # CLEAR EXISTING ROWS
        
        # REPOPULATE THE TABLE
        all_lights =  [m.ls(type=Ltype) for Ltype in self.lightTypes]
        for shapes in all_lights:
            if shapes:
                for lightshape in shapes:
                    node_type = m.nodeType(lightshape)
                    transform = m.listRelatives(lightshape, parent=True)[0]
                    if node_type in self.lightTypes:
                        self.light_name_to_list(lightshape, transform)
                        self.mute_solo_to_list(transform)
                        self.colorButton_to_list(transform)
                        self.entry_to_list(transform,"aiExposure",5)
                        self.entry_to_list(transform,"aiSamples",6)
                    else:
                        print(f"'{transform}' is not allowed by the manager - warning {node_type}")
                        pass
        m.select(clear=True)

    def delete(self):
       if self.lightTable.selectedItems():
        selection = m.ls(selection=True, dagObjects=True)
        btn_question = QMessageBox.question(self,"Question", f"Are you sure you want to delete {selection[0]} ?")
        if btn_question == QMessageBox.Yes:
            m.delete(selection)
            self.refresh()
        else:
            pass

    # DESIGN THE WAY TO SELECT LIGHTS IN TABLE
    def lightTable_selection(self):
        selected_items = self.lightTable.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            light_name_item = self.lightTable.item(row, 0)
            if light_name_item:
                try:
                    light_name = light_name_item.text()
                    m.select(clear=True)
                    m.select(light_name)
                except ValueError as e:
                    print(f"Error: {e}")
        else:
            m.select(clear=True)
            
    def create_light(self,lightType = None):
        if lightType is None or not isinstance(lightType,str):
            lightType = self.combo_lightType.currentText()
               
        if lightType == "pointLight" or lightType == "spotLight" or lightType == "directionalLight":
            lightType_key = lightType
        elif lightType == "aiAreaLight" or lightType == "aiSkyDomeLight"  or lightType == "aiPhotometricLight":
            lightType_key = lightType
        else:
            print(f"Error: Unexpected light type '{lightType}'.")
            return None
           
        if lightType not in self.lightTypes:
            print(f"Error: Light type '{lightType}' is invalid or not selected in the ComboBox.")
            return None

        func = self.lightTypes[lightType_key]  # PREBUILD MAYA LIGHT CREATION  COMMAND LINE 
        light_name = self.entry_lightName.text()
        
        if not light_name.strip():
            light_name = "defaultLight"

        naming_convention = f"LGT_{light_name.upper()}_000" 
        light_transform = None
        
        # ARNOLD LIGHT 
        if lightType_key in ["aiAreaLight", "aiSkyDomeLight","aiPhotometricLight"]:
            light_nodes = ad.createLocator(lightType_key, asLight=True)
            light_transform = m.rename(light_nodes[1], naming_convention)
            
        # elif lightType_key == "aiMeshLight":
        #     light_nodes = ad.createMeshLight()
        #     selection = m.ls(selection=True)
        #     light_transform = m.rename(selection, naming_convention)
        
        else:
            # MAYALIGHT  -  returns the transform
            light_shape = func(name=naming_convention)
            light_transform = m.ls(selection=True, long=True)[0][1:]
            
        if not light_transform or not m.objExists(light_transform):
            print(f"Failed to create light: {naming_convention}")
            return None

        light_shape_nodes = m.listRelatives(light_transform, shapes=True, fullPath=True)
        
        if not light_shape_nodes:
            print(f"Could not find shape node for {light_transform}")
            return None
            
        light_shape = light_shape_nodes[0]
        
        # POPULATE THE TABLE LIST
        self.light_name_to_list(light_shape, light_transform)
        self.mute_solo_to_list(light_transform)
        self.colorButton_to_list(light_transform)
        self.entry_to_list(light_transform,"aiExposure",5)
        self.entry_to_list(light_transform,"aiSamples",6)
        self.entry_lightName.clear()
        

    def light_name_to_list(self, light_shape_name, light_transform_name):
        self.row_position = self.lightTable.rowCount()
        self.lightTable.insertRow(self.row_position)

        # POPULATE THE "Name" COLUMN
        name_item = QTableWidgetItem(light_transform_name)
        name_item.setTextAlignment(Qt.AlignCenter)
        self.lightTable.setItem(self.row_position, 0, name_item)

        # POPULATE THE "Light Type" COLUMN
        light_type = m.nodeType(light_shape_name) # EXTRACT LIGHT TYPE FROM THE SHAPE NODE
        type_item = QTableWidgetItem(light_type)
        type_item.setTextAlignment(Qt.AlignCenter)
        self.lightTable.setItem(self.row_position, 3, type_item)

    # GENERATE WIDGET FOR MUTE AND SOLO CHECKBOX, ONE WIDGET BY CELL
    def mute_solo_to_list(self, light_transform_name):
        mute_widget = QWidget()
        mute_checkbox = QCheckBox()
        mute_checkbox.setStyleSheet("QCheckBox::indicator:unchecked { background-color: #f94144 }")
        current_visibility = m.getAttr(f"{light_transform_name}.visibility")
        mute_checkbox.setChecked(bool(current_visibility))
        mute_checkbox.stateChanged.connect(self.update_all_lights_visibility)
        mute_layout = QHBoxLayout(mute_widget)
        mute_layout.addWidget(mute_checkbox)
        mute_layout.setAlignment(Qt.AlignCenter)
        mute_layout.setContentsMargins(0,0,0,0)
        
        solo_widget = QWidget()
        solo_checkbox = QCheckBox()
        solo_checkbox.setStyleSheet("QCheckBox::indicator:checked { background-color: #adb5bd }")
        solo_checkbox.stateChanged.connect(partial(self.on_solo_toggled, self.row_position))
        solo_layout = QHBoxLayout(solo_widget)
        solo_layout.addWidget(solo_checkbox)
        solo_layout.setAlignment(Qt.AlignCenter)
        solo_layout.setContentsMargins(0,0,0,0)
        
        self.lightTable.setCellWidget(self.row_position, 1, mute_widget)
        self.lightTable.setCellWidget(self.row_position, 2, solo_widget)
    
    #  GENERATE A WIDGET COLOR PALETTE CONTROLLER
    def colorButton_to_list(self, light_transform_name):
        colorBtn_widget = QWidget()
        colorBtn = QPushButton()
        colorBtn.setFixedSize(40, 20)
        self.setButtonColor(light_transform_name, colorBtn)
        colorBtn.clicked.connect(partial(self.setColor,light_transform_name,colorBtn))
        colorBtn_layout = QHBoxLayout(colorBtn_widget)
        colorBtn_layout.addWidget(colorBtn)
        colorBtn_layout.setAlignment(Qt.AlignCenter)
        colorBtn_layout.setContentsMargins(0,0,0,0)
        self.lightTable.setCellWidget(self.row_position, 4, colorBtn_widget)
    
    # GENERATE AN EDITABLE SECTION FOR ATTRIBUTE
    def entry_to_list(self, light_transform_name,attribute_name,column):
        full_attr_name = f"{light_transform_name}.{attribute_name}"
        current_value = m.getAttr(full_attr_name)
        bar_text = self.bar_text(text=f"{current_value:.3f}")
        bar_text.setFixedSize(74, 29)
        bar_text.setAlignment(Qt.AlignCenter)
        bar_text.setContentsMargins(0,0,0,0)
        
        def update_maya_from_ui():
            try:
                new_value = float(bar_text.text()) # GET VALUE FROM UI
                m.setAttr(full_attr_name, new_value) # SET VALUE IN MAYA
            except (ValueError, RuntimeError) as e:
                print(f"Invalid input : {e}")
                # ON ERROR, Reset the text to the current value in MAYA
                current_maya_val = m.getAttr(full_attr_name)
                bar_text.setText(f"{current_maya_val:.3f}") # SETTING THE VALUE IN THE UI

        bar_text.returnPressed.connect(update_maya_from_ui)

        def update_ui_from_maya(*args):
            if not m.objExists(light_transform_name):
                return 
            bar_text.blockSignals(True) #  AVOIDING AN INFINITE LOOP BETWEEN THE UI AND MAYA TRY TO UPDATE EACH OTHER
            try:
                new_value = m.getAttr(full_attr_name) # GET VALUE FROM MAYA
                bar_text.setText(f"{new_value:.3f}") # SETTING THE VALUE IN THE UI
            finally:
                bar_text.blockSignals(False) # RE-ESTABLISHE THE SIGNAL

        # CREATE A SCRIPT JOB TO LISTEN FOR CHANGES AND STORE ID FOR CLEANUP
        job_id = m.scriptJob(attributeChange=[full_attr_name, update_ui_from_maya])
        self.script_jobs.append(job_id)
        self.lightTable.setCellWidget(self.row_position, column, bar_text)

    def on_solo_toggled(self, toggled_row, state):
        """Ensures only one solo checkbox is active at a time and updates the scene."""
        if state:
            for i in range(self.lightTable.rowCount()): # SKIP the ROW OF THE CHECKBOX THAT WAS JUST TOGGLED
                if i != toggled_row:
                    solo_widget = self.lightTable.cellWidget(i, 2)
                    if solo_widget:
                        solo_checkbox = solo_widget.findChild(QCheckBox)  # RETRIEVE THE CUSTOM WIDGET IN THE  'Solo' COLUMN
                        if solo_checkbox and solo_checkbox.isChecked(): # PREVENT RECURSIVE CALLS OF THIS FUNCTION
                            solo_checkbox.blockSignals(True)
                            solo_checkbox.setChecked(False) # UNCHECKED THE PREVIOUS SOLOED CHECKBOX
                            solo_checkbox.blockSignals(False)
        self.update_all_lights_visibility()

    
    def update_all_lights_visibility(self):
        """Updates the visibility of all lights based on the UI state (solo or mute)."""
        soloed_row = -1
        # CHECK IF ANY LIGHT IS SOLOED
        for i in range(self.lightTable.rowCount()):
            solo_widget = self.lightTable.cellWidget(i, 2)
            if solo_widget:
                solo_checkbox = solo_widget.findChild(QCheckBox)
                if solo_checkbox and solo_checkbox.isChecked():
                    soloed_row = i  # IF A SOLO CHECKBOX IS FOUND AND CHECKED, STORE ITS ROW INDEX
                    break

        # ITERATE THROUGH ALL LIGHTS TO SET THEIR VISIBILITY
        for i in range(self.lightTable.rowCount()):
            light_name_item = self.lightTable.item(i, 0)
            mute_widget = self.lightTable.cellWidget(i, 1)
            
            if not (light_name_item and mute_widget):
                continue
            
            light_name = light_name_item.text()
            if not m.objExists(light_name): # CHECK IF LIGHT STILL EXISTS
                continue
            
            mute_checkbox = mute_widget.findChild(QCheckBox)

            if m.objExists(light_name) and mute_checkbox:
                is_visible = (i == soloed_row) if soloed_row != -1 else mute_checkbox.isChecked()
                m.setAttr(f"{light_name}.visibility", is_visible) # SET THE VISIBILITY ATTRIBUTE OF THE CORRESPONDING LIGHT IN MAYA.
    
    # GET THE LIGHT COLOR VALUE 
    def setColor(self,light_name,color_button):
        if not isinstance(light_name, str) or not m.objExists(light_name):
            print(f"Error: Light '{light_name}' does not exist or is invalid.")
            return
        
        lightColor = m.getAttr(light_name + ".color")[0] #  GET THE ACTUAL LIGHT COLOR 
        color = m.colorEditor(rgbValue=lightColor) # OPEN MAYA COLOR EDITOR AND PUT THE VALUE IN IT -(PICK A COLOR)
        r, g, b, a = [float(c) for c in color.split()] #  RGB in string values -  RETRIEVE THE COLOR IN RGB VALUE
        m.setAttr(light_name + ".color", r, g, b, type="double3") # SET THE COLOR IN MAYA
        self.setButtonColor(light_name,color_button,(r, g, b))
    
    # SET THE BUTTON COLOR
    def setButtonColor(self,light_name,color_button, color=None):
        if not isinstance(light_name, str) or not m.objExists(light_name):
            print(f"Error: Light '{light_name}' does not exist or is invalid.")
            return

        if not color: # IF NOT, GET COLOR FROM MAYA
            color = m.getAttr(light_name + ".color")[0]
        if not isinstance(color, tuple):
            print(f"Error: Invalid color format for light '{light_name}': {color}")
            return
        r, g, b = [c * 255 for c in color]
        color_button.setStyleSheet(f"background-color: rgba({r},{g},{b}, 1.0)")

# --- MAYA INTEGRATION UTILITIES ---
ui = None
def getMayaMainWindow():
    global ui
    ui = LightManager()
    ui.show()
    return ui
      
getMayaMainWindow()
