# Alternative Style 2: Dark Industrial Dashboard

## Design Philosophy

A professional, high-contrast industrial control panel aesthetic inspired by military systems, robotics interfaces, and professional broadcast equipment. This style emphasizes functionality, readability, and a "mission control" atmosphere suitable for rover operations.

## Visual Characteristics

### Color Scheme

**Primary Colors:**
- Background: `#1a1a1a` (Dark Charcoal)
- Surface: `#2d2d2d` (Medium Gray)
- Accent: `#ff6b35` (Safety Orange)
- Success: `#4caf50` (Military Green)
- Warning: `#ffa726` (Amber)
- Error: `#f44336` (Alert Red)

**Text Colors:**
- Primary: `#e0e0e0` (Light Gray)
- Secondary: `#9e9e9e` (Medium Gray)
- Muted: `#616161` (Dark Gray)

### Typography

```css
font-family: 'Roboto Mono', 'Courier New', monospace;
```

- **Headers**: Bold, uppercase, wide letter-spacing
- **Body**: Monospace for technical readability
- **Status indicators**: All caps with tracking
- **Data displays**: Tabular numbers for alignment

## Key Design Elements

### 1. Grid Pattern Background
```css
background:
    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px),
    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px);
background-size: 20px 20px;
```
Creates a subtle technical grid pattern suggesting precision and measurement.

### 2. Camera Cards

**Structure:**
- Dark gray panels with 1px colored borders
- Hard edges (no border-radius or minimal 2px)
- Glowing accent lines when active
- LED-style status indicators

**Active Camera:**
```css
border: 2px solid #ff6b35;
box-shadow: 0 0 20px rgba(255, 107, 53, 0.3);
```

**Inactive Camera:**
```css
border: 1px solid #424242;
opacity: 0.6;
```

### 3. Status Indicators

**LED-style badges:**
```css
.status-led {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #4caf50;
    box-shadow: 0 0 10px #4caf50;
    animation: pulse 2s infinite;
}
```

**Status Labels:**
- `[ACTIVE]` - Green LED + text
- `[OFFLINE]` - Red LED + text
- `[STANDBY]` - Yellow LED + text

### 4. Data Displays

**Technical Info Panels:**
```
┌─────────────────────────────┐
│ CAMERA 0                    │
│ STATUS: [●] ACTIVE          │
│ DEVICE: /dev/video0         │
│ RES:    1280x720            │
│ FPS:    30.0                │
│ FRAMES: 45,231              │
└─────────────────────────────┘
```

Monospace ASCII-style borders for technical aesthetic.

### 5. Controls

**Buttons:**
- Rectangular with hard edges
- Uppercase text
- High contrast borders
- Subtle scan line effect on hover

```css
button {
    background: #2d2d2d;
    border: 2px solid #ff6b35;
    color: #ff6b35;
    text-transform: uppercase;
    letter-spacing: 2px;
    padding: 12px 24px;
    font-family: 'Roboto Mono', monospace;
    transition: all 0.2s;
}

button:hover {
    background: #ff6b35;
    color: #1a1a1a;
    box-shadow: 0 0 20px rgba(255, 107, 53, 0.5);
}
```

### 6. Placeholder States

**Inactive Camera Display:**
```
┌─────────────────────────────┐
│                             │
│         ⚠                   │
│   NO SIGNAL DETECTED        │
│                             │
│  Camera offline or          │
│  not connected              │
│                             │
└─────────────────────────────┘
```

Large warning symbol with scan line animation.

## Layout Structure

### Navigation Bar
- Fixed header with dark background
- Monospace font for all links
- Orange underline on active page
- Subtle separator lines between sections

### Camera Grid
```css
.camera-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 30px;
    padding: 40px;
    background: #1a1a1a;
}
```

### Card Header
```
┌──────────────────────────────────┐
│ [●] CAMERA 0            [ACTIVE] │
├──────────────────────────────────┤
```

Includes LED indicator, camera ID, and status badge.

## Animation Effects

### 1. Status LED Pulse
```css
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
```

### 2. Scan Line Effect
```css
@keyframes scanline {
    0% { transform: translateY(-100%); }
    100% { transform: translateY(100%); }
}
```

Subtle vertical line animation on camera feeds.

### 3. Data Stream Effect
Numbers and status text have a subtle flicker effect to simulate live data updates.

## Typography Scale

