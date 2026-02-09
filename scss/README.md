# SCSS Source Files

This directory contains SCSS source files that are compiled to CSS.

## Setup

1. Install the **Live Sass Compiler** extension in VS Code:
   - Press `Ctrl+P` (or `Cmd+P` on Mac)
   - Type: `ext install ritwickdey.live-sass`
   - Or search for "Live Sass Compiler" in the Extensions panel

2. Open any `.scss` file in this directory

3. Click "Watch Sass" in the VS Code status bar (bottom right)

## Compilation

SCSS files are automatically compiled to:
- `src/rpi_camera_stream/static/css/[name].css` (expanded)
- `src/rpi_camera_stream/static/css/[name].min.css` (minified)

## File Structure

```
scss/
├── main.scss          # Main stylesheet (import others here)
├── _variables.scss    # Colors, fonts, spacing (prefix with _)
├── _mixins.scss       # Reusable SCSS mixins
└── components/        # Component-specific styles
    ├── _navbar.scss
    └── _buttons.scss
```

**Note:** Files prefixed with `_` are partials and won't compile to separate CSS files.

## Usage in Templates

```html
<!-- Use the minified version in production -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/main.min.css') }}">

<!-- Use expanded version for debugging -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
```

## Customizing Pico CSS

To customize Pico CSS:

1. Copy SCSS files from `vendor_packages/pico-main/scss/` to `scss/pico-custom/`
2. Modify variables and import in your main SCSS
3. The extension will compile your customized version

Example `scss/main.scss`:
```scss
// Override Pico variables
$primary-color: #0f4c75;

// Import Pico
@import '../vendor_packages/pico-main/scss/pico';

// Your custom styles
@import 'components/navbar';
```
