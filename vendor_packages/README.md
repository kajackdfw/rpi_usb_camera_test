# Vendor Packages

This directory contains third-party libraries and frameworks that are included directly in the project.

## Pico CSS v2

**Location:** `pico-main/`

Pico CSS is a minimal CSS framework for semantic HTML. It provides elegant styling with minimal classes.

### What's Included

- Precompiled CSS files in `pico-main/css/`
- SCSS source files in `pico-main/scss/`
- Multiple color themes (amber, blue, cyan, etc.)
- Class-less and conditional versions

### Usage

To use Pico CSS in your templates, link to one of the CSS files:

```html
<!-- Standard version -->
<link rel="stylesheet" href="/static/vendor/pico/pico.min.css">

<!-- Class-less version (styles raw HTML) -->
<link rel="stylesheet" href="/static/vendor/pico/pico.classless.min.css">

<!-- Themed versions -->
<link rel="stylesheet" href="/static/vendor/pico/pico.blue.min.css">
```

### Available Files

- `pico.min.css` - Standard Pico CSS
- `pico.classless.min.css` - Class-less version (automatic styling)
- `pico.[theme].min.css` - Themed versions (amber, blue, cyan, etc.)
- `pico.conditional.[theme].min.css` - Conditional styling versions

### Documentation

- Official website: https://picocss.com
- Documentation: https://picocss.com/docs
- GitHub: https://github.com/picocss/pico

### License

MIT License - see `pico-main/LICENSE.md`

## Managing Vendor Packages

- **Zip files are gitignored** - Only extracted contents are tracked
- To update a package: download new zip, extract, remove old version
- Keep this README updated when adding new vendor packages
