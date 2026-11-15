# HUD design
No transparency, solid flat colours.

Reference images in this folder:
- ref_01.jpg - High contrast colour scheme, modern round corners
- ref_02.jpg - Dark mode colour use. Dark background, High contrast text, colourful accent, muted grey for backgrounds
- ref_03.jpg - High contrast colour scheme, modern round corners, mono space font use
- colour_scheme.jpg - 4 colours + black.

## Must stay
- grid overlay but colours can be adjusted to match.
- a monospace font makes sense 
- solid flat colours only, no transparency (only the 4 hex codes of colour_scheme.jpg; the preview shows through where nothing is drawn)
- HUD_COLOR_DARK (111111) bars at top and bottom behind the data fields; the grid runs behind the bars, never over text

## Free to change
- data fields shown 
- current colours

## Data fields shown in HUD
- Date + time
- gain
- whitebalance
- capture resolution
- capture format e.g. Jpeg + RAW


## Open questions
- how to get battery status?
- ~~neat way to access a settings menu~~: MENU button bottom right opens a full-screen touch menu (`menu.py`); resolution + format so far, filters etc. not yet
