# Word Wheel helper

Python program to solve 7-letter word wheels.  
Uses **Hunspell (CLI)** as dictionary backend.

## Prerequisites
- macOS
- Python 3.12 or newer
- Homebrew

### Hunspell (macOS)
Install the Hunspell engine via Homebrew:
```bash
brew install hunspell
```
Verify installation:
```bash
hunspell -v
```

**⚠️ Note**: This project does NOT use Python hunspell bindings (hunspell, cyhunspell).
Those packages are intentionally avoided because they fail to build on modern Python versions.
Instead, the program uses the Hunspell CLI (hunspell -a) via subprocess.

### Installing Hunspell Dictionaries (macOS)
Hunspell installs only the engine. Dictionaries must be installed separately.
This project expects dictionary files (.dic and .aff) in:
```bash
~/Library/Spelling
```
**⚠️ Note**: This path is configurable via .env (HUNSPELL_DIR).


Use the make commands for dict-[de,en,es,fr] or do it manually like this:
```bash
curl -L "https://cgit.freedesktop.org/libreoffice/dictionaries/plain/de/de_DE_frami.dic" \
  -o ~/Library/Spelling/de_DE_frami.dic

curl -L "https://cgit.freedesktop.org/libreoffice/dictionaries/plain/de/de_DE_frami.aff" \
  -o ~/Library/Spelling/de_DE_frami.aff
```

## Config
Rename .env.example to .env:
```bash
cp .env.example .env
```
Add adapt the contents:
```bash
# Where your Hunspell dictionaries live
HUNSPELL_DIR=/Users/YOURNAME/Library/Spelling
# Try these dictionaries in order (first match wins)
HUNSPELL_DICT_CANDIDATES=de_DE_frami,de_DE_neu,de_DE
# Encodings to try when reading .dic
HUNSPELL_DIC_ENCODINGS=utf-8,latin-1,cp1252
# Minimum word length
MINLEN=4
# Enable heuristic word filtering (recommended)
FILTER_REASONABLE=true
# Optional blacklist file (one word per line)
BLACKLIST_PATH=blacklist.txt
```

## Usage
use the Makefile. The install is only required initially. 
```bash
make install

# add at last one dictionary if you did not yet added one.
make dict-[de,en,es,fr]

# use the helper:
make run LETTERS=geifonl MANDATORY=f
```

## Development
Install development dependencies:
```bash
make install-dev
```
Use the Makefile:
```bash
make test
make coverage
```

## Notes
- Base words are loaded from the Hunspell .dic file
- Candidates are prefiltered by: owed letters, mandatory letter, minimum length and optional heuristics (to remove abbreviations / odd forms)
- Final validation is done via Hunspell CLI in batch mode (fast and stable)

Happy solving :)