"""
Setup script for creating TinyNotes.app bundle
"""
from setuptools import setup

APP = ['tinynotes.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,
    'plist': {
        'CFBundleName': 'TinyNotes',
        'CFBundleDisplayName': 'TinyNotes',
        'CFBundleIdentifier': 'com.tinynotes.app',
        'CFBundleVersion': '1.0.1',
        'CFBundleShortVersionString': '1.0.1',
        'LSUIElement': True,  # Run as menu bar app without dock icon
        'NSHighResolutionCapable': True,
    },
    'packages': ['rumps'],
    'includes': ['objc', 'Foundation', 'AppKit'],
}

setup(
    name='TinyNotes',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
