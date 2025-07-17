# VERSION CHECK
# This code is designed to work with Maya versions 2024 and earlier.

import maya.cmds as m

maya_version = m.about(version=True)
if int(maya_version) <= 2024:
    from PySide2.QtWidgets import QWidget,QTableWidgetItem,QPushButton,QHBoxLayout,QCheckBox,QMessageBox
    from PySide2.QtCore import Qt, QTimer
else:
    from PySide6.QtWidgets import QWidget,QTableWidgetItem,QPushButton,QHBoxLayout,QCheckBox,QMessageBox
    from PySide6.QtCore import Qt, QTimer

from LightManagerUI import CustomLineEdit
from functools import partial
import mtoa.utils as au



class MayaLightLogic():
    
    def __init__(self,ui):
        self.ui = ui
        self.script_jobs = [] # JOB ID COLLECTOR
        self.lightTypes = {
            "aiPhotometricLight": None,
            "aiSkyDomeLight": None,
            "aiAreaLight": None,
            "spotLight": m.spotLight,
            "pointLight": m.pointLight,
            "directionalLight": m.directionalLight,
            }


    def rename_light(self):
        if self.ui.lightTable.selectedItems():
            selection = m.ls(selection=True)[0]
            try:
                new_name = self.ui.entry_lightName.text()
                m.rename(selection, "LGT_"+new_name+"_000")          # RENAME WITH A NANING CONVENTION
                self.ui.entry_lightName.clear()
                self.refresh()
                self.info_timer(f"Light: '{selection}' renamed to 'LGT_{new_name}_000'")
            except RuntimeError as e:
                self.info_timer(f"Error: Wrong input - {e}")
        
    def refresh(self):
        # KILL ALL EXISTING SCRIPTS JOB TO PREVENT ERRORS WITH DELETED WIDGETS
        for job_id in self.script_jobs:
            if m.scriptJob(exists=job_id):
                m.scriptJob(kill=job_id, force=True)
        self.script_jobs.clear()
        self.ui.lightTable.setRowCount(0) # CLEAR EXISTING ROWS
        
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
                        self.entry_attrNum_to_list(transform,"aiExposure",5)
                        self.entry_attrNum_to_list(transform,"aiSamples",6)
                        self.Entry_attrText_to_list(f"{lightshape}.aiAov",7)
                        self.info_timer("Light Manager refreshed successfully.")
                    else:
                        self.info_timer(f"'{transform}' is not allowed by the manager - warning {node_type}")
                        pass
        m.select(clear=True)

    def delete(self):
       if self.ui.lightTable.selectedItems():
        selection = m.ls(selection=True, dagObjects=True)
        btn_question = QMessageBox.question(self.ui,"Question", f"Are you sure you want to delete {selection[0]} ?")
        if btn_question == QMessageBox.Yes:
            m.delete(selection)
            self.refresh()
            self.info_timer(f"Light  '{selection[0]}' deleted successfully.")
        else:
            pass

    # DESIGN THE WAY TO SELECT LIGHTS IN TABLE
    def lightTable_selection(self):
        selected_items = self.ui.lightTable.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            light_name_item = self.ui.lightTable.item(row, 0)
            if light_name_item:
                try:
                    light_name = light_name_item.text()
                    m.select(clear=True)
                    m.select(light_name)
                except ValueError as e:
                    self.info_timer(f"Error:  '{light_name}' None Existent")
        else:
            m.select(clear=True)
            
    def create_light(self,lightType = None):
        if lightType is None or not isinstance(lightType,str):
            lightType = self.ui.combo_lightType.currentText()
               
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
        light_name = self.ui.entry_lightName.text()
        
        if not light_name.strip():
            light_name = "defaultLight"

        naming_convention = f"LGT_{light_name.upper()}_000" 
        light_transform = None
        
        # ARNOLD LIGHT 
        if lightType_key in ["aiAreaLight", "aiSkyDomeLight","aiPhotometricLight"]:
            light_nodes = au.createLocator(lightType_key, asLight=True)
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
        self.entry_attrNum_to_list(light_transform,"aiSamples",6)
        self.entry_attrNum_to_list(light_transform,"aiExposure",5)
        self.Entry_attrText_to_list(f"{light_shape}.aiAov",7)
        
        self.ui.entry_lightName.clear()
        self.info_timer(f"Light '{lightType_key}' created successfully.")

    def light_name_to_list(self, light_shape_name, light_transform_name):
        self.row_position = self.ui.lightTable.rowCount()
        self.ui.lightTable.insertRow(self.row_position)

        # POPULATE THE "Name" COLUMN
        name_item = QTableWidgetItem(light_transform_name)
        name_item.setTextAlignment(Qt.AlignCenter)
        self.ui.lightTable.setItem(self.row_position, 0, name_item)

        # POPULATE THE "Light Type" COLUMN
        light_type = m.nodeType(light_shape_name)               # EXTRACT LIGHT TYPE FROM THE SHAPE NODE
        type_item = QTableWidgetItem(light_type)
        type_item.setTextAlignment(Qt.AlignCenter)
        self.ui.lightTable.setItem(self.row_position, 3, type_item)

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
        
        self.ui.lightTable.setCellWidget(self.row_position, 1, mute_widget)
        self.ui.lightTable.setCellWidget(self.row_position, 2, solo_widget)
    
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
        self.ui.lightTable.setCellWidget(self.row_position, 4, colorBtn_widget)
    
    # GENERATE AN EDITABLE SECTION FOR ATTRIBUTE --> Float
    def entry_attrNum_to_list(self, light_transform_name,attribute_name,column):
        full_attr_name = f"{light_transform_name}.{attribute_name}"
        current_value = m.getAttr(full_attr_name)
        bar_text = CustomLineEdit()                             # SETTING THE CURRENT VALUE IN THE UI
        if isinstance(current_value, (float)):
            bar_text.setText(f"{current_value:.3f}")
        elif isinstance(current_value, (int)):
            bar_text.setText(f"{current_value}")
        bar_text.setFixedSize(74, 29)
        bar_text.setAlignment(Qt.AlignCenter)
        bar_text.setContentsMargins(0,0,0,0)
        
        def update_maya_from_ui():
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


        bar_text.returnPressed.connect(update_maya_from_ui)

        def update_ui_from_maya(*args):
            if not m.objExists(light_transform_name):
                return 
            bar_text.blockSignals(True)                       # AVOIDING AN INFINITE LOOP BETWEEN THE UI AND MAYA TRY TO UPDATE EACH OTHER
            try:
                new_value = m.getAttr(full_attr_name)
                if isinstance(new_value, (float)):
                    bar_text.setText(f"{new_value:.3f}") 
                elif isinstance(new_value, (int)):
                    bar_text.setText(f"{new_value}")
            finally:
                bar_text.blockSignals(False)                 # RE-ESTABLISHE THE SIGNAL

        # CREATE A SCRIPT JOB TO LISTEN FOR CHANGES AND STORE ID FOR CLEANUP
        job_id = m.scriptJob(attributeChange=[full_attr_name, update_ui_from_maya])
        self.script_jobs.append(job_id)
        self.ui.lightTable.setCellWidget(self.row_position, column, bar_text)

    # GENERATE AN EDITABLE SECTION FOR ATTRIBUTE --> String
    def Entry_attrText_to_list(self, light_shape_name,column):
        full_attr_name = f"{light_shape_name}"
        current_value = m.getAttr(full_attr_name)
        bar_text = self.ui.bar_text(text=current_value)
        bar_text.setFixedSize(59, 29) 
        bar_text.setAlignment(Qt.AlignCenter)
        bar_text.setContentsMargins(0,0,0,0)
        
        def update_maya_from_ui():
            try:
                new_value = bar_text.text()
                m.setAttr(full_attr_name, new_value, type='string')
                self.info_timer(f"{light_shape_name} set to AOV: '{new_value}'")
            except (ValueError, RuntimeError) as e:
                self.info_timer(f"Invalid input : {e}")
                # ON ERROR, Reset the text to the current value in MAYA
                current_maya_val = m.getAttr(full_attr_name)
                bar_text.setText(current_maya_val)

        bar_text.returnPressed.connect(update_maya_from_ui)

        def update_ui_from_maya(*args):
            if not m.objExists(light_shape_name):
                return 
            bar_text.blockSignals(True)                     #  AVOIDING AN INFINITE LOOP BETWEEN THE UI AND MAYA
            try:
                new_value = m.getAttr(full_attr_name)
                bar_text.setText(new_value)
            finally:
                bar_text.blockSignals(False)                # RE-ESTABLISHE THE SIGNALE

        # CREATE A SCRIPT JOB TO LISTEN FOR CHANGES AND STORE ID FOR CLEANUP
        job_id = m.scriptJob(attributeChange=[full_attr_name, update_ui_from_maya])
        self.script_jobs.append(job_id)
        self.ui.lightTable.setCellWidget(self.row_position, column, bar_text)

    def on_solo_toggled(self, toggled_row, state):
        """Ensures only one solo checkbox is active at a time and updates the scene."""
        if state:
            for i in range(self.ui.lightTable.rowCount()):                  # SKIP the ROW OF THE CHECKBOX THAT WAS JUST TOGGLED
                if i != toggled_row:
                    solo_widget = self.ui.lightTable.cellWidget(i, 2)
                    if solo_widget:
                        solo_checkbox = solo_widget.findChild(QCheckBox)    # RETRIEVE THE CUSTOM WIDGET IN THE  'Solo' COLUMN
                        if solo_checkbox and solo_checkbox.isChecked():     # PREVENT RECURSIVE CALLS OF THIS FUNCTION
                            solo_checkbox.blockSignals(True)
                            solo_checkbox.setChecked(False)                 # UNCHECKED THE PREVIOUS SOLOED CHECKBOX
                            solo_checkbox.blockSignals(False)
        self.update_all_lights_visibility()

    
    def update_all_lights_visibility(self):
        """Updates the visibility of all lights based on the UI state (solo or mute)."""
        soloed_row = -1
        # CHECK IF ANY LIGHT IS SOLOED
        for i in range(self.ui.lightTable.rowCount()):
            solo_widget = self.ui.lightTable.cellWidget(i, 2)
            if solo_widget:
                solo_checkbox = solo_widget.findChild(QCheckBox)
                if solo_checkbox and solo_checkbox.isChecked():
                    soloed_row = i                        # IF A SOLO CHECKBOX IS FOUND AND CHECKED, STORE ITS ROW INDEX
                    break

        # ITERATE THROUGH ALL LIGHTS TO SET THEIR VISIBILITY
        for i in range(self.ui.lightTable.rowCount()):
            light_name_item = self.ui.lightTable.item(i, 0)
            mute_widget = self.ui.lightTable.cellWidget(i, 1)
            
            if not (light_name_item and mute_widget):
                continue
            
            light_name = light_name_item.text()
            if not m.objExists(light_name):               # CHECK IF LIGHT STILL EXISTS
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
        
        lightColor = m.getAttr(light_name + ".color")[0]        #  GET THE ACTUAL LIGHT COLOR 
        color = m.colorEditor(rgbValue=lightColor)              # OPEN MAYA COLOR EDITOR AND PUT THE VALUE IN IT -(PICK A COLOR)
        r, g, b, a = [float(c) for c in color.split()]          #  RGB in string values -  RETRIEVE THE COLOR IN RGB VALUE
        m.setAttr(light_name + ".color", r, g, b, type="double3") # SET THE COLOR IN MAYA
        self.setButtonColor(light_name,color_button,(r, g, b))
    
    # SET THE BUTTON COLOR
    def setButtonColor(self,light_name,color_button, color=None):
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
    
    def searchLight(self):
        search_text = self.ui.entry_lighSearch.text().lower()
        if not search_text:
            self.refresh()
            return
        if search_text:
            for row in range(self.ui.lightTable.rowCount()):
                researsh_light = self.ui.lightTable.item(row, 0).text()
                if search_text in researsh_light.lower():
                    self.ui.lightTable.showRow(row)
                else:
                    self.ui.lightTable.hideRow(row)
                    
    def render(self):
        m.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
        m.arnoldRenderView(mode="open")
        
    def info_timer(self,text, duration_ms=3000):
        self.ui.info_text.setText(text)
        QTimer.singleShot(duration_ms, lambda: self.ui.info_text.setText(""))
        