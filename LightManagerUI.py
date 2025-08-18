from Qt.QtCore import Qt, QSize, Signal
from Qt.QtGui import QFont, QWheelEvent
from Qt.QtWidgets import (QWidget, QTableWidget, QComboBox, QLabel, QLineEdit, QPushButton,
                          QVBoxLayout, QHBoxLayout, QAbstractItemView, QGroupBox, QApplication, QMessageBox)

from maya import cmds as m

TABLE_HEADER = ["Name", "M", "S", "Light",
                "Color", "Exposure", "Samples", "AOV"]
HEADER_SIZE = [160, 20, 20, 40, 55, 75, 75, 60]
FONT = "Nimbus Sans, Bold"
COLOR = "#c7c7c5"
FONT_WEIGHT = 600
FONT_SIZE = 11


class LightManagerUI(QWidget):
    """
    The main user interface for the Maya Light Manager.

    This class is responsible for building and displaying the GUI, which allows
    users to create, rename, delete, and manage lights in a Maya scene. It is
    built using Qt (via the Qt.py compatibility library).

    The UI is constructed in the `buildUI` method. It consists of input fields
    for light creation, a table to display scene lights, and buttons for various
    actions.

    This class communicates with the application's logic layer (e.g., MayaLightLogic.py)
    through a system of Qt signals. User actions in the UI trigger specific
    emitter methods (`emit_*`), which in turn emit signals with relevant data.
    The logic layer should connect to these signals to perform the actual Maya
    commands.
    """

    # (light_name, light_type, table_widget)
    signal_lightCreated = Signal(str, str, object)
    # (old_name, new_name,table_widget)
    signal_lightRenamed = Signal(str, str, object)
    signal_lightSearch = Signal(str, object)  # (search_text, table_widget)
    signal_table_selection = Signal(object)  # (table_widget)
    signal_lightDeleted = Signal(object)  # (table_widget)
    signal_refresh = Signal(object)  # (table_widget)

    lightTypes = [
        "aiPhotometricLight",
        "aiSkyDomeLight",
        "aiAreaLight",
        "spotLight",
        "pointLight",
        "directionalLight",
    ]

    def __init__(self):
        ''' Sets up the UI elements and connects signals to slots. '''
        super().__init__()
        self.build_ui()
        self.connect_signals()

    # SET WINDOW --------------------------------------------
    def build_ui(self):
        """
        Constructs and lays out all the UI widgets for the window.
        This includes setting up the window properties, creating buttons,
        input fields, the main table, and organizing them into layouts.
        """
        self.setWindowFlags(self.windowFlags() |
                            Qt.WindowStaysOnTopHint)  # KEEP WINDOW ON TOP
        self.setWindowTitle("Maya Light Manager")
        self.setMinimumSize(620, 690)
        self.setMaximumSize(620, 1000)

        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignCenter)

        title_light_name = self.label_text("Light Name:")
        self.entry_light_name = self.bar_text("Name your light", 160)

        self.info_text = self.label_text("Light Manager initialized")
        self.info_text.setFont(QFont(FONT, 9))

        title_ligh_search = self.label_text("Search by name:")
        self.entry_ligh_search = self.bar_text("Type light name to search", 570)

        title_light_type = self.label_text("Light Type:")
        self.combo_light_type = self.combo_list(
            self.lightTypes)  # COMBO BOX DRIVEN BY DICT

        self.button_create_light = self.push_button("Create Light")
        self.button_create_light.setStyleSheet(" background-color: #2a9d8f ; color: black;")

        self.button_refresh = self.push_button("Refresh")
        self.button_refresh.setStyleSheet(" background-color: #8ecae6 ; color: black;")

        self.button_render = self.push_button(" Render ")
        self.button_render.setFixedSize(70, 30)
        self.button_render.setContentsMargins(0, 0, 0, 0)
        self.button_render.setLayoutDirection(
            Qt.RightToLeft)  # SET THE BUTTON TO POINT RIGHT
        self.button_render.setStyleSheet(" background-color: #FFC107 ; color: black;")

        self.button_rename = self.push_button("Rename Light")
        self.button_rename.setStyleSheet(" background-color: #D17D98 ; color: white;")

        self.button_delete = self.push_button("Delete")
        self.button_delete.setStyleSheet(" background-color: #c1121f ; color: white;")

        self.light_table = QTableWidget()
        # SELECT ONLY ONE ROW AT A TIME
        self.light_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.light_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers)  # MAKE CELLS NON-EDITABLE
        self.light_table.setStyleSheet("QTableWidget { background-color: #222b33 ; color: white; }")
        for y in range(len(TABLE_HEADER)):
            self.light_table.setColumnCount(y+1)
            self.light_table.setHorizontalHeaderLabels(
                TABLE_HEADER)  # SET THE HEADER LABELS
            header = self.light_table.horizontalHeader()
            header.resizeSection(y, HEADER_SIZE[y])

        group_box_01 = QGroupBox()
        group_box_02 = QGroupBox()
        group_box_01.setStyleSheet(
            "QGroupBox { border: 1px solid grey; border-radius: 3px; padding: 20px; padding-top: 1px;padding-bottom: 2px;}")
        group_box_02.setStyleSheet(
            "QGroupBox { border: 1px solid grey; border-radius: 3px; padding: 3px;}")
        layoutV_01 = QVBoxLayout()
        layoutV_02 = QVBoxLayout()
        layoutV_01_01 = QVBoxLayout()
        layoutH_02 = QHBoxLayout()
        layoutH_03 = QHBoxLayout()

        layoutV_01_01.addWidget(self.button_render)
        layoutH_02.addWidget(title_light_name)
        layoutH_02.addWidget(self.entry_light_name)
        layoutH_02.addWidget(title_light_type)
        layoutH_02.addWidget(self.combo_light_type)
        layoutH_03.addWidget(self.button_create_light)
        layoutH_03.addWidget(self.button_rename)
        layoutV_02.addWidget(title_ligh_search)
        layoutV_02.addWidget(self.entry_ligh_search)
        layoutV_02.addWidget(self.light_table)
        layoutV_02.addWidget(self.button_refresh)
        layoutV_02.addWidget(self.button_delete)

        layoutV_01.addLayout(layoutV_01_01)
        layoutV_01.addLayout(layoutH_02)
        layoutV_01.addLayout(layoutH_03)

        group_box_01.setLayout(layoutV_01)
        group_box_02.setLayout(layoutV_02)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.logo)
        self.main_layout.addWidget(group_box_01)
        self.main_layout.addWidget(group_box_02)
        self.main_layout.addWidget(self.info_text)

        self.main_layout.setAlignment(Qt.AlignCenter)
        self.setLayout(self.main_layout)

    # GENERIC WIDGETS --------------------------------------------
    def label_text(self, text: str) -> QLabel:
        """ Creates a QLabel with standardized font and color. 
        Args:
            text (str): The text to display in the label.
        """
        label = QLabel(text=text)
        label.setFont(QFont(FONT, FONT_SIZE))
        label.setStyleSheet(f"color:{COLOR}")
        return label

    def bar_text(self, text: str = None, length=20) -> QLineEdit:
        """ Creates a QLineEdit with standardized font and size.
        Args:
            text (str, optional): Placeholder text for the line edit. Defaults to None.
            length (int, optional): The width of the line edit. Defaults to 20.
        """
        line_edit = QLineEdit(placeholderText=text)
        line_edit.setFixedSize(QSize(length, 25))
        line_edit.setFont(QFont(FONT, FONT_SIZE))
        return line_edit

    def combo_list(self, light_list: list) -> QComboBox:
        """Creates a QComboBox populated with items from a list.
        Args:
            light_list (list): A list of strings to add as items to the combo box.
        """
        combo_box = QComboBox()
        for light in sorted(light_list):
            combo_box.addItem(light)
            combo_box.setFont(QFont(FONT, FONT_SIZE))
        return combo_box

    def push_button(self, text: str) -> QPushButton:
        """Creates a QPushButton with a standardized font.
        Args:
            text (str): The text to display on the button.
        """
        button = QPushButton(text)
        button.setFont(QFont(FONT, FONT_SIZE))
        return button

    # SIGNALS --------------------------------------------
    def connect_signals(self):
        """
        Connects UI widget signals (e.g., button clicks) to their
        corresponding emitter methods in this class.
        """
        self.button_create_light.clicked.connect(self.emit_lightCreated)
        self.button_rename.clicked.connect(self.emit_lightRenamed)
        self.button_refresh.clicked.connect(self.emit_refresh)
        self.button_delete.clicked.connect(self.emit_lightDeleted)
        self.light_table.itemSelectionChanged.connect(
            self.emit_table_selection)
        self.entry_ligh_search.textChanged.connect(self.emit_lightSearch)

    # EMITTERS --------------------------------------
    def emit_lightCreated(self):
        """
        Gathers light name and type from the UI and emits the `signal_lightCreated`.
        Clears the light name field.
        """
        self.light_name = self.entry_light_name.text()
        self.light_type = self.combo_light_type.currentText()
        self.signal_lightCreated.emit(
            self.light_name, self.light_type, self.light_table)
        self.entry_light_name.clear()

    def emit_lightRenamed(self):
        """
        Gathers the old name from the table selection and the new name
        from the input field, then emits the `signal_lightRenamed`.
        Clears the light name field.
        """
        if self.light_table.selectedItems():
            self.old_name = self.light_table.currentItem().text()
            self.new_name = self.entry_light_name.text()
            self.signal_lightRenamed.emit(
                self.old_name, self.new_name, self.light_table)
            self.entry_light_name.clear()

    def emit_lightDeleted(self):
        """
        Confirms with the user and then emits the `signal_lightDeleted`
        for the currently selected light.
        """
        if self.light_table.selectedItems():
            selection = self.light_table.currentItem().text()
            btn_question = QMessageBox.question(
                self, "Question", f"Are you sure you want to delete {selection} ?")
            if btn_question == QMessageBox.Yes:
                self.signal_lightDeleted.emit(self.light_table)
            else:
                pass

    def emit_lightSearch(self):
        """
        Gathers the search text from the input field and emits the
        `signal_lightSearch`.
        """
        search_text = self.entry_ligh_search.text()
        self.signal_lightSearch.emit(search_text, self.light_table)

    def emit_table_selection(self):
        """ Emits the `signal_table_selection` when the table selection changes. """
        self.signal_table_selection.emit(self.light_table)

    def emit_refresh(self):
        """ Emits the `signal_refresh. """
        self.signal_refresh.emit(self.light_table)


class CustomLineEditNum(QLineEdit):
    """
    A custom QLineEdit that allows numerical values to be adjusted using the mouse wheel.
    It supports different step sizes based on keyboard modifiers (Ctrl, Shift).
    """

    def __init__(self,):
        """Initializes the QLineEdit and sets the default text."""
        super().__init__()
        self.setText("0.000")

    def wheelEvent(self, event: QWheelEvent):
        """
        Handles the wheel event to increment or decrement the QLineEdit's numerical value.
        - Ctrl + Scroll: Adjusts the value by 0.01
        - Shift + Scroll: Adjusts the value by 0.001
        Args:
            event (QWheelEvent): The wheel event.
        """
        modifiers = QApplication.keyboardModifiers()  # GET THE CURRENT KEYBOARD MODIFIERS
        if modifiers == Qt.ControlModifier:
            step = 0.01
        elif modifiers == Qt.ShiftModifier:
            step = 0.001
        else:
            super().wheelEvent(event)
            return

        current_value = float(self.text())
        delta = event.angleDelta().y() / 120
        new_value = current_value + delta * step
        try:
            self.setText(f"{new_value:.3f}")
        except ValueError:
            pass
