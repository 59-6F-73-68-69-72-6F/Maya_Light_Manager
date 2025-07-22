######################################################
# - MAYA LIGHT MANAGER -
# AUTHOR : RUDY LETI
# DATE : 2025/07/09
# DESIGNED TO SPEED UP LIGHTING PRODUCTION PROCESS
#
# .LIST THE MOST COMMON LIGHTS USED IN PRODUCTION (ARNOLD ORIENTED) IN THE SCENE ( CREATE,GATHER , RENAME AND DELETE LIGHTS)
# . NAMING CONVENTION INTEGRATED
# . LIGHTS SELECTABLE FROM THE UI
# . ALLOW TO MUTE OR SOLO LIGHTS
# . ALLOW QUICK MODIFICATION OF LIGHT COLOR,EXPOSURE, SAMPLES AND AOV
# . ALLOW TO SEARCH LIGHTS BY NAME
# . ALLOW TO RENDER THE SCENE FROM THE UI
# . FILTERS LIGHTS BY TYPE (MAYA LIGHT, ARNOLD)
# . CLEAR AND EASY SAMPLES MANAGMENT
######################################################

# VERSION CHECK
# This code is designed to work with Maya versions 2024 and earlier.
import maya.cmds as m
maya_version = m.about(version=True)

if int(maya_version) <= 2024:
    from PySide2.QtGui import QPixmap
else:
    from PySide6.QtGui import QPixmap
    
import LightManagerUI as lmui
import MayaLightLogic as mll
import os

logic = None
ui = None

def getMayaMainWindow()-> lmui.LightManagerUI:
    global ui,logic
    
    ui = lmui.LightManagerUI()
    logic = mll.MayaLightLogic(ui)
    
    # LOAD LOGO IMAGE
    script_path = os.path.dirname(os.path.abspath(__file__))  # GET THE PATH OF THE CURRENT SCRIPT
    logo_path = os.path.join(script_path, "img", "logo.png")
    img = QPixmap(logo_path)
    ui.logo.setPixmap(img)
    
    # SET SIGNALS
    ui.signal_table_selection.connect(logic.lightTable_selection)
    ui.signal_lightCreated.connect(logic.create_light)
    ui.signal_lightRenamed.connect(logic.rename_light)
    ui.signal_lightSearch.connect(logic.searchLight)
    ui.button_render.clicked.connect(logic.render) 
    ui.signal_lightDeleted.connect(logic.delete)
    ui.signal_refresh.connect(logic.refresh)
    logic.refresh(ui.lightTable)  # INITIAL REFRESH TO LOAD LIGHTS
    
    ui.show()
    return ui
getMayaMainWindow()
