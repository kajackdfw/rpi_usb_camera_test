# SCSS Source Files

This directory contains SCSS source files that are compiled to CSS.

## Setup

1. Install the **Live Sass Compiler** extension by Glenn Marks in VS Code:
   - Press `Ctrl+P` (or `Cmd+P` on Mac)
   - Type: `ext install glenn2223.live-sass`
   - Or search for "Live Sass Compiler" by Glenn Marks in the Extensions panel

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

## Color System

This project uses Pico CSS colors directly via the `pico-colors` namespace:

```scss
// Import Pico colors
@use '../vendor_packages/pico-main/scss/colors' as pico-colors;

// Use Pico colors directly
background: pico-colors.$zinc-200;
color: pico-colors.$orange-450;
border: 1px solid pico-colors.$jade-600;
```

### Available Color Palettes

Each palette has 19 shades (950-50):
- **Zinc** (`$zinc-###`): Grays for backgrounds, text, borders
- **Orange** (`$orange-###`): Brand colors
- **Jade** (`$jade-###`): Success/emerald colors
- **Azure** (`$azure-###`): Primary/blue colors
- **Red, Pink, Fuchsia, Purple, Violet, Indigo, Blue, Cyan, Teal, Green, Lime, Yellow, Amber**: See `vendor_packages/pico-main/scss/colors/_index.scss`

### Semantic Variables

The `_variables.scss` file provides semantic color names:

```scss
// Gray colors
$gray-950 through $gray-50
$gray (default: $gray-500)

// Brand colors (orange)
$brand-950 through $brand-50
$brand (default: $brand-450)

// Success colors (jade)
$success-950 through $success-50
$success (default: $success-400)

// Primary colors (azure)
$primary (azure-700)
$primary-hover (azure-600)
```
