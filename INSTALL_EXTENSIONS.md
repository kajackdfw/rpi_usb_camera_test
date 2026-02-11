# VS Code Extensions for Development

This project uses VS Code extensions to enhance the development workflow.

## Required Extensions

### Live Sass Compiler
**ID:** `glenn2223.live-sass`

Automatically compiles SCSS files to CSS when you save.

**Install:**
```bash
code --install-extension glenn2223.live-sass
```

Or in VS Code:
1. Press `Ctrl+Shift+X` (Extensions panel)
2. Search for "Live Sass Compiler"
3. Click Install

**Usage:**
1. Open any `.scss` file in the `scss/` directory
2. Click "Watch Sass" in the status bar (bottom right)
3. Edit and save SCSS files - CSS will auto-generate

## Recommended Extensions

The project includes `.vscode/extensions.json` which will prompt you to install recommended extensions when you open the workspace.

## Configuration

All extension settings are pre-configured in `.vscode/settings.json`:
- SCSS output: `src/rpi_camera_stream/static/css/`
- Both expanded and minified CSS generated
- Source maps enabled for debugging
- Vendor packages excluded from compilation
