from functools import partial
import os

from Qt.QtWidgets import QWidget,QTableWidgetItem,QPushButton,QHBoxLayout,QCheckBox,QLineEdit,QLabel
from Qt.QtCore import Qt,QTimer,QObject
from Qt.QtGui import QPixmap

import mtoa.utils as au
import maya.cmds as m

from LightManagerUI import CustomLineEditNum

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))


class MayaLightLogic(QObject):
    
    def __init__(self,ui):
        super().__init__()
        self.ui = ui
        self.maya_path = os.environ.get('MAYA_LOCATION')
        self.script_jobs = [] # JOB ID COLLECTOR
        self.lightTypes = {
            "aiPhotometricLight": None,
            "aiSkyDomeLight": None,
            "aiAreaLight": None,
            "spotLight": m.spotLight,
            "pointLight": m.pointLight,
            "directionalLight": m.directionalLight,
            }

    def rename_light(self,old_name:str, new_name:str,light_table:object):
        try:
            m.rename(old_name, "LGT_"+new_name+"_000")          # RENAME WITH A NANING CONVENTION
            self.refresh(light_table)
            self.info_timer(f"Light: '{old_name}' renamed to 'LGT_{new_name}_000'")
        except ValueError as e:
            self.info_timer(f"Error: Wrong input - {e}")
        
    def refresh(self,light_table:object):
        # KILL ALL EXISTING SCRIPTS JOB TO PREVENT ERRORS WITH DELETED WIDGETS
        for job_id in self.script_jobs:
            if m.scriptJob(exists=job_id):
                m.scriptJob(kill=job_id, force=True)
        self.script_jobs.clear()
        light_table.setRowCount(0) # CLEAR EXISTING ROWS
        
        # REPOPULATE THE TABLE
        all_lights =  [m.ls(type=Ltype) for Ltype in self.lightTypes]
        for shapes in all_lights:
            if shapes:
                for lightshape in shapes:
                    node_type = m.nodeType(lightshape)
                    transform = m.listRelatives(lightshape, parent=True)[0]
                    if node_type in self.lightTypes:
                        self.light_name_to_list(lightshape, transform,light_table)
                        self.mute_solo_to_list(transform,light_table)
                        self.colorButton_to_list(transform,light_table)
                        self.entry_attrNum_to_list(transform,"aiExposure",5,light_table)
                        self.entry_attrNum_to_list(transform,"aiSamples",6,light_table)
                        self.Entry_attrText_to_list(f"{lightshape}.aiAov",7,light_table)
                        self.info_timer("Light Manager refreshed successfully.")
                    else:
                        self.info_timer(f"'{transform}' is not allowed by the manager - warning {node_type}")
                        pass
        m.select(clear=True)

    def delete(self,light_table:object):
        selection = m.ls(selection=True, dagObjects=True)
        m.delete(selection)
        self.refresh(light_table)
        self.info_timer(f"Light  '{selection[0]}' deleted successfully.")

    # DESIGN THE WAY TO SELECT LIGHTS IN TABLE
    def lightTable_selection(self,lightTable:object):
        selected_items = lightTable.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            light_name_item = lightTable.item(row, 0)
            if light_name_item:
                try:
                    light_name = light_name_item.text()
                    m.select(clear=True)
                    m.select(light_name)
                except ValueError as e:
                    self.info_timer(f"Error:  '{light_name}' None Existent")
        else:
            m.select(clear=True)
            
    def create_light(self,light_name:str, light_type:str,light_table:object):
        if light_type not in self.lightTypes:
            self.info_timer(f"Error: Light type '{light_type}' is invalid or not selected in the ComboBox.")
            return None
        lightType_key = light_type
        func = self.lightTypes[lightType_key]  # PREBUILD MAYA LIGHT CREATION  COMMAND LINE 
        
        if not light_name.strip():
            light_name = "defaultLight"

        naming_convention = f"LGT_{light_name.upper()}_000" 
        light_transform = None
        
        # ARNOLD LIGHT 
        if lightType_key in ["aiAreaLight", "aiSkyDomeLight","aiPhotometricLight"]:
            light_nodes = au.createLocator(lightType_key, asLight=True)
            light_transform = m.rename(light_nodes[1], naming_convention)
        else:
            # MAYALIGHT
            light_shape = func(name=naming_convention)
            light_transform = m.ls(selection=True, long=True)[0][1:]
            
        if not light_transform or not m.objExists(light_transform):
            self.info_timer(f"Failed to create light: {naming_convention}")
            return None

        light_shape_nodes = m.listRelatives(light_transform, shapes=True, fullPath=True)
        
        if not light_shape_nodes:
            self.info_timer(f"Could not find shape node for {light_name}")
            return None
            
        light_shape = light_shape_nodes[0]
        
        # POPULATE THE TABLE LIST
        self.light_name_to_list(light_shape, light_transform,light_table)
        self.mute_solo_to_list(light_transform,light_table)
        self.colorButton_to_list(light_transform,light_table)
        self.entry_attrNum_to_list(light_transform,"aiSamples",6,light_table)
        self.entry_attrNum_to_list(light_transform,"aiExposure",5,light_table)
        self.Entry_attrText_to_list(f"{light_shape}.aiAov",7,light_table)

        self.info_timer(f"'{lightType_key}': '{light_name}' has been created successfully.")

    def light_name_to_list(self, light_shape_name:str, light_transform_name:str, light_table:object):
        self.row_position = light_table.rowCount()
        light_table.insertRow(self.row_position)

        # POPULATE THE "Name" COLUMN
        name_item = QTableWidgetItem(light_transform_name)
        name_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        light_table.setItem(self.row_position, 0, name_item)

        # POPULATE THE "Light Type" COLUMN
        light_type = m.nodeType(light_shape_name)
        icon_light_type = QLabel()
        
        if light_type in ["aiAreaLight", "aiSkyDomeLight","aiPhotometricLight"]:
            icon_path = os.path.join(SCRIPT_PATH, "img", "icons", f"{light_type[2:]}Shelf.png")
        else:
            icon_path = os.path.join(SCRIPT_PATH, "img", "icons", f"{light_type}.png")
            print(icon_path)
        
        img = QPixmap(icon_path)
        icon_light_type.setPixmap(img)
        icon_light_type.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        light_table.setCellWidget(self.row_position, 3, icon_light_type)

    # MUTE AND SOLO CHECKBOX, ONE WIDGET BY CELL
    def mute_solo_to_list(self, light_transform_name:int,light_table:object):
        mute_widget = QWidget()
        mute_checkbox = QCheckBox()
        mute_checkbox.setStyleSheet("QCheckBox::indicator:unchecked { background-color: #f94144 }")
        current_visibility = m.getAttr(f"{light_transform_name}.visibility")
        mute_checkbox.setChecked(bool(current_visibility))
        mute_checkbox.stateChanged.connect(partial(self.update_all_lights_visibility,light_table))
        mute_layout = QHBoxLayout(mute_widget)
        mute_layout.addWidget(mute_checkbox)
        mute_layout.setAlignment(Qt.AlignCenter)
        mute_layout.setContentsMargins(0,0,0,0)
        
        solo_widget = QWidget()
        solo_checkbox = QCheckBox()
        solo_checkbox.setStyleSheet("QCheckBox::indicator:checked { background-color: #adb5bd }")
        solo_checkbox.stateChanged.connect(partial(self.on_solo_toggled, self.row_position,light_table))
        solo_layout = QHBoxLayout(solo_widget)
        solo_layout.addWidget(solo_checkbox)
        solo_layout.setAlignment(Qt.AlignCenter)
        solo_layout.setContentsMargins(0,0,0,0)
        
        light_table.setCellWidget(self.row_position, 1, mute_widget)
        light_table.setCellWidget(self.row_position, 2, solo_widget)
    
    #  COLOR PALETTE CONTROLLER
    def colorButton_to_list(self, light_transform_name:str,light_table:object):
        colorBtn_widget = QWidget()
        colorBtn = QPushButton()
        colorBtn.setFixedSize(40, 20)
        self.setButtonColor(light_transform_name, colorBtn)
        colorBtn.clicked.connect(partial(self.setColor,light_transform_name,colorBtn))
        colorBtn_layout = QHBoxLayout(colorBtn_widget)
        colorBtn_layout.addWidget(colorBtn)
        colorBtn_layout.setAlignment(Qt.AlignCenter)
        colorBtn_layout.setContentsMargins(0,0,0,0)
        light_table.setCellWidget(self.row_position, 4, colorBtn_widget)
    
    # GENERATE AN EDITABLE SECTION FOR ATTRIBUTE --> Float
    def entry_attrNum_to_list(self, light_transform_name:str,attribute_name:str,column:int,light_table:object):
        full_attr_name = f"{light_transform_name}.{attribute_name}"
        current_value = m.getAttr(full_attr_name)
        bar_text = CustomLineEditNum()                             # SETTING THE CURRENT VALUE IN THE UI
        if isinstance(current_value, (float)):
            bar_text.setText(f"{current_value:.3f}")
        elif isinstance(current_value, (int)):
            bar_text.setText(f"{current_value}")
        bar_text.setFixedSize(74, 29)
        bar_text.setAlignment(Qt.AlignCenter)
        bar_text.setContentsMargins(0,0,0,0)
        
        def _update_maya_from_ui():
            try:
                new_value = float(bar_text.text())             # GET VALUE FROM UI
                m.setAttr(full_attr_name, new_value)             # SET VALUE IN MAYA
            except (ValueError, RuntimeError) as e:
                self.info_timer(f"Wrong input:  Please enter a number")
                # ON ERROR, Reset the text to the current value in MAYA
                current_maya_val = m.getAttr(full_attr_name)
                if isinstance(current_maya_val, (float)):
                    bar_text.setText(f"{current_maya_val:.3f}")
                elif isinstance(current_maya_val, (int)):
                    bar_text.setText(f"{current_maya_val}")
        bar_text.returnPressed.connect(_update_maya_from_ui)

        def _update_ui_from_maya(*args):
            if not m.objExists(light_transform_name):
                return 
            bar_text.blockSignals(True)                # AVOIDING AN INFINITE LOOP BETWEEN THE UI AND MAYA
            try:
                new_value = m.getAttr(full_attr_name)
                if isinstance(new_value, (float)):
                    bar_text.setText(f"{new_value:.3f}") 
                elif isinstance(new_value, (int)):
                    bar_text.setText(f"{new_value}")
            finally:
                bar_text.blockSignals(False)          # RE-ESTABLISHE THE SIGNAL

        # CREATE A SCRIPT JOB TO LISTEN FOR CHANGES AND STORE ID FOR CLEANUP
        job_id = m.scriptJob(attributeChange=[full_attr_name, _update_ui_from_maya])
        self.script_jobs.append(job_id)
        light_table.setCellWidget(self.row_position, column, bar_text)

    # GENERATE AN EDITABLE SECTION FOR ATTRIBUTE --> String
    def Entry_attrText_to_list(self, light_shape_name:str,column:int,light_table:object):
        full_attr_name = f"{light_shape_name}"
        current_value = m.getAttr(full_attr_name)
        bar_text = QLineEdit(placeholderText=current_value)
        bar_text.setFixedSize(59, 29)
        bar_text.setAlignment(Qt.AlignCenter)
        bar_text.setContentsMargins(0,0,0,0)
        
        def _update_maya_from_ui():
            try:
                new_value = bar_text.text()
                m.setAttr(full_attr_name, new_value, type='string')
                self.info_timer(f"{light_shape_name} set to AOV: '{new_value}'")
            except (ValueError, RuntimeError) as e:
                self.info_timer(f"Invalid input : {e}")
                # ON ERROR, Reset the text to the current value in MAYA
                current_maya_val = m.getAttr(full_attr_name)
                bar_text.setText(current_maya_val)
        bar_text.returnPressed.connect(_update_maya_from_ui)

        def _update_ui_from_maya(*args:str):
            if not m.objExists(light_shape_name):
                return 
            bar_text.blockSignals(True)                     #  AVOIDING AN INFINITE LOOP BETWEEN THE UI AND MAYA
            try:
                new_value = m.getAttr(full_attr_name)
                bar_text.setText(new_value)
            finally:
                bar_text.blockSignals(False)

        # CREATE A SCRIPT JOB TO LISTEN FOR CHANGES AND STORE ID FOR CLEANUP
        job_id = m.scriptJob(attributeChange=[full_attr_name, _update_ui_from_maya])
        self.script_jobs.append(job_id)
        light_table.setCellWidget(self.row_position, column, bar_text)

    def on_solo_toggled(self, toggled_row:int,light_table:object,state:bool):
        """Ensures only one solo checkbox is active at a time and updates the scene."""
        if state:
            for i in range(light_table.rowCount()):                  # SKIP the ROW OF THE CHECKBOX THAT WAS JUST TOGGLED
                if i != toggled_row:
                    solo_widget = light_table.cellWidget(i, 2)
                    if solo_widget:
                        solo_checkbox = solo_widget.findChild(QCheckBox)    # RETRIEVE THE CUSTOM WIDGET IN THE  'Solo' COLUMN
                        if solo_checkbox and solo_checkbox.isChecked():     # PREVENT RECURSIVE CALLS OF THIS FUNCTION
                            solo_checkbox.blockSignals(True)
                            solo_checkbox.setChecked(False)                 # UNCHECKED THE PREVIOUS SOLOED CHECKBOX
                            solo_checkbox.blockSignals(False)
        self.update_all_lights_visibility(light_table)

    def update_all_lights_visibility(self,light_table:object, *args:str):
        """Updates the visibility of all lights based on the UI state (solo or mute)."""
        soloed_row = -1
        # CHECK IF ANY LIGHT IS SOLOED
        for i in range(light_table.rowCount()):
            solo_widget = light_table.cellWidget(i, 2)
            if solo_widget:
                solo_checkbox = solo_widget.findChild(QCheckBox)
                if solo_checkbox and solo_checkbox.isChecked():
                    soloed_row = i                        # IF A SOLO CHECKBOX IS FOUND AND CHECKED, STORE ITS ROW INDEX
                    break

        # ITERATE THROUGH ALL LIGHTS TO SET THEIR VISIBILITY
        for i in range(light_table.rowCount()):
            light_name_item = light_table.item(i, 0)
            mute_widget = light_table.cellWidget(i, 1)
            
            if not (light_name_item and mute_widget):
                continue
            
            light_name = light_name_item.text()
            if not m.objExists(light_name):
                continue
            mute_checkbox = mute_widget.findChild(QCheckBox)

            if m.objExists(light_name) and mute_checkbox:
                is_visible = (i == soloed_row) if soloed_row != -1 else mute_checkbox.isChecked()
                m.setAttr(f"{light_name}.visibility", is_visible) # SET THE VISIBILITY OF THE CORRESPONDING LIGHT IN MAYA.
    
    # GET THE LIGHT COLOR VALUE 
    def setColor(self,light_name:str,color_button:QPushButton):
        if not isinstance(light_name, str) or not m.objExists(light_name):
            self.info_timer(f"Error: Light '{light_name}' does not exist or is invalid.")
            return
        
        lightColor = m.getAttr(light_name + ".color")[0]        #  GET THE ACTUAL LIGHT COLOR 
        color = m.colorEditor(rgbValue=lightColor)              # OPEN MAYA COLOR EDITOR
        r, g, b, a = [float(c) for c in color.split()]          #  RGB in string values 
        m.setAttr(light_name + ".color", r, g, b, type="double3") # SET THE COLOR IN MAYA
        self.setButtonColor(light_name,color_button,(r, g, b))
    
    def setButtonColor(self,light_name:int,color_button:QPushButton, color:tuple=None):
        if not isinstance(light_name, str) or not m.objExists(light_name):
            self.info_timer(f"Error:  '{light_name}' does not exist or is invalid.")
            return

        if not color: # IF NOT, GET COLOR FROM MAYA
            color = m.getAttr(light_name + ".color")[0]
        if not isinstance(color, tuple):
            self.info_timer( f"Error:  Invalid color format for '{light_name}': {color}")
            return
        r, g, b = [c * 255 for c in color]
        color_button.setStyleSheet(f"background-color: rgba({r},{g},{b}, 1.0)")
    
    def searchLight(self, *args:str|object):
        search_text = args[0]
        if not search_text:
            self.refresh(args[1])
            return
        if search_text:
            for row in range(args[1].rowCount()):
                researsh_light = args[1].item(row, 0).text()
                if search_text in researsh_light.lower():
                    args[1].showRow(row)
                else:
                    args[1].hideRow(row)
                    
    def render(self):
        m.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
        m.arnoldRenderView(mode="open")
        
    def info_timer(self,text:str, duration_ms:int=3500):
        self.ui.info_text.setText(text)
        QTimer.singleShot(duration_ms, lambda: self.ui.info_text.setText(""))
        
