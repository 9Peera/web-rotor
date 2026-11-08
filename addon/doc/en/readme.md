# Web Rotor for NVDA

Web Rotor adds a VoiceOver-style rotor to NVDA for quickly exploring the elements of a web page.
It supports 23 categories, which you can choose and reorder yourself. Each category is a tab,
you can type a letter to jump to an item, and category shortcuts work with both English and Thai
keyboard layouts. The interface is available in English and Thai.

Author: Peera Pilarit (peera@cfbt.or.th)
Version: 1.8.0

## Opening the rotor

1. Open a web page in a browser supported by NVDA (Chrome, Firefox, Edge, etc.).
2. Make sure you are in **browse mode**, not focus mode.
3. Press **Control+Windows+U** (or **NVDA+F7** if you enabled that option in the settings).

Focus starts in the **list of the first category**, so you can use the arrow keys or type a letter right away.
Each category is a tab above the list.

## Keys in the rotor window

| Key | Action |
|---|---|
| Up / Down arrow | Move through the items of the current category |
| Type a letter (in the list) | Jump to the next item starting with that letter. Press the same letter again to move to the next match, or type several letters quickly to search for a word. Works with Thai and English letters. A short beep means no match. |
| Left / Right arrow (in the list) | Change category (wraps around in the order set in the settings). NVDA reads the category name, the number of items and the first item. |
| Shift+Tab (from the list) | Move to the category tabs. Use Left/Right arrow to choose a tab, then Tab to return to its list. |
| **Alt+letter** | Jump straight to a category (see the table below). Works with English and Thai layouts, from anywhere in the window. |
| **Enter** or **Space** | Move to the selected element in the page and close the window. **Enter works from anywhere in the window**, on the tabs or in the list. |
| Escape | Close the window without doing anything |

Other NVDA commands keep working while the rotor is open (default). The settings include an
experimental option to block them temporarily. It is **off by default** because it can conflict with
some other add-ons and make NVDA stop responding.

## Alt+letter shortcuts per category

Both columns always work, whatever interface language you chose: with an English keyboard layout
use the English column, with a Thai layout use the Thai column. You do not need to switch layouts first.

| Category | English | Thai |
|---|---|---|
| Headings | Alt+H | Alt+ห |
| Links (all) | Alt+K | Alt+ล |
| Visited links | Alt+V | Alt+ข |
| Unvisited links | Alt+U | Alt+ค |
| Landmarks | Alt+D | Alt+จ |
| Main landmark | Alt+M | Alt+ง |
| Buttons | Alt+B | Alt+ป |
| Form fields (all) | Alt+O | Alt+ช |
| Edit fields | Alt+E | Alt+ฉ |
| Checkboxes | Alt+X | Alt+ซ |
| Radio buttons | Alt+R | Alt+ญ |
| Combo boxes | Alt+C | Alt+ฎ |
| Tables | Alt+T | Alt+ต |
| Lists | Alt+L | Alt+ร |
| List items | Alt+I | Alt+ฏ |
| Graphics | Alt+G | Alt+ฐ |
| Block quotes | Alt+Q | Alt+ณ |
| Frames | Alt+N | Alt+ฟ |
| Separators | Alt+S | Alt+ด |
| Embedded objects | Alt+J | Alt+อ |
| Annotations | Alt+A | Alt+ถ |
| Paragraphs | Alt+P | Alt+ย |
| Articles | Alt+Z | Alt+บ |

Shortcuts only work for categories that are enabled in the settings.

By default the first 7 categories are enabled (headings, links, landmarks, buttons, form fields,
tables, lists). You can enable the others in the settings.

## Settings

Open the settings with **Control+Windows+Shift+U**, or from the NVDA menu (NVDA+N) > Preferences >
**Web Rotor settings...**

- **Language**: show Web Rotor in **English** (default) or **Thai**. This is separate from NVDA's own language.
- **Categories**: check or uncheck each category, and use **Move up** / **Move down** to set the order
  used by Left/Right arrow in the rotor.
- **Restore defaults**: go back to the 7 standard categories.
- **Use NVDA+F7 to open Web Rotor instead of NVDA's standard Elements List** (off by default).
- **Block other NVDA commands while Web Rotor is open** (experimental, off by default). If NVDA stops
  responding with this option enabled, turn it off.

All settings are saved and apply the next time you open the rotor.

## Technical notes

Web Rotor uses NVDA's internal `treeInterceptor._iterNodesByType()`, the same mechanism as the standard
Elements List (NVDA+F7), so it works in every browser where NVDA supports browse mode.

Some categories (such as paragraphs, articles or frames) may be empty on some sites or browsers,
depending on how the browser reports the page structure to NVDA. This is normal.

A category with more than 2,000 elements is cut off at the first 2,000 to keep NVDA responsive.
