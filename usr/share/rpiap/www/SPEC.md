# UI Specification

## Overview

Web UI for the RPiAP system, built with FastAPI and HTMX. Modern design and HTMX-only interactions (no custom JavaScript). Full-featured version with dashboard, settings, speedtest, and network interface management.

## Technology Stack

- **Backend**: Python3, FastAPI with Jinja2 templates
- **Frontend**: HTMX for dynamic interactions, no custom JavaScript
- **Styling**: CSS with CSS variables, Tailwind CSS-inspired utility classes, and BEM methodology
- **Architecture**: Server-rendered partials swapped via HTMX
- **Themes**: Support for multiple themes (default, dark, compact, colorful) via CSS variables and data attributes

## Core Components

### Header

The header provides navigation and user context across the application.

- **Fixed positioning**: Sticky at top of viewport
- **Hamburger menu**: CSS-only responsive toggle for sidebar visibility
  - **Desktop**: Always visible (3 lines), toggles sidebar hide/show
  - **Mobile**: Always visible (3 lines), toggles sidebar overlay
- **Title**: Application branding ("rpiap")
- **Responsive**: Adapts to mobile/desktop layouts

### Sidebar

The sidebar contains primary navigation links.

- **Desktop behavior**: Visible by default, collapsible via hamburger menu toggle
- **Mobile behavior**: Hidden by default, shown as overlay via hamburger menu toggle
- **Navigation links**: Dashboard, Speed Test, collapsible Test menu, and collapsible Settings menu
- **Icons**: Visual navigation aids (emoji icons)
- **Fixed width**: Consistent layout structure (250px)
- **Smooth transitions**: CSS transitions for show/hide animations
- **Active state highlighting**: Active menu items are highlighted with blue background (`#3498db`) and white text
  - **Main menu items**: Dashboard link is highlighted when on home page (`/`)
  - **Collapsible menu items**: Test/Settings menus are highlighted when on corresponding pages
  - **Submenu items**: Submenu items are highlighted when on their respective pages
  - **CSS classes**: `.sidebar__link--active` for main menu items, `.sidebar__sublink--active` for submenu items
  - **Automatic updates**: Sidebar active states are automatically updated during HTMX partial loads via `/api/sidebar/update` endpoint

#### Collapsible Menu Items

The sidebar supports collapsible menu items with dynamic submenus:

- **Test Menu**: A collapsible menu item that loads submenu items dynamically via HTMX
  - **Expand/Collapse**: Clicking the "Test" menu item toggles the submenu visibility via CSS checkbox (`#test-menu-toggle`)
  - **Dynamic Loading**: Submenu items are loaded from `/test/submenu` endpoint when expanded (HTMX `hx-get` on label click)
  - **Auto-load on Test Pages**: When on a test page (URL starts with `/test/`), the submenu automatically loads on page load (`hx-trigger="load"`)
  - **Stay Open**: When clicking on submenu items within the Test menu, the menu remains open to allow navigation between submenu pages (checkbox stays checked)
  - **Implementation**: Uses CSS checkbox pattern for state management (`:checked` pseudo-class) and HTMX for dynamic content loading

- **Settings Menu**: A collapsible menu item that loads settings submenu items dynamically via HTMX
  - **Expand/Collapse**: Clicking the "Settings" menu item toggles the submenu visibility via CSS checkbox (`#settings-menu-toggle`)
  - **Dynamic Loading**: Submenu items (DNS, WLAN, Client) are loaded from `/settings/submenu` endpoint when expanded
  - **Auto-load on Settings Pages**: When on a settings page (URL starts with `/settings/`), the submenu automatically loads on page load (`hx-trigger="load"`)
  - **Stay Open**: When clicking on submenu items within the Settings menu, the menu remains open
  - **Implementation**: Uses CSS checkbox pattern for state management and HTMX for dynamic content loading

#### Sidebar Active State Updates

The sidebar automatically updates active states during HTMX partial page loads:

