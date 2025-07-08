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

from PySide2.QtWidgets import QWidget,QTableWidget,QComboBox,QLabel,QLineEdit,QPushButton,QVBoxLayout,QAbstractItemView
from PySide2.QtGui import QFont
from PySide2.QtCore import Qt
from maya import cmds as m


TABLE_HEADER = ["Name","M","S","LightType","Color","Exposure","Samples"]
HEADER_SIZE = [180,20,20,100,55,75,75]
FONT = "Nimbus Sans, Bold"
COLOR = "#c7c7c5"
FONT_WEIGHT = 600
FONT_SIZE = 11


class LightManagerUI(QWidget):
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
        

    # SET WINDOW --------------------------------------------
    def buildUI(self):
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # KEEP WINDOW ON TOP
        self.setWindowTitle("Maya Light Manager")
        self.setMinimumSize(610,670)
        self.setMaximumSize(610,1000)
        layoutV = QVBoxLayout(self)
        
        self.logo = QLabel()
        
        title_lightName = self.label_text("Light Name:")
        self.entry_lightName = self.bar_text("name your light  (key,rim...etc")
        
        title_lightType = self.label_text("Light Type:")
        self.combo_lightType = self.combo_list(self.lightTypes) # COMBO BOX DRIVEN BY DICT
        
        self.button_createlight = self.push_button("Create Light")
        self.button_createlight.setStyleSheet(" background-color: #2a9d8f ; color: black;")
        
        self.button_refresh = self.push_button("Refresh")
        self.button_refresh.setStyleSheet(" background-color: #8ecae6 ; color: black;")
        
        self.button_rename = self.push_button("Light Renamer")
        self.button_rename.setStyleSheet(" background-color: #D17D98 ; color: white;")
        
        self.button_delete = self.push_button("Delete")
        self.button_delete.setStyleSheet(" background-color: #c1121f ; color: white;")
        
        title_lightList = self.label_text("Light List:")
        
        self.lightTable = QTableWidget()
        self.lightTable.setSelectionMode(QAbstractItemView.SingleSelection) #SELECT ONLY ONE ROW AT A TIME
        self.lightTable.setEditTriggers(QAbstractItemView.NoEditTriggers) # MAKE CELLS NON-EDITABLE
        self.lightTable.setStyleSheet("QTableWidget { background-color: #222b33 ; color: white; }")
        for y in range(7):
            self.lightTable.setColumnCount(y+1)
            self.lightTable.setHorizontalHeaderLabels(TABLE_HEADER)  # SET THE HEADER LABELS
            header = self.lightTable.horizontalHeader()
            header.resizeSection(y,HEADER_SIZE[y])
        
        layoutV.addWidget(self.logo)
        layoutV.addWidget(title_lightName)
        layoutV.addWidget(self.entry_lightName)
        layoutV.addWidget(self.button_createlight)
        layoutV.addWidget(title_lightType)
        layoutV.addWidget(self.combo_lightType)
        layoutV.addWidget(title_lightList)
        layoutV.addWidget(self.button_rename)
        layoutV.addWidget(self.lightTable)
        layoutV.addWidget(self.button_refresh)
        layoutV.addWidget(self.button_delete)
        
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


