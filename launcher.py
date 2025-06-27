'''
Copy the script in Maya script editor (python).
change the PATH to yours
Drag and Drop the script in your Maya shelf.
Enjoy !
'''

import sys
import main
from importlib import reload

directory = r"YOUR_PATH\Maya_Light_Manager"
if directory not in sys.path:
    sys.path.append(directory)

reload(main)
main.LightManager()
print("Launched Maya Light Manager.")