- **Mechanism**: Each partial content template includes a hidden div with `hx-trigger="load"` that calls `/api/sidebar/update` endpoint
- **Endpoint**: `GET /api/sidebar/update?current_path=<path>` returns updated sidebar HTML with correct active states
- **Target**: Sidebar container (`#sidebar-container`) is updated via HTMX `hx-swap="innerHTML"`
- **Implementation**: 
  - Partial templates include hidden trigger divs
  - Trigger fires automatically when partial content is loaded into `.content-area`
  - Sidebar template (`sidebar.html`) accepts `current_path` parameter to determine active states
  - Active states are determined by comparing `current_path` with menu item URLs
- **Benefits**: Navigation state is always correct, even during HTMX partial loads without full page refresh

### Notification Bar

The notification bar is a sticky container that includes status bars (success/error) and info bar for displaying user feedback and system information.

- **Container Class**: `.notification-bar`
- **Positioning**: Sticky below header, never scrolls away
- **Layout**: Lives inside `.main-content` and respects the sidebar's visible/hidden state (same horizontal offset/width as page content)
- **Behavior**: Collapses when all bars are hidden (no reserved space)

#### Success Bar

Displays success messages and feedback to users.

- **Container ID**: `successBar`
- **Visibility**: Controlled via HX-Trigger from API endpoints
- **Styling**: Green background via CSS variable `--bg-status-success`
- **Auto-hide**: 5 seconds via HTMX trigger
- **Manual close**: Click × button to hide
- **Trigger**: `showSuccessBar` event from `POST /api/successbar`
- **HTMX**: Uses `hx-swap="textContent"` to update text content only

#### Error Bar

Displays error messages and feedback to users.

- **Container ID**: `errorBar`
- **Visibility**: Controlled via HX-Trigger from API endpoints
- **Styling**: Red background via CSS variable `--bg-status-error`
- **Auto-hide**: 5 seconds via HTMX trigger
- **Manual close**: Click × button to hide
- **Trigger**: `showErrorBar` event from `POST /api/errorbar`
- **HTMX**: Uses `hx-swap="textContent"` to update text content only

#### Info Bar

Displays persistent system information.

- **Container ID**: `infoBar`
- **Visibility**: Controlled by text content presence (CSS `:not(:empty)` selector)
- **Content**: Dynamic system status information (plain text only)
- **HTMX**: Uses `hx-swap="textContent"` to update text content only
- **Backend**: Server returns plain text instead of HTML fragments
- **Refresh**: Triggered via `refreshInfoBar` event from body

## Hamburger Menu Implementation

The hamburger menu is implemented using pure CSS with checkbox input toggle for state management.

### Desktop Behavior

- Hamburger icon always visible (3 horizontal lines)
- Sidebar visible by default
- Clicking hamburger hides sidebar and expands main content to full width
- Hamburger lines animate to X when active

### Mobile Behavior

- Hamburger icon always visible (3 horizontal lines)
- Sidebar hidden by default (off-screen)
- Main content stays in place, sidebar overlays page content
- Hamburger lines animate to X when active
- Clicking overlay or hamburger again hides sidebar

## CSS Styling Guidelines

### CSS Variables and Theme Support

RPIAP uses CSS variables for theming support:

- **Default theme**: Light theme with standard colors
- **Dark theme**: Dark mode with `[data-theme="dark"]` attribute
- **Compact theme**: Reduced spacing with `[data-theme="compact"]` attribute
- **Colorful theme**: Vibrant colors and gradients with `[data-theme="colorful"]` attribute

**Theme Variables:**
- Layout variables: `--header-height`, `--sidebar-width`
- Color variables: `--bg-primary`, `--bg-secondary`, `--text-primary`, `--text-secondary`, etc.
- Component colors: `--color-primary`, `--color-success`, `--color-error`, etc.
- Spacing variables: `--spacing-xs`, `--spacing-sm`, `--spacing-md`, `--spacing-lg`, `--spacing-xl`
- Border radius: `--border-radius-sm`, `--border-radius-md`
- Shadows: `--shadow-sm`, `--shadow-md`

### Tailwind CSS-Inspired Utility Classes

All CSS follows Tailwind CSS-inspired utility class naming conventions:

**Spacing utilities (implemented):**
- `.mt-4` - margin-top: 24px
- `.mb-4` - margin-bottom: 24px
- `.p-4` - padding: 16px
- `.px-4` - padding-left/right: 16px
- `.py-2` - padding-top/bottom: 8px
- `.gap-4` - gap: 16px

**Layout utilities (implemented):**
- `.text-center` - center text alignment
- `.d-flex` - display: flex
- `.justify-between` - justify-content: space-between
- `.items-center` - align-items: center
- `.flex-wrap` - flex-wrap: wrap

**Color utilities (implemented):**
- `.bg-primary`, `.bg-success`, `.bg-error`, `.bg-warning`, `.bg-info`
- `.text-muted` - muted text color

**When adding new styles:**
- ✅ **Use utility classes first** - prefer existing utility classes over custom CSS
- ✅ **Follow naming pattern** - use Tailwind-style naming (e.g., `bg-primary`, `text-error`)
- ✅ **Component classes** - use BEM methodology for component-specific styles
- ✅ **Mobile-first** - start with mobile styles, add breakpoints for larger screens
- ✅ **CSS variables** - use CSS variables for colors and spacing to support theming

**Current implementation:**
- ✅ Comprehensive utility classes
- ✅ BEM methodology for component classes (`.sidebar__item`, `.statusbar__content`, etc.)
- ✅ Mobile-first responsive breakpoints (@media max-width: 768px)
- ✅ Tailwind-style naming conventions (kebab-case)
- ✅ Active state classes (`.sidebar__link--active`, `.sidebar__sublink--active`) for navigation highlighting
- ✅ CSS variables for theming support

## UI Components Gallery

The `/test/ui` page provides a comprehensive visual reference for all UI components used throughout the application. This page is purely for design visualization and does not include functional behavior.

### Available Components

#### Form Components
- **Text Input**: Standard input field with label, placeholder, and helper text
- **Text Input (Error)**: Input field with error styling and error message
- **Password Input**: Input field with visibility toggle button
- **Select Box**: Dropdown selection component
- **Textarea**: Multi-line text input field

#### Boolean & Choice Components
- **Checkbox**: Single checkbox with custom styling (supports both `.checkbox-container` and `.checkbox` syntax)
- **Checkbox Group**: Multiple checkboxes for multiple selections
- **Radio Buttons**: Single selection from multiple options (supports both `.radio-container` and `.radio` syntax)
- **Toggle Switch**: On/off switch component (supports both `.toggle-switch` and `.toggle` syntax)

#### Button Components
- **Primary Button**: Main call-to-action button
- **Secondary Button**: Alternative action button
- **Success Button**: Confirmation action button
- **Danger Button**: Destructive action button
- **Disabled Button**: Non-interactive button state
- **Loading Button**: Button with loading indicator
- **Button Sizes**: Small (`.btn--sm`) and Large (`.btn--lg`) variants

#### Feedback Components
- **Success Alert**: Green alert box for success messages
- **Error Alert**: Red alert box for error messages
- **Warning Alert**: Yellow alert box for warning messages
- **Info Alert**: Blue alert box for informational messages
- **Badges**: Small status indicators (Primary, Secondary, Success, Warning, Danger)

#### Layout Components
- **Cards**: Content containers with header and body sections (`.ui-card`, `.card`)
- **Tabs**: Tabbed navigation interface
- **Breadcrumbs**: Navigation hierarchy display
- **Pagination**: Page navigation component
- **Grid**: Responsive grid layouts (`.grid`, `.grid--2-cols`)

### Component Organization

Components are organized into logical sections on the `/test/ui` page:
1. **Form Inputs** - All form input types
2. **Booleans & Choices** - Selection and toggle components
3. **Buttons** - All button variants and states
4. **Feedback & Status** - Alerts and status indicators
5. **Layout & Navigation** - Structural and navigation components

### Styling Guidelines for Components

All UI components follow these design principles:
- **Consistent Spacing**: 8px grid system for padding and margins (configurable via CSS variables)
- **Color Palette**: Semantic color usage via CSS variables (primary blue, success green, error red, etc.)
- **Typography**: Consistent font sizes and weights
- **Interactive States**: Hover, focus, and active states for all interactive elements
- **Accessibility**: Proper contrast ratios and keyboard navigation support
- **Responsive Design**: Mobile-first approach with appropriate breakpoints
- **Theme Support**: All components adapt to selected theme via CSS variables

