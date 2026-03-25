#!/usr/bin/env python3
"""
TinyNotes - A simple macOS menu bar app for quick note-taking
"""
import os
import sys
import json
import rumps
from datetime import datetime
from pathlib import Path
from AppKit import (
    NSWindow, NSTextView, NSMakeRect, NSClosableWindowMask, NSTitledWindowMask,
    NSScrollView, NSApp, NSOpenPanel
)
from Foundation import NSObject, NSURL, NSBundle
import objc
import atexit
import subprocess


class Note:
    """Represents a single note"""

    def __init__(self, title=None, content="", created_at=None, last_modified=None):
        self.created_at = created_at or datetime.now().isoformat()
        self.content = content
        self._title = title
        self.last_modified = last_modified or self.created_at

    @property
    def title(self):
        """Returns the title or generates one from the timestamp"""
        if self._title:
            return self._title
        # Parse ISO format and create readable title
        dt = datetime.fromisoformat(self.created_at)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @title.setter
    def title(self, value):
        self._title = value

    def to_dict(self):
        """Convert note to dictionary for JSON serialization"""
        return {
            'title': self._title,
            'content': self.content,
            'created_at': self.created_at,
            'last_modified': self.last_modified
        }

    @classmethod
    def from_dict(cls, data):
        """Create note from dictionary"""
        return cls(
            title=data.get('title'),
            content=data.get('content', ''),
            created_at=data.get('created_at'),
            last_modified=data.get('last_modified', data.get('created_at'))  # Fallback for old notes
        )


class NoteWindowController(NSObject):
    """Controller for note window"""

    def init(self):
        self = objc.super(NoteWindowController, self).init()
        if self is None:
            return None
        self.app = None
        self.note = None
        self.text_view = None
        self.is_new_note = False
        self.window = None
        self.saved = False  # Track if we already saved
        self.original_content = ""  # Track original content to detect changes
        return self

    @objc.python_method
    def setup(self):
        """Setup after init"""
        print(f"DEBUG: Controller setup complete. Has window: {self.window is not None}")

    def windowWillClose_(self, notification):
        """Called when window is about to close - save the note"""
        if not self.saved:
            print("DEBUG: windowWillClose_ called - checking if need to save")

            current_content = str(self.text_view.string()).rstrip()

            # Only save if content changed or it's a new note with content
            if current_content != self.original_content:
                print("DEBUG: Content changed, saving")
                self.save_note()
            else:
                print("DEBUG: No changes, not saving")

            self.saved = True
        else:
            print("DEBUG: windowWillClose_ called - already saved, skipping")

        # Remove from open windows list
        if self in self.app.open_windows:
            self.app.open_windows.remove(self)

    def windowShouldClose_(self, sender):
        """Called to ask if window should close"""
        # Don't save here, let windowWillClose_ handle it
        print("DEBUG: windowShouldClose_ called - allowing close")
        return objc.YES

    def cancelOperation_(self, sender):
        """Called when ESC key is pressed"""
        print("DEBUG: ESC pressed - closing window")
        if self.window:
            self.window.close()

    def save_note(self):
        """Save the note"""
        print("DEBUG: save_note called")

        if not self.text_view or not self.app:
            print("DEBUG: Missing text_view or app")
            return

        # Don't strip yet - we need to detect empty first lines
        content = str(self.text_view.string())
        # Only strip trailing whitespace, keep leading newlines to detect empty titles
        content = content.rstrip()

        print(f"DEBUG: Content = '{repr(content)}'")

        if not content:
            # Empty note - delete if it exists
            print("DEBUG: Empty note")
            if not self.is_new_note and self.note in self.app.notes:
                self.app.notes.remove(self.note)
                self.app.delete_note(self.note)
                self.app.build_menu()
            return

        # Parse first line as title
        lines = content.split('\n', 1)
        first_line = lines[0].strip()

        if self.is_new_note:
            # New note - create timestamp
            now = datetime.now()
            datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
            self.note.created_at = now.isoformat()
            self.note.last_modified = now.isoformat()

            if len(lines) > 1:
                # Has multiple lines
                if first_line:
                    # First line has content - it's the title
                    self.note._title = f"{first_line} ({datetime_str})"
                    self.note.content = lines[1].rstrip()
                    print(f"DEBUG: Multi-line note with title. Title: '{self.note._title}'")
                else:
                    # First line is empty - no title
                    self.note._title = None
                    self.note.content = lines[1].rstrip()
                    print(f"DEBUG: Multi-line note without title. Content: '{lines[1][:30]}'")
            else:
                # Single line - that's the content, no title
                self.note._title = None
                self.note.content = first_line
                print(f"DEBUG: Single-line note. Content: '{first_line}', will use datetime title")

            self.app.notes.append(self.note)
            print("DEBUG: Added new note")
        else:
            # Existing note - update last_modified
            now = datetime.now()
            self.note.last_modified = now.isoformat()

            if len(lines) > 1:
                # Multiple lines
                if first_line:
                    # First line has content - it's the title
                    if self.note._title:
                        # Had a title before - update it but keep datetime
                        original_title = self.note._title
                        if ' (' in original_title:
                            # Keep the datetime from original
                            self.note._title = f"{first_line} {original_title[original_title.rfind('('):]}"
                        else:
                            # Shouldn't happen, but add datetime
                            datetime_str = datetime.fromisoformat(self.note.created_at).strftime("%Y-%m-%d %H:%M:%S")
                            self.note._title = f"{first_line} ({datetime_str})"
                    else:
                        # Didn't have a title before - add one now with original created_at
                        datetime_str = datetime.fromisoformat(self.note.created_at).strftime("%Y-%m-%d %H:%M:%S")
                        self.note._title = f"{first_line} ({datetime_str})"
                        print(f"DEBUG: Added title to titleless note: '{self.note._title}'")

                    self.note.content = lines[1].rstrip()
                    print(f"DEBUG: Updated multi-line note. Title: '{self.note._title}'")
                else:
                    # First line is empty - remove title if it had one
                    self.note._title = None
                    self.note.content = lines[1].rstrip()
                    print(f"DEBUG: Removed title from note")
            else:
                # Single line update
                self.note._title = None
                self.note.content = first_line
                print(f"DEBUG: Updated single-line note")

        self.app.save_note(self.note)
        self.app.build_menu()

        print(f"DEBUG: Total notes: {len(self.app.notes)}")

        rumps.notification(
            title="TinyNotes",
            subtitle="Note saved",
            message=self.note.title
        )


