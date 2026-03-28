# Shortcuts Reference Documentation

Agent-optimized reference for macOS Shortcuts authoring. Start with the doc most relevant to your task.

## Documents

| Document | Use When |
|----------|----------|
| [format-reference.md](format-reference.md) | Understanding the .shortcut plist structure, top-level keys, serialization types |
| [action-catalog.md](action-catalog.md) | Looking up action identifiers and their parameter schemas |
| [variable-system.md](variable-system.md) | Wiring action outputs, embedding variables in text, aggrandizements |
| [apple-intelligence.md](apple-intelligence.md) | Using AI actions (askllm, Writing Tools), model selection, output types |
| [cli-reference.md](cli-reference.md) | Running, signing, importing shortcuts from the command line |
| [real-shortcut-patterns.md](real-shortcut-patterns.md) | Common patterns from production shortcuts — copy and adapt |

## Quick Start for Agents

1. Read **format-reference.md** for plist structure basics
2. Look up actions in **action-catalog.md** (friendly name → identifier table at top)
3. Wire variables using patterns from **variable-system.md**
4. For AI shortcuts, consult **apple-intelligence.md**
5. Use **real-shortcut-patterns.md** as templates for common workflows
6. Build, sign, and test with **cli-reference.md**

## Sources

- 41 production shortcuts from Apple gallery and iCloud
- Apple WorkflowKit, ContentKit, WritingToolsAppIntentsExtension frameworks
- Community projects: Cherri, shortcuts-js, iOS-Shortcuts-Reference
- Zachary7829 format documentation