## Dashboard Features

The dashboard (`/`) provides an overview of network interfaces and system status.

### Interface Cards

The dashboard displays network interfaces in three categories:

- **WAN Interfaces**: External-facing network interfaces (`.wan-interfaces-grid`, `.wan-interface-card`)
- **LAN Interfaces**: Local network interfaces (`.lan-interfaces-grid`, `.lan-interface-card`)
- **Other Interfaces**: Additional network interfaces (`.other-interfaces-grid`, `.other-interface-card`)

**Interface Card Features:**
- Status indicators (online/offline) with colored dots
- IPv4/IPv6 status display
- Interface name and details
- Active/inactive state styling (green border for active, red for inactive)
- Hover effects and transitions
- Responsive grid layout

### Interface Management

Network interfaces can be managed via the `/api/interfaces` endpoints:
- Interface status information
- Interface activation/deactivation
- IPv4/IPv6 configuration display

## Settings Pages

### DNS Settings (`/settings/dns`)

Configuration page for DNS settings with form-based interface.

- **Form**: DNS configuration form (`.settings_dns_form.html`)
- **Content**: Settings page layout (`.settings_dns_content.html`)
- **API**: `/api/settings/dns` endpoints for form submission and updates

### WLAN Settings (`/settings/wlan`)

Configuration page for WLAN (Wireless LAN) settings.

- **Form**: WLAN configuration form with country and channel selection
- **Content**: Settings page layout (`.settings_wlan_content.html`)
- **API**: `/api/settings/wlan` endpoints for form submission and updates
- **Dynamic Selects**: Country and channel selection dropdowns loaded via HTMX

### Client Settings (`/settings/wcli`)

Configuration page for wireless client settings.

- **Form**: Client configuration form (`.settings_wcli_form.html`)
- **Content**: Settings page layout (`.settings_wcli_content.html`)
- **API**: `/api/settings/wcli` endpoints for form submission and updates

## Speedtest Page

The speedtest page (`/speedtest`) provides network speed testing functionality.

### Features

- **Test Controls**: Start/stop speed test buttons
- **Progress Display**: Real-time progress bar during test execution
- **Results Display**: Speed metrics (download, upload, ping) in card format
- **Test Details**: Additional test information and statistics
- **HTMX Integration**: Dynamic updates via `/api/speedtest` endpoints

### Speed Metrics Display

- **Metric Cards**: Grid layout displaying download, upload, and ping metrics
- **Progress Bar**: Visual progress indicator during test execution
- **Responsive Design**: Adapts to mobile and desktop layouts

## Development Guidelines

### No Custom JavaScript

All interactivity must be handled through HTMX attributes and server-rendered partials. No custom JavaScript files or inline scripts (except HTMX library).

### Server-Rendered Partials

Dynamic content is provided as complete HTML partials from FastAPI endpoints, not JSON data to be processed by JavaScript.

### Theme Support

- Themes are controlled via `data-theme` attribute on HTML element
- Theme selection can be managed via query parameter (`?theme=dark`)
- All components should use CSS variables for colors and spacing
- Theme changes should be applied without page reload when possible

### Static File Caching

- Static files use `NoCacheStaticFiles` middleware with `Cache-Control: no-cache, must-revalidate`
- Ensures fresh content on every request
- No cache-busting query parameters needed (disabled caching)

### Accessibility

- Use semantic HTML
- Provide ARIA labels where needed
- Ensure keyboard navigation works
- Status messages should be announced to screen readers

### Performance

- Minimize HTTP requests
- Use appropriate caching headers for static assets
- Keep HTML partials lightweight
- Use HTMX indicators for loading states

## API Endpoints

### Page Routes
- `GET /` - Dashboard/home page with network interface cards
- `GET /speedtest` - Speedtest page
- `GET /settings/dns` - DNS settings page
- `GET /settings/wlan` - WLAN settings page
- `GET /settings/wcli` - Client settings page
- `GET /test/button` - Test button page with status/info bar functionality
- `GET /test/ui` - Test UI page with component gallery for visual reference
- `GET /test/select` - Test select page

