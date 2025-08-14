# KubeSeek Component Documentation

## Table of Contents
1. [Overview](#overview)
2. [Dashboard Template (dashboard.html)](#dashboard-template-dashboardhtml)
3. [CSS Styling](#css-styling)
4. [JavaScript Functions](#javascript-functions)
5. [Component Structure](#component-structure)
6. [Responsive Design](#responsive-design)
7. [Accessibility Features](#accessibility-features)
8. [Customization Guide](#customization-guide)

## Overview

The KubeSeek dashboard is built using a single HTML template with embedded CSS and JavaScript. The interface provides a real-time view of Kubernetes cluster health with a focus on simplicity and usability.

## Dashboard Template (dashboard.html)

### File Location
```
templates/dashboard.html
```

### Template Structure

#### HTML Head Section
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kubernetes Monitoring Dashboard</title>
    <!-- Font Awesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
```

**Key Features:**
- UTF-8 character encoding
- Responsive viewport configuration
- Font Awesome icons for visual indicators

#### CSS Variables and Responsive Design
```css
:root {
  --min-item-width: 20ch;
  --max-item-width: .5fr;
  --grid-spacing: .1rem;
  --item-padding: .1rem;
}
```

**CSS Variables:**
- `--min-item-width`: Minimum width for grid items (20 characters)
- `--max-item-width`: Maximum width for grid items (0.5 fraction of available space)
- `--grid-spacing`: Spacing between grid items (0.1rem)
- `--item-padding`: Internal padding for grid items (0.1rem)

### Responsive Breakpoints

#### Mobile Devices (max-width: 600px)
```css
@media (max-width: 600px) {
  :root {
    --max-item-width: 1fr;
  }
}
```
- Items expand to full width on small screens

#### Large Screens (min-width: 2560px)
```css
@media (min-width: 2560px) {
  :root {
    --max-item-width: 250px;
  }
}
```
- Items are capped at 250px width on very large screens

## CSS Styling

### Dark Theme Design
The dashboard uses a dark theme optimized for monitoring environments:

#### Color Palette
```css
/* Background Colors */
background-color: #1e1e1e;  /* Main background */
background-color: #2d2d2d;  /* Item background */
border: #3d3d3d solid 1px;  /* Item borders */

/* Text Colors */
color: #f1f1f1;             /* Primary text */
color: #ff9999;             /* Error text */

/* Status Colors */
background-color: #4caf50;  /* Healthy status (green) */
background-color: #f44336;  /* Error status (red) */
```

#### Typography
```css
font-family: "BlinkMacSystemFont", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "Noto Sans", sans-serif;
font-size: 12px;            /* Base font size */
font-weight: normal;        /* Non-bold typography */
```

### Layout Components

#### Container Layout
```css
.container {
    max-width: 98%;
}
```
- Uses 98% of available width for optimal space utilization

#### Grid Layout
```css
.monitor-list {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(var(--min-item-width), var(--max-item-width)));
    grid-gap: var(--grid-spacing);
    margin-bottom: 1rem;
}
```
- CSS Grid with auto-fitting columns
- Responsive to screen size
- Configurable spacing and sizing

#### Item Styling
```css
.item {
    width: 100%;
    padding: var(--item-padding) !important;
    border: #3d3d3d solid 1px;
    border-radius: 4px;
    background-color: #2d2d2d;
    text-align: center;
}
```
- Full-width items with centered content
- Subtle borders and rounded corners
- Dark background for contrast

### Status Indicators

#### Status Classes
```css
.status {
    font-size: 0.9em;
    font-weight: normal;
    padding: 4px 8px;
    border-radius: 2px;
    display: inline-block;
}

.status.ok {
    background-color: #4caf50;  /* Green for healthy */
}

.status.error {
    background-color: #f44336;  /* Red for issues */
}
```

#### Error Details
```css
.error-details {
    font-size: 0.8em;
    color: #ff9999;
    margin-top: 4px;
}
```
- Smaller text for detailed error information
- Red-tinted color for error emphasis

### Interactive Elements

#### Refresh Button
```css
.refresh-button {
    margin-bottom: 15px;
    padding: 8px 16px;
    background-color: #007bff;
    color: #fff;
    border: none;
    border-radius: 2px;
    cursor: pointer;
    font-size: 0.9em;
    font-weight: normal;
    transition: background-color 0.3s;
}

.refresh-button:hover {
    background-color: #0056b3;
}
```
- Blue button with hover effects
- Smooth color transition
- Proper spacing and sizing

## JavaScript Functions

### Refresh Functionality
```javascript
function refreshDashboard() {
    window.location.reload();
}
```

**Purpose:** Reloads the entire dashboard page to fetch fresh data

**Usage:** Called when the refresh button is clicked

**Implementation:** Simple page reload for immediate data refresh

## Component Structure

### Main Dashboard Layout
```html
<body>
    <h1><i class="fas fa-heartbeat"></i> Kubernetes Monitoring Dashboard</h1>
    <button class="refresh-button" onclick="refreshDashboard()">
        <i class="fas fa-sync-alt"></i> Refresh
    </button>

    <!-- Nodes Section -->
    <div class="container">
        <h2><i class="fas fa-server"></i> Nodes</h2>
        <div class="monitor-list">
            <!-- Node items -->
        </div>
    </div>

    <!-- Namespaces Section -->
    <div class="container">
        <h2><i class="fas fa-layer-group"></i> Namespaces</h2>
        <div class="monitor-list">
            <!-- Namespace items -->
        </div>
    </div>
</body>
```

### Node Item Template
```html
<div class="item">
    <div class="item-name">{{ node }}</div>
    <div class="status {% if status.status == 200 %}ok{% else %}error{% endif %}">
        {% if status.status == 200 %}
            <i class="fas fa-check-circle"></i> Healthy
        {% else %}
            <i class="fas fa-times-circle"></i> Issue
        {% endif %}
    </div>
</div>
```

**Features:**
- Dynamic status class assignment
- Conditional icon display
- Status text based on health

### Namespace Item Template
```html
<div class="item">
    <div class="item-name">{{ namespace }}</div>
    <div class="status {% if status.status == 200 %}ok{% else %}error{% endif %}">
        {% if status.status == 200 %}
            <i class="fas fa-check-circle"></i> {{ status.message }}
        {% else %}
            <i class="fas fa-times-circle"></i> {{ status.message }}
        {% endif %}
    </div>
    <!-- Show error details if present -->
    {% if status.status != 200 %}
        <div class="error-details">
            {% if status.unhealthy_pods %}
                Pods with issues: {{ status.unhealthy_pods|join(', ') }}
            {% endif %}
            {% if status.log_issues %}
                (Log errors detected)
            {% endif %}
        </div>
    {% endif %}
</div>
```

**Features:**
- Dynamic status display
- Error details for unhealthy namespaces
- List of unhealthy pods
- Log error indicators

## Responsive Design

### Mobile-First Approach
The dashboard is designed with mobile devices in mind:

1. **Flexible Grid:** Items automatically adjust to screen size
2. **Readable Text:** Optimized font sizes for small screens
3. **Touch-Friendly:** Adequate button sizes for touch interaction

### Breakpoint Strategy
- **Default:** Desktop layout with constrained item widths
- **Mobile (≤600px):** Full-width items for better readability
- **Large Screens (≥2560px):** Fixed maximum width to prevent excessive stretching

### Grid Behavior
```css
grid-template-columns: repeat(auto-fit, minmax(var(--min-item-width), var(--max-item-width)));
```
- `auto-fit`: Automatically fits as many columns as possible
- `minmax`: Ensures minimum and maximum column widths
- Responsive to container size changes

## Accessibility Features

### Semantic HTML
- Proper heading hierarchy (h1, h2)
- Meaningful button labels
- Descriptive icon usage

### Visual Indicators
- Color-coded status indicators
- Icon-based status representation
- Clear visual hierarchy

### Keyboard Navigation
- Clickable refresh button
- Proper focus states (via CSS hover effects)

### Screen Reader Support
- Descriptive text for status indicators
- Proper alt text for icons (via Font Awesome)
- Logical content structure

## Customization Guide

### Modifying Colors
To change the color scheme, update the CSS variables:

```css
:root {
  /* Primary colors */
  --primary-bg: #1e1e1e;
  --secondary-bg: #2d2d2d;
  --border-color: #3d3d3d;
  --text-color: #f1f1f1;
  
  /* Status colors */
  --healthy-color: #4caf50;
  --error-color: #f44336;
  --warning-color: #ff9800;
}
```

### Adjusting Layout
To modify the grid layout:

```css
:root {
  --min-item-width: 25ch;    /* Increase minimum width */
  --max-item-width: 1fr;     /* Allow full width */
  --grid-spacing: 0.5rem;    /* Increase spacing */
  --item-padding: 0.5rem;    /* Increase padding */
}
```

### Adding New Sections
To add monitoring sections for other Kubernetes resources:

1. **Add HTML Structure:**
```html
<div class="container">
    <h2><i class="fas fa-cube"></i> Pods</h2>
    <div class="monitor-list">
        {% for pod, status in health_data.pods.items() %}
            <div class="item">
                <div class="item-name">{{ pod }}</div>
                <div class="status {% if status.status == 200 %}ok{% else %}error{% endif %}">
                    {{ status.message }}
                </div>
            </div>
        {% endfor %}
    </div>
</div>
```

2. **Update Backend:** Add corresponding data to the health API response

### Custom Status Types
To add new status types (e.g., warning):

```css
.status.warning {
    background-color: #ff9800;
    color: #000;
}
```

```html
<div class="status {% if status.status == 200 %}ok{% elif status.status == 300 %}warning{% else %}error{% endif %}">
```

### Performance Optimizations

#### CSS Optimizations
- Use CSS variables for consistent theming
- Minimize CSS selectors for better performance
- Use efficient grid layout

#### JavaScript Optimizations
- Minimal JavaScript for better performance
- Simple page reload for data refresh
- No complex DOM manipulation

#### Template Optimizations
- Efficient Jinja2 template usage
- Conditional rendering to avoid unnecessary elements
- Proper escaping of user data

## Browser Compatibility

### Supported Browsers
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

### CSS Features Used
- CSS Grid (supported in all modern browsers)
- CSS Variables (supported in all modern browsers)
- Flexbox (fallback for older browsers)

### JavaScript Features Used
- ES6+ features (arrow functions, template literals)
- Modern DOM APIs
- Font Awesome icons (CDN-based)

## Security Considerations

### Content Security
- Template auto-escaping prevents XSS
- No inline JavaScript execution
- External resources loaded from trusted CDNs

### Data Handling
- Server-side data processing
- Client-side display only
- No sensitive data exposure

## Deployment Considerations

### Static Asset Optimization
- Consider bundling CSS and JavaScript
- Optimize Font Awesome loading
- Use CDN for external resources

### Caching Strategy
- Cache static assets (CSS, JS, icons)
- Implement proper cache headers
- Consider service worker for offline functionality

### Monitoring Integration
- Add analytics for dashboard usage
- Monitor dashboard performance
- Track user interactions for UX improvements