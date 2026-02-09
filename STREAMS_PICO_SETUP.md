# Streams Page Pico CSS Setup

## What's Been Done

### 1. Created SCSS File
- **File:** `scss/streams.scss`
- Contains custom styles for the camera streams page
- Uses Pico CSS variables for theming

### 2. Created New Template
- **File:** `src/rpi_camera_stream/templates/streams_pico.html`
- Uses Pico CSS instead of plain CSS
- Includes dark/light mode toggle
- Similar layout to the home page

### 3. Set Up Pico CSS
- Copied `pico.conditional.min.css` to `src/rpi_camera_stream/static/vendor/pico/css/`
- Conditional version supports both light and dark themes

### 4. Updated Flask Route
- Modified `src/rpi_camera_stream/routes/mjpeg.py`
- `/lan/streams` now uses `streams_pico.html` template

## Next Steps

### 1. Compile SCSS
Open VS Code and:
1. Open the file `scss/streams.scss`
2. Click **"Watch Sass"** in the status bar (bottom right)
3. This will compile to:
   - `src/rpi_camera_stream/static/css/streams.css`
   - `src/rpi_camera_stream/static/css/streams.min.css`

### 2. Test the Page
```bash
# Start the server
python -m rpi_camera_stream --device /dev/video4 --port 5000

# Visit in browser
http://localhost:5000/lan/streams
```

## Features

### Dark/Light Mode Toggle
- Click the moon/sun button in the navbar to toggle themes
- Theme preference is saved in localStorage
- Falls back to system preference on first visit

### Responsive Design
- 3-column grid on desktop (auto-fit)
- Single column on mobile (< 768px)
- Cards expand to fill available space

### Pico CSS Benefits
- Semantic HTML (minimal classes needed)
- Built-in dark mode support
- Consistent spacing and typography
- Accessible by default

## Customization

### Colors
Edit `scss/streams.scss` and use Pico CSS variables:
- `var(--pico-primary)` - Primary color
- `var(--pico-card-background-color)` - Card backgrounds
- `var(--pico-muted-color)` - Subtle text

### Layout
Adjust the grid in `scss/streams.scss`:
```scss
.camera-grid {
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
}
```

## Files Modified/Created

- ✅ `scss/streams.scss` (new)
- ✅ `src/rpi_camera_stream/templates/streams_pico.html` (new)
- ✅ `src/rpi_camera_stream/static/vendor/pico/css/pico.conditional.min.css` (copied)
- ✅ `src/rpi_camera_stream/routes/mjpeg.py` (updated)