### HTMX Partial Endpoints
- `GET /api/sidebar/update?current_path=<path>` - Returns updated sidebar partial with correct active states based on current path
- `GET /test/submenu` - Returns test submenu partial
- `GET /settings/submenu` - Returns settings submenu partial (DNS, WLAN, Client)

### Notification Bar Endpoints
- `POST /api/successbar` - Triggers success bar display via HX-Trigger
- `GET /api/successbar` - Returns success status bar text content
- `GET /api/successbar/hide` - Returns empty string to hide success bar
- `POST /api/errorbar` - Triggers error bar display via HX-Trigger
- `GET /api/errorbar` - Returns error status bar text content
- `GET /api/errorbar/hide` - Returns empty string to hide error bar
- `GET /api/infobar` - Returns plain text content for info bar (textContent swap)
- `POST /api/infobar/activate` - Activates info bar via file and triggers refresh
- `POST /api/infobar/deactivate` - Deactivates info bar and triggers refresh

### Settings API Endpoints
- `POST /api/settings/dns` - Submit DNS settings form
- `GET /api/settings/dns` - Get DNS settings form partial
- `POST /api/settings/wlan` - Submit WLAN settings form
- `GET /api/settings/wlan` - Get WLAN settings form partial
- `POST /api/settings/wcli` - Submit client settings form
- `GET /api/settings/wcli` - Get client settings form partial

### Speedtest API Endpoints
- `POST /api/speedtest` - Start speed test
- `GET /api/speedtest` - Get speedtest results partial
- `GET /api/speedtest/results` - Get speedtest results data

### Interfaces API Endpoints
- `GET /api/interfaces` - Get all network interfaces information
- `POST /api/interfaces/{interface}/activate` - Activate network interface
- `POST /api/interfaces/{interface}/deactivate` - Deactivate network interface

### Test API Endpoints
- `POST /api/test/select` - Handle test select form submission

## File Structure

```
├── app.py                          # FastAPI application with theme support
├── SPEC.md                         # This specification
├── routers/
│   ├── __init__.py                 # Routers package
│   ├── home.py                     # Dashboard/home router (GET /)
│   ├── settings.py                 # Settings router (submenu, DNS, WLAN, Client pages)
│   ├── speedtest.py                # Speedtest router (GET /speedtest)
│   ├── test.py                     # Test menu router (submenu endpoint)
│   ├── test_button.py              # Test button page router
│   ├── test_select.py              # Test select page router
│   ├── test_ui.py                  # Test UI page router
│   └── api/
│       ├── infobar.py              # Info bar router (/api/infobar endpoints)
│       ├── successbar.py           # Success bar router (/api/successbar endpoints)
│       ├── errorbar.py             # Error bar router (/api/errorbar endpoints)
│       ├── sidebar.py              # Sidebar router (/api/sidebar/update)
│       ├── settings_dns.py         # DNS settings API router
│       ├── settings_wlan.py        # WLAN settings API router
│       ├── settings_wcli.py        # Client settings API router
│       ├── speedtest.py            # Speedtest API router
│       ├── interfaces.py           # Network interfaces API router
│       └── test_select.py          # Test select API router
├── static/
│   ├── css/
│   │   └── styles.css              # Comprehensive stylesheet with CSS variables and themes
│   ├── js/
│   │   └── htmx.min.js             # HTMX library
│   └── settings.json               # Settings configuration file
└── templates/
    ├── index.html                  # Main page template with layout structure
    └── partials/
        ├── sidebar.html            # Sidebar partial (Dashboard + Speed Test + Test + Settings menus)
        ├── home_content.html       # Dashboard/home page content partial with interface cards
        ├── wan_cards.html          # WAN interface cards partial
        ├── lan_cards.html          # LAN interface cards partial
        ├── lan_info.html           # LAN interface info partial
        ├── other_cards.html        # Other interface cards partial
        ├── speedtest_content.html  # Speedtest page content partial
        ├── speedtest_results.html  # Speedtest results partial
        ├── settings_submenu.html   # Settings submenu partial (DNS, WLAN, Client)
        ├── settings_dns_content.html # DNS settings page content partial
        ├── settings_dns_form.html  # DNS settings form partial
        ├── settings_wlan_content.html # WLAN settings page content partial
        ├── settings_wlan_form.html # WLAN settings form partial
        ├── settings_wcli_content.html # Client settings page content partial
        ├── settings_wcli_form.html # Client settings form partial
        ├── countries_select.html   # Country selection dropdown partial
        ├── channels_select.html    # Channel selection dropdown partial
        ├── test_submenu.html       # Test submenu partial
        ├── test_button_content.html # Test button page content partial
        ├── test_select_content.html # Test select page content partial
        └── test_ui_content.html    # Test UI page content partial
```

