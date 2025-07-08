from PySide2.QtGui import QPixmap
import LightManagerUI as lmui
import MayaLightLogic as mll
import os

logic = None
ui = None
def getMayaMainWindow():
    global ui
    global logic
    
    ui = lmui.LightManagerUI()
    logic = mll.MayaLightLogic(ui)
    
    # LOAD LOGO IMAGE
    script_path = os.path.dirname(os.path.abspath(__file__))  # GET THE PATH OF THE CURRENT SCRIPT
    logo_path = os.path.join(script_path, "img", "logo.png")
    img = QPixmap(logo_path)
    ui.logo.setPixmap(img)
    
    # SET SIGNALS
    ui.button_createlight.clicked.connect(logic.create_light)
    ui.button_rename.clicked.connect(logic.rename_light)
    ui.button_refresh.clicked.connect(logic.refresh)
    ui.button_delete.clicked.connect(logic.delete)
    ui.lightTable.itemSelectionChanged.connect(logic.lightTable_selection)
    ui.entry_lighSearch.textChanged.connect(logic.searchLight)
    
    

    ui.show()
    return ui
getMayaMainWindow()
