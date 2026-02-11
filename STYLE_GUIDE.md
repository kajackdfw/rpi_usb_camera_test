# Style Guide

## Typography

### Font Family

The application uses the system font stack for optimal cross-platform appearance and performance:

```css
font-family: ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
```

This stack provides:
- Native system fonts on each platform
- Consistent emoji rendering across devices
- Fast loading (no external font downloads)

## Icons

### Preferred Icon Library

**Lucide Icons** is the preferred icon library for this project.

- Website: https://lucide.dev/
- Clean, consistent, and open-source icon set
- Available as SVG, React components, and web fonts
- Optimized for modern web applications

## CSS Frameworks

### Primary Framework: Pico CSS

The project uses Pico CSS v2 for semantic HTML styling with automatic light/dark theme support.

- **Location**: `vendor_packages/pico-main/css/`
- **Used version**: `pico.conditional.min.css` (supports data-theme attribute)
- **Docs**: https://picocss.com
- **License**: MIT

### Custom SCSS

Custom styles are written in SCSS and compiled to CSS:
- **Source**: `scss/` directory
- **Output**: `src/rpi_camera_stream/static/css/`
- **Main files**:
  - `main.scss` - Core styles, utilities, cards, forms
  - `streams.scss` - Camera stream page styles
  - `_variables.scss` - Color variables using Pico CSS colors

See `scss/README.md` for SCSS compilation instructions.
