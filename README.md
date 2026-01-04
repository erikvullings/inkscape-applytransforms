# inkscape-applytransforms
An Inkscape extension which recursively applies transformations to shapes.

Note that performing this operation on certain shapes (stars, lpes, ...) will convert them to paths,
and clones are affected in strange ways due to clone transforms behave.

**update 2020-7-27** - updated to work with Inkscape 1.0+. Use legacy branch `inkscape-pre1.0-compat` for prior version of Inkscape.

**update 2016-1-5** - now only affects selected shapes when there is an active selection.

## Installation

Download `applytransform.inx` and `applytransform.py`, then copy them to the Inkscape installation folder subdirectory `share\inkscape\extensions`.
  * On Windows this may be `C:\Program Files\Inkscape\share\inkscape\extensions` (or `%appdata%\inkscape\extensions` if you don't want to install globally)
  * On Ubuntu, this may be `/usr/share/inkscape/extensions/` or (`~/.config/inkscape/extensions` if you don't want to install globally)
  * On macOS, this may be `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions`
  * Generally, you should be able to go to the Inkscape Preferences, select `System`, and see the path for `User extensions`
  
If the downloaded files have `.txt` suffixes added by GitHub, be sure to remove them. Restart Inkscape if it's running.

### Arch Linux
This package is also available via the [AUR](https://aur.archlinux.org/packages/inkscape-applytransforms-git/).
```bash
pacaur -S inkscape-applytransforms-git
```

## Usage

Activate the extension from the main menu:

> Extensions | Modify Path | Apply Transform

or use it from the command line. The id of the extension is automatically available as an action:

> `inkscape -g --actions com.klowner.filter.apply-transform test.svg`

or for older versions of Inkscape:

> `inkscape -g --verb com.klowner.filter.apply_transform test.svg`

## Changes

This version includes a number of improvements and bug fixes from the original repository, including:

*   **Text and Tspan Transformation:** Now correctly applies transformations to `text` and `tspan` elements, including scaling of font size.
*   **Rectangle Scaling Fix:** Corrected the scaling logic for rectangles.
*   **Stroke Width Scaling Fix:** Improved stroke width scaling to handle both `style` and direct attributes.
*   **ValueError Fix:** Made the `scaleMultiple` function more robust to prevent a `ValueError`.
*   **Improved Circle and Ellipse Handling:** Simple transformations (translation and uniform scaling) are now applied to circles and ellipses without issuing a warning. Warnings are only shown for complex transformations that might distort the shape.
*   **clipPath and linearGradient Handling:** Added basic handling for `clipPath` and `linearGradient` elements. The extension will now apply the transform to the element and issue a warning.
*   **Testing:** The extension is now tested, and all tests are passing.