class TinyNotesApp(rumps.App):
    """Main application class for TinyNotes"""

    def __init__(self):
        super(TinyNotesApp, self).__init__(
            name="TinyNotes",
            title="✎",  # Pencil icon
            quit_button=None
        )

        # Set up notes directory
        self.notes_dir = Path.home() / "TinyNotes"
        self.notes_dir.mkdir(exist_ok=True)

        # Load existing notes
        self.notes = self.load_notes()

        # Keep track of open windows to prevent garbage collection
        self.open_windows = []

        # Build initial menu
        self.build_menu()

    def load_notes(self):
        """Load notes from individual JSON files"""
        notes = []
        seen_timestamps = set()  # Track timestamps to avoid duplicates

        if not self.notes_dir.exists():
            return notes

        try:
            # Load all .json files from the notes directory
            for note_file in sorted(self.notes_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                with open(note_file, 'r') as f:
                    data = json.load(f)
                    note = Note.from_dict(data)

                    # Only add if we haven't seen this timestamp
                    if note.created_at not in seen_timestamps:
                        notes.append(note)
                        seen_timestamps.add(note.created_at)
                    else:
                        print(f"DEBUG: Skipping duplicate note with timestamp {note.created_at}")
        except Exception as e:
            rumps.alert(f"Error loading notes: {e}")

        return notes

    def save_note(self, note):
        """Save a single note to its own JSON file"""
        try:
            # Create sanitized title for filename
            title_part = ""
            if note._title:
                # Extract just the title part (before datetime if present)
                title_text = note._title.split(' (')[0] if ' (' in note._title else note._title
            else:
                # Use first 30 chars of content
                title_text = note.content[:30] if note.content else "note"

            # Sanitize: lowercase, replace spaces with hyphens, remove special chars
            sanitized = "".join(c if c.isalnum() or c == ' ' else '' for c in title_text)
            sanitized = sanitized.strip().replace(' ', '-').lower()[:50]  # Limit length

            if sanitized:
                title_part = f"_{sanitized}"

            # Use created_at timestamp + title for filename
            timestamp_part = note.created_at.replace(':', '-').replace('.', '-')
            filename = f"{timestamp_part}{title_part}.json"
            filepath = self.notes_dir / filename

            with open(filepath, 'w') as f:
                json.dump(note.to_dict(), f, indent=2)

            print(f"DEBUG: Saved note to {filepath}")
        except Exception as e:
            rumps.alert(f"Error saving note: {e}")

    def delete_note(self, note):
        """Delete a note file"""
        try:
            # Find the note file by timestamp prefix
            timestamp_part = note.created_at.replace(':', '-').replace('.', '-')

            # Look for file that starts with this timestamp
            for filepath in self.notes_dir.glob(f"{timestamp_part}*.json"):
                filepath.unlink()
                print(f"DEBUG: Deleted note file {filepath}")
                break
        except Exception as e:
            rumps.alert(f"Error deleting note: {e}")

    def build_menu(self):
        """Build the menu with notes and actions"""
        # Clear existing menu items
        self.menu.clear()

        # Add recent notes (latest 20, sorted by most recently modified)
        if self.notes:
            recent_notes = sorted(
                self.notes,
                key=lambda n: n.last_modified,
                reverse=True
            )[:20]

            for note in recent_notes:
                # Create a display title
                if note._title:
                    # Has custom title - extract title and datetime parts
                    full_title = note.title
                    if ' (' in full_title:
                        title_part = full_title.split(' (')[0]
                        datetime_part = ' (' + full_title.split(' (')[1]  # Includes the closing )

                        # Truncate title part if needed, but always show datetime
                        max_title_length = 40  # Leave room for datetime (about 22 chars)
                        if len(title_part) > max_title_length:
                            title_part = title_part[:max_title_length - 3] + "..."

                        display_title = title_part + datetime_part
                    else:
                        # Old format without datetime
                        display_title = full_title[:47] + "..." if len(full_title) > 50 else full_title
                else:
                    # No custom title - show "Untitled" + datetime
                    datetime_str = note.title  # This is the auto-generated datetime
                    display_title = f"Untitled {datetime_str}"

                note_item = rumps.MenuItem(
                    display_title,
                    callback=lambda sender, n=note: self.edit_note(n)
                )
                self.menu.add(note_item)
        else:
            self.menu.add(rumps.MenuItem("No notes yet", callback=None))

        # Add separator and "New Note"
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("New Note", callback=self.create_new_note))

        # Add separator and "Open Note File..."
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Open Note File...", callback=self.open_note_file))

        # Add separator and settings
        self.menu.add(rumps.separator)

        # Add "Start at Login" toggle
        start_at_login_item = rumps.MenuItem(
            "Start at Login",
            callback=self.toggle_start_at_login
        )
        start_at_login_item.state = self.is_login_item_enabled()
        self.menu.add(start_at_login_item)

        # Add separator and "Quit TinyNotes"
        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Quit TinyNotes", callback=self.quit_app))

    def create_new_note(self, _=None):
        """Create a new note via menu"""
        self.show_note_window(Note())

    def edit_note(self, note):
        """Edit an existing note"""
        self.show_note_window(note)

    def show_note_window(self, note):
        """Show a simple window for creating/editing a note"""
        is_new_note = note not in self.notes

        # Create window
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 500, 350),
            NSTitledWindowMask | NSClosableWindowMask,
            2,  # NSBackingStoreBuffered
            False
        )

        # Prevent window from terminating app when closed
        window.setReleasedWhenClosed_(False)

        # Make window float on top of all other windows
        window.setLevel_(3)  # NSFloatingWindowLevel

        # Set window title
        if is_new_note:
            window.setTitle_("New Note")
        else:
            window.setTitle_("Edit Note")

        # Center window
        window.center()

        # Create scroll view with text view
        scroll_view = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, 500, 350))
        scroll_view.setHasVerticalScroller_(True)
        scroll_view.setAutoresizingMask_(18)  # Width and height resizable

        text_view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 500, 350))
        text_view.setAutoresizingMask_(2)  # Width resizable

        # Set initial text
        if note._title and note.content:
            # Strip datetime from title for editing (e.g., "title (2026-03-25 12:00:00)" -> "title")
            display_title = note._title
            if ' (' in display_title:
                display_title = display_title.split(' (')[0]
            text_view.setString_(f"{display_title}\n{note.content}")
        elif note.content:
            # No title - show empty first line, then content
            text_view.setString_(f"\n{note.content}")

        scroll_view.setDocumentView_(text_view)

        # Create controller and set as window delegate
        controller = NoteWindowController.alloc().init()
        controller.app = self
        controller.note = note
        controller.text_view = text_view
        controller.is_new_note = is_new_note
        controller.window = window

        # Store original content to detect changes (without datetime for comparison)
        if note._title and note.content:
            display_title = note._title
            if ' (' in display_title:
                display_title = display_title.split(' (')[0]
            controller.original_content = f"{display_title}\n{note.content}"
        elif note.content:
            # No title - empty first line, then content
            controller.original_content = f"\n{note.content}"
        else:
            controller.original_content = ""

        # Keep reference to prevent garbage collection
        self.open_windows.append(controller)

        window.setDelegate_(controller)
        controller.setup()

        # Set content view
        window.setContentView_(scroll_view)

        # Show window, activate app, and set focus
        NSApp.activateIgnoringOtherApps_(True)
        window.makeKeyAndOrderFront_(None)
        window.makeFirstResponder_(text_view)

        print(f"DEBUG: Window created")
        print(f"DEBUG: Window delegate is: {window.delegate()}")
        print(f"DEBUG: Controller object: {controller}")

    def delete_note_ui(self, note):
        """Delete a note via UI"""
        confirm = rumps.alert(
            title="Delete Note",
            message=f"Are you sure you want to delete '{note.title}'?",
            ok="Delete",
            cancel="Cancel"
        )

        if confirm == 1:
            self.notes.remove(note)
            self.delete_note(note)
            self.build_menu()
            rumps.notification(
                title="TinyNotes",
                subtitle="Note deleted",
                message=note.title
            )

    def open_note_file(self, _):
        """Open a note file using file picker"""
        panel = NSOpenPanel.openPanel()
        panel.setTitle_("Open Note File")
        panel.setPrompt_("Open")
        panel.setCanChooseFiles_(True)
        panel.setCanChooseDirectories_(False)
        panel.setAllowsMultipleSelection_(False)
        panel.setAllowedFileTypes_(["json"])
        panel.setLevel_(3)  # Float on top of all windows

        # Set default directory to notes folder
        if self.notes_dir.exists():
            panel.setDirectoryURL_(NSURL.fileURLWithPath_(str(self.notes_dir)))

        # Activate app and show panel
        NSApp.activateIgnoringOtherApps_(True)
        result = panel.runModal()

        if result == 1:  # NSModalResponseOK
            url = panel.URL()
            if url:
                filepath = url.path()
                try:
                    # Load the note from file
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        note = Note.from_dict(data)

                    # Check if note already exists in our list (by created_at timestamp)
                    existing_note = None
                    for n in self.notes:
                        if n.created_at == note.created_at:
                            existing_note = n
                            break

                    if existing_note:
                        # Open existing note
                        self.edit_note(existing_note)
                    else:
                        # Add to notes list and open
                        self.notes.append(note)
                        self.build_menu()
                        self.edit_note(note)

                    print(f"DEBUG: Opened note from file. Total notes now: {len(self.notes)}")

                except Exception as e:
                    rumps.alert(f"Error opening note file: {e}")

    def is_login_item_enabled(self):
        """Check if app is in login items"""
        try:
            result = subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to get the name of every login item'],
                capture_output=True,
                text=True
            )
            login_items = result.stdout.strip()
            return "TinyNotes" in login_items
        except Exception:
            return False

    def toggle_start_at_login(self, sender):
        """Toggle start at login"""
        try:
            if sender.state:
                # Currently enabled, disable it
                subprocess.run([
                    "osascript", "-e",
                    'tell application "System Events" to delete login item "TinyNotes"'
                ])
                sender.state = False
                rumps.notification(
                    title="TinyNotes",
                    subtitle="Start at Login",
                    message="Disabled"
                )
            else:
                # Currently disabled, enable it
                # Get app bundle path
                bundle = NSBundle.mainBundle()
                app_path = bundle.bundlePath()

                subprocess.run([
                    "osascript", "-e",
                    f'tell application "System Events" to make login item at end with properties {{path:"{app_path}", hidden:false}}'
                ])
                sender.state = True
                rumps.notification(
                    title="TinyNotes",
                    subtitle="Start at Login",
                    message="Enabled"
                )
        except Exception as e:
            rumps.alert(f"Error toggling start at login: {e}")

    def quit_app(self, _):
        """Quit the application"""
        rumps.quit_application()