- **Page Title**: 36px, bold, uppercase, tracking: 4px
- **Section Headers**: 24px, bold, uppercase, tracking: 3px
- **Camera Labels**: 18px, medium, uppercase, tracking: 2px
- **Body Text**: 14px, normal
- **Technical Data**: 12px, monospace, tabular-nums

## Hover States

### Camera Cards
- Subtle glow effect
- Brightness increase by 10%
- Border color intensifies

### Buttons
- Background fills with accent color
- Text inverts
- Glow increases

### Snapshot Images
- Crosshair overlay appears
- Zoom cursor
- Border glows

## Iconography

Use simple geometric shapes and symbols:
- **Active**: ● (filled circle)
- **Inactive**: ○ (empty circle)
- **Warning**: ⚠ (triangle)
- **Error**: ✕ (X mark)
- **Success**: ✓ (check mark)
- **Live**: ▶ (play symbol)
- **Offline**: ■ (square)

## Contrast with Current Style

| Aspect | Current (Glassmorphic) | Alternative (Industrial) |
|--------|----------------------|------------------------|
| **Background** | Purple gradient | Dark charcoal + grid |
| **Cards** | White, soft shadows | Dark gray, hard borders |
| **Aesthetic** | Modern, friendly | Professional, technical |
| **Typography** | Sans-serif, clean | Monospace, precise |
| **Colors** | Pastels, gradients | High contrast, neon accents |
| **Borders** | Rounded (12px) | Sharp (0-2px) |
| **Mood** | Contemporary, welcoming | Military, focused |

## Use Cases

**Best suited for:**
- Professional robotics operations
- Research and development environments
- Industrial monitoring systems
- Military or aerospace applications
- Users who prefer dark mode
- Environments with ambient lighting
- Long-duration monitoring sessions

**Advantages:**
- ✅ Reduced eye strain in dark environments
- ✅ Professional, "serious" appearance
- ✅ High information density
- ✅ Clear status differentiation
- ✅ Feels purpose-built for robotics
- ✅ Excellent contrast for outdoor viewing on laptops

## Implementation Notes

### CSS Variables
```css
:root {
    --bg-primary: #1a1a1a;
    --bg-secondary: #2d2d2d;
    --accent-orange: #ff6b35;
    --status-active: #4caf50;
    --status-inactive: #616161;
    --text-primary: #e0e0e0;
    --text-secondary: #9e9e9e;
    --border-color: #424242;
    --glow-orange: rgba(255, 107, 53, 0.3);
}
```

### Font Loading
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet">
```

### Performance Considerations
- Minimize box-shadow complexity
- Use CSS transforms for animations
- Lazy load camera snapshots
- Optimize monospace font rendering

## Sample Component: Camera Card

```html
<div class="camera-card" data-status="active">
    <div class="card-header">
        <span class="status-led active"></span>
        <span class="camera-id">CAMERA 0</span>
        <span class="status-badge active">[ACTIVE]</span>
    </div>

    <div class="card-body">
        <div class="snapshot-container">
            <img src="/api/snapshot" alt="Camera 0">
            <div class="scan-line"></div>
        </div>

        <div class="info-panel">
            <div class="info-row">
                <span class="label">DEVICE:</span>
                <span class="value">/dev/video0</span>
            </div>
            <div class="info-row">
                <span class="label">RES:</span>
                <span class="value">1280x720</span>
            </div>
            <div class="info-row">
                <span class="label">FPS:</span>
                <span class="value">30.0</span>
            </div>
        </div>
    </div>

    <div class="card-actions">
        <button class="btn-primary">
            <span>▶</span> LIVE STREAM
        </button>
        <button class="btn-secondary">
            <span>↻</span> REFRESH
        </button>
    </div>
</div>
```

## Future Enhancements

1. **Console Log Panel**: Real-time system messages
2. **Performance Graphs**: CPU, bandwidth, frame rate charts
3. **Command Line Interface**: For advanced operations
4. **Heat Maps**: Show camera activity over time
5. **Recording Indicators**: Red recording badge when capturing
6. **Timestamp Overlay**: Military time display
7. **Grid Overlay Toggle**: Composition guides on snapshots

---

**Style Category**: Industrial / Military / Technical
**Complexity**: Medium (more CSS, careful color balance)
**Best For**: Professional/technical users, dark environment use
**Inspiration**: NASA mission control, military HUDs, broadcast equipment