## Testing

Visit various pages to test functionality:

**Dashboard Page (`/`):**
- Dashboard page with network interface cards (WAN, LAN, Other)
- Interface status indicators and details
- Sidebar Dashboard link is highlighted (active state)
- Responsive grid layout for interface cards

**Speedtest Page (`/speedtest`):**
- Speed test controls and progress display
- Speed metrics display (download, upload, ping)
- Sidebar Speed Test link is highlighted (active state)

**Settings Pages (`/settings/dns`, `/settings/wlan`, `/settings/wcli`):**
- Settings forms with HTMX submission
- Dynamic dropdowns (countries, channels)
- Sidebar Settings menu is highlighted and expanded (active state)
- Settings submenu items are highlighted when on corresponding pages

**Test Pages (`/test/button`, `/test/ui`, `/test/select`):**
- Test button page with status bar and info bar functionality
- UI components gallery for visual design reference
- Test select page for testing form interactions
- Sidebar Test menu is highlighted and expanded (active state)
- Test submenu items are highlighted when on corresponding pages

**Header & Sidebar:**
- Desktop: Sidebar visible by default, hamburger menu toggles hide/show with page expansion
- Mobile: Sidebar hidden by default, hamburger menu shows overlay with sidebar
- Hamburger Animation: 3 lines transform to X when active (desktop and mobile)
- Navigation: Collapsible menus (Test, Settings) with dynamic submenu loading
- **Active States**: Menu items are highlighted with blue background when on corresponding page
- **HTMX Updates**: Sidebar active states update automatically during partial page loads

**Success Bar:**
- Success button: Shows green success bar that auto-hides after 5s
- Click × to manually dismiss success messages

**Error Bar:**
- Error button: Shows red error bar that auto-hides after 5s
- Click × to manually dismiss error messages

**Info Bar:**
- Info activate: Shows persistent info bar content
- Info remove: Hides info bar content
- Auto-refresh via HTMX triggers

**Theme Support:**
- Theme selection via query parameter (`?theme=dark`, `?theme=compact`, `?theme=colorful`)
- All components adapt to selected theme
- CSS variables ensure consistent theming across all components

## Recent Changes

### Full-Featured Dashboard (v1.0)
- **Added**: Comprehensive dashboard with network interface cards (WAN, LAN, Other)
- **Added**: Network interface management API endpoints
- **Added**: Interface status indicators and details display

### Settings Pages (v1.0)
- **Added**: DNS settings page with form-based configuration
- **Added**: WLAN settings page with country and channel selection
- **Added**: Client settings page for wireless client configuration
- **Added**: Dynamic dropdowns loaded via HTMX

### Speedtest Integration (v1.0)
- **Added**: Speedtest page with real-time progress and results display
- **Added**: Speed metrics cards (download, upload, ping)
- **Added**: HTMX-based dynamic updates

### Theme Support (v1.0)
- **Added**: CSS variables for theming support
- **Added**: Multiple theme options (default, dark, compact, colorful)
- **Added**: Theme selection via query parameter

### Success/Error Bars Implementation (v1.0)
- **Added**: Success bar and error bar functionality
- **API**: Endpoints `/api/successbar` and `/api/errorbar` with HX-Trigger mechanism
- **UX**: Separate success (green) and error (red) notification bars with 5-second auto-hide
- **Architecture**: Dedicated routers `successbar.py` and `errorbar.py` for better organization