def check_single_instance():
    """Ensure only one instance of TinyNotes is running"""
    lock_file = Path.home() / "TinyNotes" / ".tinynotes.lock"

    # Create notes directory if it doesn't exist
    lock_file.parent.mkdir(exist_ok=True)

    if lock_file.exists():
        try:
            # Read the PID from lock file
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())

            # Check if process is still running
            try:
                os.kill(pid, 0)  # Check if process exists (doesn't actually kill it)
                # Process exists - another instance is running
                rumps.alert(
                    title="TinyNotes Already Running",
                    message="TinyNotes is already running. Only one instance can run at a time."
                )
                sys.exit(0)
            except OSError:
                # Process doesn't exist - stale lock file, remove it
                lock_file.unlink()
        except (ValueError, FileNotFoundError):
            # Invalid or missing lock file, remove it
            if lock_file.exists():
                lock_file.unlink()

    # Create lock file with current PID
    with open(lock_file, 'w') as f:
        f.write(str(os.getpid()))

    # Register cleanup function to remove lock file on exit
    def cleanup_lock():
        if lock_file.exists():
            lock_file.unlink()

    atexit.register(cleanup_lock)


def main():
    """Main entry point"""
    # Check for single instance
    check_single_instance()

    # Start the app
    app = TinyNotesApp()
    app.run()


if __name__ == "__main__":
    main()
