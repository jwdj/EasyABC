![EasyABC logo](img/abclogo.png "EasyABC")

# EasyABC

An open source ABC editor for Windows, OSX and Linux. It is published under the GNU Public License.

## Features

- Good ABC standard coverage thanks to internal use of abcm2ps and abc2midi
- Syntax highlighting
- Zoom support
- Import MusicXML, MIDI and Noteworthy Composer files.
- Export to MIDI, SVG, PDF (single tune or whole tune book).
- Select notes by clicking on them and add music symbols by using drop-down menus in the toolbar.
- Play the active tune as midi (using SoundFont)
- See which notes are currently playing (Follow score)
- Contextual guidance (ABC Assist)
- Record songs from midi directly in the program (no OSX support at the moment).
- Just press Rec, play on your midi keyboard and then press Stop.
- The musical score is automatically updated as you type in ABC code.
- Support for unicode (utf-8) and other encodings.
- Transpose and halve/double note length functionality (using abc2abc)
- An abcm2ps format file can easily be specified in the settings.
- ABC fields in the file header are applied to every single tune in a tune book.
- Automatic alignment of bars on different lines
- Available in Italian, French, Danish, Swedish, Dutch and English
- Functions to generate incipits, sort tunes and renumber X: fields.
- Musical search function - search for note sequences irrespectively of key, etc.

## Credits - software components used by EasyABC

- abcm2ps for converting ABC code to note images (developed/maintained by Jean-François Moine)
- abc2midi for converting ABC code to midi (by James Allwright, maintained by Seymour Shlien)
- xml2abc for converting from MusicXML to ABC (by Willem Vree)
- abc2xml for converting from ABC to ABC (by Willem Vree)
- nwc2xml for converting from Noteworthy Composer format to ABC via XML (by James Lee)
- wxPython cross-platform user-interface framework
- scintilla for the text editor used for ABC code
- python midi package for the initial parsing of midi files to be imported
- pygame (which wraps portmidi) for real-time midi input
- FluidSynth for playing using SoundFonts
- Many thanks to the translators: Valerio Pelliccioni (italian), Bendix Rødgaard (danish), Frédéric Aupépin (french). Universal binaries of abcm2ps and abc2midi for OSX are available thanks to Chuck Boody.

## Links

- [abcnotation.com](https://abcnotation.com)
- [abcplus.sourceforge.net](https://abcplus.sourceforge.net)

## Keyboard shortcuts

- <kbd>F5</kbd> Refresh
- <kbd>F6</kbd> Play current song
- <kbd>F7</kbd> Stop song
- <kbd>Ctrl-Shift-F</kbd> Find in Files (or show entire collection)
