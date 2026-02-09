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

### Current Framework: Tailwind CSS

The project currently uses Tailwind CSS 3.4 (via Play CDN) for utility-first styling.

### Alternative Available: Pico CSS

Pico CSS v2 is available in `vendor_packages/pico-main/` for semantic HTML styling.

- **Use case**: Pages that benefit from class-less, semantic HTML styling
- **Location**: `vendor_packages/pico-main/css/`
- **Docs**: https://picocss.com
- **License**: MIT

See `vendor_packages/README.md` for integration instructions.
