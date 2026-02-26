# --------------------------------------------------------------------------------
# Project: ExtractPDF-EPUB
# File: src/extract_app/modules/ui/theme.py
# Version: 1.0.0
# Description: Centralized Design System tokens (Colors, Fonts, Spacing).
#              Based on Dark Navy Dashboard references (ZeroClaw, Sleep Lab).
# --------------------------------------------------------------------------------

# --- Color Palette (Dark Navy Theme) ---
class Colors:
    """Application-wide color constants."""
    # Backgrounds
    BG_APP          = "#0D1117"    # Deepest background
    BG_SIDEBAR      = "#161B22"    # Sidebar panel
    BG_CARD         = "#1C2333"    # Card / Surface
    BG_CARD_HOVER   = "#252D3D"    # Card hover state
    BG_INPUT        = "#0D1117"    # Input field background
    
    # Borders
    BORDER          = "#30363D"    # Subtle borders
    BORDER_ACCENT   = "#3B82F6"    # Active/Focused border (Blue)
    
    # Accent Colors
    PRIMARY         = "#3B82F6"    # Primary Blue (buttons, links)
    PRIMARY_HOVER   = "#2563EB"    # Primary hover
    SUCCESS         = "#10B981"    # Green (Translated, OK, Active)
    SUCCESS_HOVER   = "#059669"    # Green hover
    WARNING         = "#F59E0B"    # Amber warning
    DANGER          = "#EF4444"    # Red (delete, error)
    DANGER_HOVER    = "#B91C1C"    # Darker red hover
    
    # Text
    TEXT_PRIMARY    = "#F0F6FC"    # Main headings, bright text
    TEXT_SECONDARY  = "#C9D1D9"    # Body text
    TEXT_MUTED      = "#8B949E"    # Labels, metadata, placeholders
    TEXT_LINK       = "#58A6FF"    # Clickable links
    
    # Sidebar specific
    SIDEBAR_ACTIVE  = "#1F2A3D"    # Active menu item bg
    SIDEBAR_HOVER   = "#1A2332"    # Menu item hover


# --- Font Configuration ---
class Fonts:
    """Font family and size presets."""
    FAMILY      = "Segoe UI"
    
    # Sizes
    H1          = (FAMILY, 22, "bold")
    H2          = (FAMILY, 18, "bold")
    H3          = (FAMILY, 15, "bold")
    BODY        = (FAMILY, 13)
    BODY_BOLD   = (FAMILY, 13, "bold")
    SMALL       = (FAMILY, 11)
    TINY        = (FAMILY, 10)
    
    # Special
    LOGO        = (FAMILY, 20, "bold")
    NAV         = (FAMILY, 13)
    NAV_LABEL   = (FAMILY, 10, "bold")
    BUTTON      = (FAMILY, 13, "bold")


# --- Spacing ---
class Spacing:
    """Common padding and margin values."""
    XS  = 4
    SM  = 8
    MD  = 12
    LG  = 16
    XL  = 20
    XXL = 32
    
    # Component specific
    SIDEBAR_WIDTH   = 220
    CARD_RADIUS     = 12
    BUTTON_RADIUS   = 8
    BUTTON_HEIGHT   = 36
    NAV_BUTTON_H    = 38
