from functools import partial
import os

from Qt.QtWidgets import QWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QCheckBox, QLineEdit, QLabel
from Qt.QtCore import Qt, QTimer, QObject
from Qt.QtGui import QPixmap

import mtoa.utils as au
import maya.cmds as m

from LightManagerUI import CustomLineEditNum

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))


class MayaLightLogic(QObject):

    def __init__(self, ui):
        """
        Initializes the logic for the Light Manager.
        Args:
            ui (LightManagerUI): An instance of the UI class to which this logic will connect.
        """
        super().__init__()
        self.ui = ui
        self.maya_path = os.environ.get('MAYA_LOCATION')
        self.script_jobs = []  # JOB ID COLLECTOR
        self.lightTypes = {
            "aiPhotometricLight": None,
            "aiSkyDomeLight": None,
            "aiAreaLight": None,
            "spotLight": m.spotLight,
            "pointLight": m.pointLight,
            "directionalLight": m.directionalLight,
        }

    def rename_light(self, old_name: str, new_name: str, light_table: object):
        """
        Renames a light in the Maya scene with a specific naming convention.

        Args:
            old_name (str): The current name of the light to rename.
            new_name (str): The new base name for the light.
            light_table (QTableWidget): The table widget to refresh after renaming.
        """
        try:
            # RENAME WITH A NANING CONVENTION
            m.rename(old_name, "LGT_"+new_name+"_000")
        except ValueError as e:
            self.info_timer(f"Error: Wrong input - {e}")
        self.refresh(light_table)
        self.info_timer(f"Light: '{old_name}' renamed to 'LGT_{new_name}_000'")

    def refresh(self, light_table: object):
        """
        Clears and repopulates the entire UI table with lights from the Maya scene.

        This is the main function for synchronizing the UI with the scene. It first
        kills all previously created scriptJobs to prevent errors, then finds all
        lights matching the allowed types, and for each light, it populates a row
        in the table with all the necessary widgets and callbacks.

        Args:
            light_table (QTableWidget): The table widget to refresh.
        """
        # KILL ALL EXISTING SCRIPTS JOB TO PREVENT ERRORS WITH DELETED WIDGETS
        for job_id in self.script_jobs:
            if m.scriptJob(exists=job_id):
                m.scriptJob(kill=job_id, force=True)
        self.script_jobs.clear()
        light_table.setRowCount(0)  # CLEAR EXISTING ROWS

        # REPOPULATE THE TABLE
        all_lights = [m.ls(type=Ltype) for Ltype in self.lightTypes]
        for shapes in all_lights:
            if shapes:
                for lightshape in shapes:
                    node_type = m.nodeType(lightshape)
                    transform = m.listRelatives(lightshape, parent=True)[0]
                    if node_type in self.lightTypes:
                        self.light_name_to_list(
                            lightshape, transform, light_table)
                        self.mute_solo_to_list(transform, light_table)
                        self.color_button_to_list(transform, light_table)
                        self.entry_attr_num_to_list(transform, "aiExposure", 5, light_table)
                        self.entry_attr_num_to_list(transform, "aiSamples", 6, light_table)
                        self.entry_attr_text_to_list(f"{lightshape}.aiAov", 7, light_table)
                        self.info_timer("Light Manager refreshed successfully.")
                    else:
                        self.info_timer(f"'{transform}' is not allowed by the manager - warning {node_type}")
                        pass
        m.select(clear=True)

    def delete(self, light_table: object):
        """
        Deletes the currently selected light from the Maya scene.
        Args:
            light_table (QTableWidget): The table widget to refresh after deletion.
        """
        selection = m.ls(selection=True, dagObjects=True)
        m.delete(selection)
        self.refresh(light_table)
        self.info_timer(f"Light  '{selection[0]}' deleted successfully.")

    def light_table_selection(self, lightTable: object):
        """
        Synchronizes the Maya scene selection with the UI table selection.

        When a user selects an item in the table, this function selects the
        corresponding light node in the Maya scene.

        Args:
            lightTable (QTableWidget): The table widget where the selection changed.
        """
        selected_items = lightTable.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            light_name_item = lightTable.item(row, 0)
            if light_name_item:
                light_name = light_name_item.text()
                m.select(clear=True)
                try:
                    m.select(light_name)
                except ValueError as e:
                    self.info_timer(f"Error:  '{light_name}' None Existent")
        else:
            m.select(clear=True)

    def create_light(self, light_name: str, light_type: str, light_table: object):
        """
        Creates a new light in the Maya scene based on UI inputs.

        It handles both standard Maya lights and Arnold lights, applies a naming
        convention, and then populates the UI table with the new light's information.

        Args:
            light_name (str): The base name for the new light.
            light_type (str): The type of light to create (e.g., 'spotLight', 'aiAreaLight').
            light_table (QTableWidget): The table to update with the new light.
        """
        if light_type not in self.lightTypes:
            self.info_timer(f"Error: Light type '{light_type}' is invalid or not selected in the ComboBox.")
            return None
        lightType_key = light_type
        # PREBUILD MAYA LIGHT CREATION  COMMAND LINE
        func = self.lightTypes[lightType_key]

        if not light_name.strip():
            light_name = "defaultLight"

        naming_convention = f"LGT_{light_name.upper()}_000"
        light_transform = None

        # ARNOLD LIGHT
        if lightType_key in ["aiAreaLight", "aiSkyDomeLight", "aiPhotometricLight"]:
            light_nodes = au.createLocator(lightType_key, asLight=True)
            light_transform = m.rename(light_nodes[1], naming_convention)
        else:
            # MAYALIGHT
            light_shape = func(name=naming_convention)
            light_transform = m.ls(selection=True, long=True)[0][1:]

        if not light_transform or not m.objExists(light_transform):
            self.info_timer(f"Failed to create light: {naming_convention}")
            return

        light_shape_nodes = m.listRelatives(
            light_transform, shapes=True, fullPath=True)

        if not light_shape_nodes:
            self.info_timer(f"Could not find shape node for {light_name}")
            return

        light_shape = light_shape_nodes[0]

        # POPULATE THE TABLE LIST
        self.light_name_to_list(light_shape, light_transform, light_table)
        self.mute_solo_to_list(light_transform, light_table)
        self.color_button_to_list(light_transform, light_table)
        self.entry_attr_num_to_list(light_transform, "aiSamples", 6, light_table)
        self.entry_attr_num_to_list(light_transform, "aiExposure", 5, light_table)
        self.entry_attr_text_to_list(f"{light_shape}.aiAov", 7, light_table)

        self.info_timer(f"'{lightType_key}': '{light_name}' has been created successfully.")

    def light_name_to_list(self, light_shape_name: str, light_transform_name: str, light_table: object):
        """
        Populates the 'Name' and 'Light Type' columns for a new row in the table.

        Args:
            light_shape_name (str): The name of the light's shape node.
            light_transform_name (str): The name of the light's transform node.
            light_table (QTableWidget): The table to add the row to.
        """
        self.row_position = light_table.rowCount()
        light_table.insertRow(self.row_position)

        # POPULATE THE "Name" COLUMN
        name_item = QTableWidgetItem(light_transform_name)
        name_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        light_table.setItem(self.row_position, 0, name_item)

        # POPULATE THE "Light Type" COLUMN
        light_type = m.nodeType(light_shape_name)
        icon_light_type = QLabel()

        if light_type in ["aiAreaLight", "aiSkyDomeLight", "aiPhotometricLight"]:
            icon_path = os.path.join(SCRIPT_PATH, "img", "icons", f"{light_type[2:]}Shelf.png")
        else:
            icon_path = os.path.join(SCRIPT_PATH, "img", "icons", f"{light_type}.png")
            print(icon_path)

        img = QPixmap(icon_path)
        icon_light_type.setPixmap(img)
        icon_light_type.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        light_table.setCellWidget(self.row_position, 3, icon_light_type)

    def mute_solo_to_list(self, light_transform_name: int, light_table: object):
        """
        Adds 'Mute' and 'Solo' checkboxes to the current row in the table.

        Args:
            light_transform_name (str): The name of the light's transform node.
            light_table (QTableWidget): The table to add the widgets to.
        """
        mute_widget = QWidget()
        mute_checkbox = QCheckBox()
        mute_checkbox.setStyleSheet("QCheckBox::indicator:unchecked { background-color: #f94144 }")
        current_visibility = m.getAttr(f"{light_transform_name}.visibility")
        mute_checkbox.setChecked(bool(current_visibility))
        mute_checkbox.stateChanged.connect(partial(self.update_all_lights_visibility, light_table))
        mute_layout = QHBoxLayout(mute_widget)
        mute_layout.addWidget(mute_checkbox)
        mute_layout.setAlignment(Qt.AlignCenter)
        mute_layout.setContentsMargins(0, 0, 0, 0)

        solo_widget = QWidget()
        solo_checkbox = QCheckBox()
        solo_checkbox.setStyleSheet("QCheckBox::indicator:checked { background-color: #adb5bd }")
        solo_checkbox.stateChanged.connect(partial(self.on_solo_toggled, self.row_position, light_table))
        solo_layout = QHBoxLayout(solo_widget)
        solo_layout.addWidget(solo_checkbox)
        solo_layout.setAlignment(Qt.AlignCenter)
        solo_layout.setContentsMargins(0, 0, 0, 0)

        light_table.setCellWidget(self.row_position, 1, mute_widget)
        light_table.setCellWidget(self.row_position, 2, solo_widget)

    def color_button_to_list(self, light_transform_name: str, light_table: object):
        """
        Adds a color swatch button to the current row in the table.

        Args:
            light_transform_name (str): The name of the light's transform node.
            light_table (QTableWidget): The table to add the widget to.
        """
        colorBtn_widget = QWidget()
        colorBtn = QPushButton()
        colorBtn.setFixedSize(40, 20)
        self.set_button_color(light_transform_name, colorBtn)
        colorBtn.clicked.connect(partial(self.set_color, light_transform_name, colorBtn))
        colorBtn_layout = QHBoxLayout(colorBtn_widget)
        colorBtn_layout.addWidget(colorBtn)
        colorBtn_layout.setAlignment(Qt.AlignCenter)
        colorBtn_layout.setContentsMargins(0, 0, 0, 0)
        light_table.setCellWidget(self.row_position, 4, colorBtn_widget)

    def entry_attr_num_to_list(self, light_transform_name: str, attribute_name: str, column: int, light_table: object):
        """
        Adds a numeric input field to a cell for a specific attribute.

        This creates a two-way binding: changes in the UI update Maya, and
        changes in Maya (via a scriptJob) update the UI.

        Args:
            light_transform_name (str): The light's transform node name.
            attribute_name (str): The name of the numeric attribute to control (e.g., 'aiExposure').
            column (int): The table column index to place this widget in.
            light_table (QTableWidget): The table to add the widget to.
        """
        full_attr_name = f"{light_transform_name}.{attribute_name}"
        current_value = m.getAttr(full_attr_name)
        # SETTING THE CURRENT VALUE IN THE UI
        bar_text = CustomLineEditNum()
        if isinstance(current_value, (float)):
            bar_text.setText(f"{current_value:.3f}")
        elif isinstance(current_value, (int)):
            bar_text.setText(f"{current_value}")
        bar_text.setFixedSize(74, 29)
        bar_text.setAlignment(Qt.AlignCenter)
        bar_text.setContentsMargins(0, 0, 0, 0)

        def _update_maya_from_ui():
            # GET VALUE FROM UI
            try:
                # SET VALUE IN MAYA
                new_value = float(bar_text.text())
                m.setAttr(full_attr_name, new_value)
            except (ValueError, RuntimeError) as e:
                self.info_timer(f"Wrong input:  Please enter a number")
                # ON ERROR, Reset the text to the current value in MAYA
                current_maya_val = m.getAttr(full_attr_name)
                if isinstance(current_maya_val, (float)):
                    bar_text.setText(f"{current_maya_val:.3f}")
                elif isinstance(current_maya_val, (int)):
                    bar_text.setText(f"{current_maya_val}")
        bar_text.returnPressed.connect(_update_maya_from_ui)

        def _update_ui_from_maya(*_: str):
            if not m.objExists(light_transform_name):
                return
            # AVOIDING AN INFINITE LOOP BETWEEN THE UI AND MAYA
            bar_text.blockSignals(True)
            new_value = m.getAttr(full_attr_name)
            try:
                if isinstance(new_value, (float)):
                    bar_text.setText(f"{new_value:.3f}")
                elif isinstance(new_value, (int)):
                    bar_text.setText(f"{new_value}")
            finally:
                # RE-ESTABLISHE THE SIGNAL
                bar_text.blockSignals(False)

        # CREATE A SCRIPT JOB TO LISTEN FOR CHANGES AND STORE ID FOR CLEANUP
        job_id = m.scriptJob(attributeChange=[full_attr_name, _update_ui_from_maya])
        self.script_jobs.append(job_id)
        light_table.setCellWidget(self.row_position, column, bar_text)

    def entry_attr_text_to_list(self, light_shape_name: str, column: int, light_table: object):
        """
        Adds a text input field to a cell for a specific string attribute.

        This creates a two-way binding: changes in the UI update Maya, and
        changes in Maya (via a scriptJob) update the UI.

        Args:
            light_shape_name (str): The light's shape node name (including attribute).
            column (int): The table column index to place this widget in.
            light_table (QTableWidget): The table to add the widget to.
        """
        full_attr_name = f"{light_shape_name}"
        current_value = m.getAttr(full_attr_name)
        bar_text = QLineEdit(placeholderText=current_value)
        bar_text.setFixedSize(59, 29)
        bar_text.setAlignment(Qt.AlignCenter)
        bar_text.setContentsMargins(0, 0, 0, 0)

        def _update_maya_from_ui():
            new_value = bar_text.text()
            try:
                m.setAttr(full_attr_name, new_value, type='string')
                self.info_timer(
                    text=f"{light_shape_name.split('.')[0].split('|')[2]} set AOV: '{new_value}'")
            except (ValueError, RuntimeError) as e:
                self.info_timer(f"Invalid input : {e}")
                # ON ERROR, Reset the text to the current value in MAYA
                current_maya_val = m.getAttr(full_attr_name)
                bar_text.setText(current_maya_val)
        bar_text.returnPressed.connect(_update_maya_from_ui)

        def _update_ui_from_maya(*_: str):
            if not m.objExists(light_shape_name):
                return
            # AVOIDING AN INFINITE LOOP BETWEEN THE UI AND MAYA
            bar_text.blockSignals(True)
            new_value = m.getAttr(full_attr_name)
            try:
                bar_text.setText(new_value)
            finally:
                bar_text.blockSignals(False)

        # CREATE A SCRIPT JOB TO LISTEN FOR CHANGES AND STORE ID FOR CLEANUP
        job_id = m.scriptJob(attributeChange=[full_attr_name, _update_ui_from_maya])
        self.script_jobs.append(job_id)
        light_table.setCellWidget(self.row_position, column, bar_text)

    def on_solo_toggled(self, toggled_row: int, light_table: object, state: bool):
        """
        Callback for when a 'Solo' checkbox is toggled.

        It ensures only one light can be soloed at a time. When a box is checked,
        it unchecks any other currently soloed box, then triggers a visibility update.

        Args:
            toggled_row (int): The row index of the checkbox that was changed.
            light_table (QTableWidget): The table containing the widgets.
            state (bool): The new state of the checkbox (True if checked).
        """
        if state:
            # SKIP the ROW OF THE CHECKBOX THAT WAS JUST TOGGLED
            for i in range(light_table.rowCount()):
                if i != toggled_row:
                    solo_widget = light_table.cellWidget(i, 2)
                    if solo_widget:
                        # RETRIEVE THE CUSTOM WIDGET IN THE  'Solo' COLUMN
                        solo_checkbox = solo_widget.findChild(QCheckBox)
                        if solo_checkbox and solo_checkbox.isChecked():     # PREVENT RECURSIVE CALLS OF THIS FUNCTION
                            solo_checkbox.blockSignals(True)
                            # UNCHECKED THE PREVIOUS SOLOED CHECKBOX
                            solo_checkbox.setChecked(False)
                            solo_checkbox.blockSignals(False)
        self.update_all_lights_visibility(light_table)

    def update_all_lights_visibility(self, light_table: object, *args: str):
        """
        Updates the visibility of all lights based on the UI's Mute/Solo states.

        Logic:
        1. Checks if any light is currently soloed.
        2. If a light is soloed, it makes only that light visible.
        3. If no light is soloed, it sets each light's visibility based on its
           own 'Mute' checkbox state.

        Args:
            light_table (QTableWidget): The table containing the Mute/Solo widgets.
            *args: Catches any extra arguments passed by Qt signals.
        """
        soloed_row = -1
        # CHECK IF ANY LIGHT IS SOLOED
        for i in range(light_table.rowCount()):
            solo_widget = light_table.cellWidget(i, 2)
            if solo_widget:
                solo_checkbox = solo_widget.findChild(QCheckBox)
                if solo_checkbox and solo_checkbox.isChecked():
                    # IF A SOLO CHECKBOX IS FOUND AND CHECKED, STORE ITS ROW INDEX
                    soloed_row = i
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
                # SET THE VISIBILITY OF THE CORRESPONDING LIGHT IN MAYA.
                m.setAttr(f"{light_name}.visibility", is_visible)

    def set_color(self, light_name: str, color_button: QPushButton):
        """
        Opens the Maya color editor to set a light's color.

        Args:
            light_name (str): The name of the light to modify.
            color_button (QPushButton): The button in the UI whose color will be updated.
        """
        if not isinstance(light_name, str) or not m.objExists(light_name):
            self.info_timer(f"Error: Light '{light_name}' does not exist or is invalid.")
            return

        # GET THE ACTUAL LIGHT COLOR
        lightColor = m.getAttr(light_name + ".color")[0]
        # OPEN MAYA COLOR EDITOR
        color = m.colorEditor(rgbValue=lightColor)
        r, g, b, a = [float(c) for c in color.split()]  # RGB in string values
        m.setAttr(light_name + ".color", r, g, b, type="double3")  # SET THE COLOR IN MAYA
        self.set_button_color(light_name, color_button, (r, g, b))

    def set_button_color(self, light_name: int, color_button: QPushButton, color: tuple = None):
        """
        Sets the background color of a button to match a light's color.

        Args:
            light_name (str): The name of the light to get the color from.
            color_button (QPushButton): The UI button to update.
            color (tuple, optional): The RGB color to set. If None, it's fetched from Maya.
        """
        if not isinstance(light_name, str) or not m.objExists(light_name):
            self.info_timer(f"Error:  '{light_name}' does not exist or is invalid.")
            return

        if not color:  # IF NOT, GET COLOR FROM MAYA
            color = m.getAttr(light_name + ".color")[0]
        if not isinstance(color, tuple):
            self.info_timer(f"Error:  Invalid color format for '{light_name}': {color}")
            return
        r, g, b = [c * 255 for c in color]
        color_button.setStyleSheet(f"background-color: rgba({r},{g},{b}, 1.0)")

    def search_light(self, *args: str | object):
        """
        Filters the visibility of rows in the table based on a search string.

        Args:
            args[0] (str): The text to search for in the light names.
            args[1] (QTableWidget): The table whose rows will be filtered.
        """
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
        """ Sets the current renderer to Arnold and opens the Arnold Render View. """

        m.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
        m.arnoldRenderView(mode="open")

    def info_timer(self, text: str, duration_ms: int = 3500):
        """
        Displays a message in the UI's info label for a specified duration.

        Args:
            text (str): The message to display.
            duration_ms (int, optional): How long to display the message in milliseconds. Defaults to 3500.
        """
        self.ui.info_text.setText(text)
        QTimer.singleShot(duration_ms, lambda: self.ui.info_text.setText(""))
