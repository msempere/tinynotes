# TinyNotes

A simple macOS menu bar application for quick note-taking.

## Installation

Install via Homebrew:

```bash
brew tap msempere/tinynotes
brew install --cask tinynotes
```

The app will appear in your menu bar as a pencil icon.

**Note**: On first launch, macOS may show a dialog asking "Are you sure you want to open this?" because the app is not code-signed. Click "Open" to proceed.

## Usage

### Creating Notes

Click the menu bar icon and select "New Note". Type your note with an optional title on the first line. Close the window to save automatically.

### Managing Notes

- Click any note in the menu to edit it
- Clear all content to delete a note
- Notes are sorted by most recently modified
- Use "Open Note File..." to import external notes
- Toggle "Start at Login" to launch TinyNotes automatically

### Note Format

```
Title (optional first line)
Content goes here
With multiple lines supported
```

If no title is provided, notes display as "Untitled" with a timestamp.

## Storage

Notes are stored in `~/TinyNotes/` as individual JSON files with readable filenames:

```
2026-03-25T12-30-45-123456_shopping-list.json
2026-03-25T14-15-00-789012_meeting-notes.json
```

## Building from Source

### Requirements

- macOS 10.10 or later
- Homebrew Python 3.7+

### Setup

```bash
/opt/homebrew/bin/python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./run.sh
```

### Building Distribution

```bash
./venv/bin/pip install py2app
./build-release.sh 1.0.0
```

The standalone app will be created in `dist/TinyNotes.app`.

## Technical Details

- Built with rumps and PyObjC
- Single instance enforcement via lock file
- Auto-save on window close
- ESC key closes and saves

## License

MIT License - see LICENSE file for details.
