# Shortcuts CLI Reference

macOS `shortcuts` command-line tool for managing and running shortcuts.

---

## Commands

### shortcuts run

Run a shortcut by name.

```bash
# Basic run
shortcuts run "Shortcut Name"

# Run with text input
shortcuts run "Shortcut Name" -i "input text"

# Run with file input
shortcuts run "Shortcut Name" -i /path/to/file

# Run with output to file
shortcuts run "Shortcut Name" -o /path/to/output

# Run with stdin/stdout
echo "hello" | shortcuts run "Shortcut Name" | cat

# Run with specific output type
shortcuts run "Shortcut Name" -o output.txt -t public.plain-text
```

**Flags:**

| Flag | Description |
|------|-------------|
| `-i <input>` | Input (text string or file path) |
| `-o <output>` | Output file path |
| `-t <type>` | Output UTI type (e.g., `public.plain-text`, `public.json`) |

### shortcuts list

List all installed shortcuts.

```bash
# List all shortcuts
shortcuts list

# List with folder names
shortcuts list --show-folders

# Output as JSON (if supported)
shortcuts list
```

### shortcuts sign

Sign a shortcut for distribution.

```bash
# Sign for anyone (public distribution)
shortcuts sign -m anyone -i unsigned.shortcut -o signed.shortcut

# Sign for sharing (requires Apple ID)
shortcuts sign -m people-who-know-me -i unsigned.shortcut -o signed.shortcut
```

**Flags:**

| Flag | Description |
|------|-------------|
| `-m <mode>` | Signing mode: `anyone`, `people-who-know-me` |
| `-i <input>` | Input unsigned shortcut file |
| `-o <output>` | Output signed shortcut file |

**Requirements:**
- Active iCloud session (Apple ID signed in)
- Network connectivity (iCloud notarization)
- macOS with Shortcuts framework

**Common errors:**
- `NSInvalidArgumentException` — malformed plist (check `WFWorkflowClientVersion` is String)
- Network/iCloud errors — check connectivity and Apple ID

### shortcuts view

View shortcut details (if supported on your macOS version).

```bash
shortcuts view "Shortcut Name"
```

---

## Import / Install

```bash
# Import a signed shortcut (opens Shortcuts app with import dialog)
open signed.shortcut

# Direct import via shortcuts command
shortcuts import signed.shortcut
```

---

## File Locations

| Item | Path |
|------|------|
| User shortcuts database | `~/Library/Shortcuts/` |
| Shortcuts SQLite DB | `~/Library/Shortcuts/Shortcuts.sqlite` (TCC protected) |
| WorkflowKit framework | `/System/Library/PrivateFrameworks/WorkflowKit.framework/` |
| Gallery shortcuts | `.../WorkflowKit.framework/Versions/A/Resources/Gallery.bundle/Contents/Resources/` |
| Gallery index | `.../Gallery.bundle/Contents/Resources/gallery.plist` |
| WritingTools extension | `/System/Library/ExtensionKit/Extensions/WritingToolsAppIntentsExtension.appex` |
| ContentKit framework | `/System/Library/PrivateFrameworks/ContentKit.framework/` |

---

## plist Utilities

```bash
# Validate plist structure
plutil -lint unsigned.shortcut

# Convert binary plist to XML (for debugging)
plutil -convert xml1 -o debug.xml unsigned.shortcut

# Convert XML to binary
plutil -convert binary1 -o binary.plist debug.xml

# Print plist as JSON
plutil -convert json -o - unsigned.shortcut | python3 -m json.tool

# Extract value
plutil -extract WFWorkflowClientVersion raw unsigned.shortcut
```

---

## iCloud API

Download shortcuts shared via iCloud links:

```bash
# Get shortcut metadata (returns JSON with download URL)
curl -s "https://www.icloud.com/shortcuts/api/records/SHORTCUT_ID"

# Extract download URL from response
curl -s "https://www.icloud.com/shortcuts/api/records/SHORTCUT_ID" | \
    python3 -c "import json,sys; print(json.load(sys.stdin)['fields']['shortcut']['value']['downloadURL'])"

# Download the actual .shortcut file
curl -L -o shortcut.shortcut "DOWNLOAD_URL"
```

**Note:** Vanity URLs (e.g., `/shortcuts/getstartedwithmodels`) are iOS deep links — they open the Shortcuts app directly and cannot be resolved via the web API. Use the Gallery.bundle files on macOS instead.

---

## Agent Integration Pattern

For agents running shortcuts programmatically:

```bash
# Build → Validate → Sign → Run
python3 build_shortcut.py && \
plutil -lint unsigned.shortcut && \
shortcuts sign -m anyone -i unsigned.shortcut -o signed.shortcut && \
shortcuts import signed.shortcut && \
shortcuts run "My Shortcut" -i "input data" -o result.txt
```
