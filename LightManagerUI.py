from Qt.QtCore import Qt, QSize,Signal
from Qt.QtGui import QFont,QWheelEvent
from Qt.QtWidgets import (QWidget,QTableWidget,QComboBox,QLabel,QLineEdit,QPushButton,
                            QVBoxLayout,QHBoxLayout,QAbstractItemView,QGroupBox,QApplication,QMessageBox)

from maya import cmds as m

TABLE_HEADER = ["Name","M","S","Light","Color","Exposure","Samples","AOV"]
HEADER_SIZE = [160,20,20,40,55,75,75,60]
FONT = "Nimbus Sans, Bold"
COLOR = "#c7c7c5"
FONT_WEIGHT = 600
FONT_SIZE = 11


class LightManagerUI(QWidget):
    
    signal_lightCreated = Signal(str,str,object) # (light_name, light_type, table_widget)
    signal_lightRenamed = Signal(str,str,object) # (old_name, new_name,table_widget)
    signal_lightSearch = Signal(str,object) # (search_text, table_widget)
    signal_table_selection = Signal(object) # (table_widget)
    signal_lightDeleted = Signal(object) # (table_widget)
    signal_refresh = Signal(object) # (table_widget)
    
    
    lightTypes = {
        "aiPhotometricLight":None,
        "aiSkyDomeLight": None,
        "aiAreaLight": None,
        "spotLight": m.spotLight,
        "pointLight": m.pointLight,
        "directionalLight": m.directionalLight,
        }

    def __init__(self):
        super().__init__()
        self.buildUI()
        self.connect_signals()

    # SET WINDOW --------------------------------------------
    def buildUI(self):
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # KEEP WINDOW ON TOP
        self.setWindowTitle("Maya Light Manager")
        self.setMinimumSize(620,690)
        self.setMaximumSize(620,1000)
        
        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignCenter)
    
        title_lightName = self.label_text("Light Name:")
        self.entry_lightName = self.bar_text("Name your light", 160)
        
        self.info_text = self.label_text("Light Manager initialized")
        self.info_text.setFont(QFont(FONT,9))
        
        title_lighSearch = self.label_text("Search by name:")
        self.entry_lighSearch = self.bar_text("Type light name to search",570)
        
        title_lightType = self.label_text("Light Type:")
        self.combo_lightType = self.combo_list(self.lightTypes) # COMBO BOX DRIVEN BY DICT
        
        self.button_createlight = self.push_button("Create Light")
        self.button_createlight.setStyleSheet(" background-color: #2a9d8f ; color: black;")
        
        self.button_refresh = self.push_button("Refresh")
        self.button_refresh.setStyleSheet(" background-color: #8ecae6 ; color: black;")
        
        self.button_render = self.push_button(" Render ")
        self.button_render.setFixedSize(70, 30)
        self.button_render.setContentsMargins(0, 0, 0, 0)
        self.button_render.setLayoutDirection(Qt.RightToLeft)  # SET THE BUTTON TO POINT RIGHT
        self.button_render.setStyleSheet(" background-color: #FFC107 ; color: black;")
        
        self.button_rename = self.push_button("Rename Light")
        self.button_rename.setStyleSheet(" background-color: #D17D98 ; color: white;")
        
        self.button_delete = self.push_button("Delete")
        self.button_delete.setStyleSheet(" background-color: #c1121f ; color: white;")
        
        self.lightTable = QTableWidget()
        self.lightTable.setSelectionMode(QAbstractItemView.SingleSelection) # SELECT ONLY ONE ROW AT A TIME
        self.lightTable.setEditTriggers(QAbstractItemView.NoEditTriggers) # MAKE CELLS NON-EDITABLE
        self.lightTable.setStyleSheet("QTableWidget { background-color: #222b33 ; color: white; }")
        for y in range(len(TABLE_HEADER)):
            self.lightTable.setColumnCount(y+1)
            self.lightTable.setHorizontalHeaderLabels(TABLE_HEADER)  # SET THE HEADER LABELS
            header = self.lightTable.horizontalHeader()
            header.resizeSection(y,HEADER_SIZE[y])
        
        group_box_01 = QGroupBox()
        group_box_02 = QGroupBox()
        group_box_01.setStyleSheet("QGroupBox { border: 1px solid grey; border-radius: 3px; padding: 20px; padding-top: 1px;padding-bottom: 2px;}")
        group_box_02.setStyleSheet("QGroupBox { border: 1px solid grey; border-radius: 3px; padding: 3px;}")
        layoutV_01   = QVBoxLayout()
        layoutV_02   = QVBoxLayout()
        layoutV_01_01 = QVBoxLayout()
        layoutH_02   = QHBoxLayout()
        layoutH_03   = QHBoxLayout()
        
        layoutV_01_01.addWidget(self.button_render)
        layoutH_02.addWidget(title_lightName)
        layoutH_02.addWidget(self.entry_lightName)
        layoutH_02.addWidget(title_lightType)
        layoutH_02.addWidget(self.combo_lightType)
        layoutH_03.addWidget(self.button_createlight)
        layoutH_03.addWidget(self.button_rename)
        layoutV_02.addWidget(title_lighSearch)
        layoutV_02.addWidget(self.entry_lighSearch)
        layoutV_02.addWidget(self.lightTable)
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
    def label_text(self,text:str):
        label = QLabel(text=text)
        label.setFont(QFont(FONT,FONT_SIZE))
        label.setStyleSheet(f"color:{COLOR}")
        return label

    def bar_text(self,text:str=None, length=20):
        line_edit = QLineEdit(placeholderText=text)
        line_edit.setFixedSize(QSize(length, 25))
        line_edit.setFont(QFont(FONT,FONT_SIZE))
        return line_edit

    def combo_list(self,light_list:dict):
        combo_box = QComboBox()
        for light in sorted(light_list):
            combo_box.addItem(light)
            combo_box.setFont(QFont(FONT,FONT_SIZE))
        return combo_box

    def push_button(self,text:str):
        button = QPushButton(text)
        button.setFont(QFont(FONT,FONT_SIZE))
        return button

    # SIGNALS --------------------------------------------
    def connect_signals(self):
        self.button_createlight.clicked.connect(self.emit_lightCreated)
        self.button_rename.clicked.connect(self.emit_lightRenamed)
        self.button_refresh.clicked.connect(self.emit_refresh)
        self.button_delete.clicked.connect(self.emit_lightDeleted)
        self.lightTable.itemSelectionChanged.connect(self.emit_table_selection)
        self.entry_lighSearch.textChanged.connect(self.emit_lightSearch)
        
    # EMITTERS --------------------------------------
    def emit_lightCreated(self):
       self.light_name = self.entry_lightName.text()
       self.light_type = self.combo_lightType.currentText()
       self.signal_lightCreated.emit( self.light_name, self.light_type,self.lightTable)
       self.entry_lightName.clear()
    
    def emit_lightRenamed(self):
        if self.lightTable.selectedItems():
            self.old_name = self.lightTable.currentItem().text()
            self.new_name = self.entry_lightName.text()
            self.signal_lightRenamed.emit(self.old_name, self.new_name, self.lightTable)
            self.entry_lightName.clear()
    
    def emit_lightDeleted(self):
        if self.lightTable.selectedItems():
            selection = self.lightTable.currentItem().text()
            btn_question = QMessageBox.question(self,"Question", f"Are you sure you want to delete {selection} ?")
            if btn_question == QMessageBox.Yes:
                self.signal_lightDeleted.emit(self.lightTable)
            else:
                pass
        
    def emit_lightSearch(self):
        search_text = self.entry_lighSearch.text()
        self.signal_lightSearch.emit(search_text, self.lightTable)
        
    def emit_table_selection(self):
        self.signal_table_selection.emit(self.lightTable)
        
    def emit_refresh(self):
        self.signal_refresh.emit(self.lightTable)


"""
Custom Line Edit for Numeric Input with Wheel Event Support.
Ctrl + Scroll to Adjust Value(0.01) or Shift + Scroll to Adjust Value(0.001).
"""
class CustomLineEditNum(QLineEdit):
        def __init__(self,):
            super().__init__()
            self.setText("0.000") 

        def wheelEvent(self, event: QWheelEvent):
            modifiers = QApplication.keyboardModifiers() # Get the current keyboard modifiers
            if modifiers == Qt.ControlModifier:
                step = 0.01
            elif modifiers ==   Qt.ShiftModifier:
                step = 0.001
            else:
                super().wheelEvent(event)
                return
            
            try:
                current_value = float(self.text())
                delta = event.angleDelta().y() / 120  
                new_value = current_value + delta * step
                self.setText(f"{new_value:.3f}")
            except ValueError:
                pass
