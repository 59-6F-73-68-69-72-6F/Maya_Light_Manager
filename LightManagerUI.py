# VERSION CHECK
# This code is designed to work with Maya versions 2024 and earlier.

from maya import cmds as m

maya_version = m.about(version=True)
if int(maya_version) <= 2024:
    from PySide2.QtCore import Qt, QSize
    from PySide2.QtGui import QFont,QWheelEvent
    from PySide2.QtWidgets import (QWidget,QTableWidget,QComboBox,QLabel,QLineEdit,QPushButton,
                               QVBoxLayout,QHBoxLayout,QAbstractItemView,QGroupBox,QApplication)
else:
    from PySide6.QtCore import Qt, QSize
    from PySide6.QtGui import QFont,QWheelEvent
    from PySide6.QtWidgets import (QWidget,QTableWidget,QComboBox,QLabel,QLineEdit,QPushButton,
                               QVBoxLayout,QHBoxLayout,QAbstractItemView,QGroupBox,QApplication)


TABLE_HEADER = ["Name","M","S","LightType","Color","Exposure","Samples","AOV"]
HEADER_SIZE = [160,20,20,90,55,75,75,60]
FONT = "Nimbus Sans, Bold"
COLOR = "#c7c7c5"
FONT_WEIGHT = 600
FONT_SIZE = 11


class LightManagerUI(QWidget):
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
        
        self.button_rename = self.push_button("Light Renamer")
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
        layoutV_01_01   = QVBoxLayout()
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
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.logo)
        main_layout.addWidget(group_box_01)
        main_layout.addWidget(group_box_02)
        main_layout.addWidget(self.info_text)
        
        main_layout.setAlignment(Qt.AlignCenter)
        self.setLayout(main_layout)
        
    # GENERIC WIDGETS --------------------------------------------
    def label_text(self,text):
        label = QLabel(text=text)
        label.setFont(QFont(FONT,FONT_SIZE))
        label.setStyleSheet(f"color:{COLOR}")
        return label

    def bar_text(self,text=None, length=20):
        line_edit = QLineEdit(placeholderText=text)
        line_edit.setFixedSize(QSize(length, 25))
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


class CustomLineEdit(QLineEdit):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setText("0.000") 

        def wheelEvent(self, event: QWheelEvent):
            modifiers = QApplication.keyboardModifiers()
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
