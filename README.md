<h1 style="color: #5DADE2;">Maya Light Manager</h1> 

<blockquote style="color:rgb(85, 88, 91);">A custom tool for Autodesk Maya to significantly speed up the lighting workflow, particularly for artists using the Arnold renderer.</blockquote>

The **Maya Light Manager**, provides a compact and efficient user interface that centralizes the management of all supported lights within a Maya scene. Instead of navigating through the Outliner and Attribute Editor, artists can perform most common lighting tasks from a single, intuitive panel.

<h2 style="color: #48C9B0;">Key Features</h2>

*   **Centralized Light Lister**: Automatically gathers and lists all compatible lights (standard Maya lights and Arnold lights like `aiAreaLight`, `aiSkyDomeLight`, etc.) in a clean, organized table.

*   **Quick Light Creation**: Create new lights by selecting a type and giving them a descriptive name (e.g., "key", "rim"). The tool automatically applies a professional naming convention (`LGT_KEY_000`).

*   **Direct Attribute Control**: Modify essential light attributes directly from the list without selecting the light in Maya:
    *   **Mute/Solo**: Toggle lights on/off with the 'M' (Mute) checkbox or isolate a single light with the 'S' (Solo) checkbox to see its individual contribution.
    *   **Color**: A color swatch allows you to open the Maya color picker and change a light's color instantly.
    *   **Exposure, Samples, & AOV**: Edit numeric fields for Exposure and Samples directly. You can even use the mouse wheel (with Ctrl/Shift) to increment/decrement values. The light's AOV (Arbitrary Output Variable) can also be set.

*   **Efficient Scene Management**:
    *   **Rename & Delete**: Select a light in the UI to rename or delete it from the scene (with a confirmation prompt for deletion).
    *   **Search**: A search bar allows you to filter the list and quickly find specific lights by name.
    *   **Render**: A dedicated "Render" button launches the Arnold RenderView to immediately see your changes.

    *   **Refresh**: Instantly update the list to reflect any changes made elsewhere in Maya.

*   **Real-time Sync**: The tool stays synchronized with the Maya scene. Any changes made to light attributes in the Attribute Editor are reflected back in the Light Manager's UI.

<h2 style="color: #48C9B0;">Why Use the Light Manager?</h2>

This application streamlines the entire lighting process by reducing clicks, centralizing controls, and providing workflow-enhancing features that allow lighting artists to work faster and more efficiently.
