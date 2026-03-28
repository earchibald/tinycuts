"""Integration tests: build shortcuts and validate with plutil."""
import os
import sys
import plistlib
import subprocess
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "resources"))

from builder_template import (
    make_shortcut, new_uuid, make_attachment, make_comment,
    make_text_with_variable, make_if_block, make_repeat_count,
)


def _build_and_validate(actions):
    """Build a shortcut plist and validate with plutil -lint. Returns loaded plist."""
    shortcut = make_shortcut("Test Shortcut", actions)
    with tempfile.NamedTemporaryFile(suffix=".shortcut", delete=False) as f:
        plistlib.dump(shortcut, f, fmt=plistlib.FMT_BINARY)
        path = f.name
    try:
        result = subprocess.run(
            ["plutil", "-lint", path],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"plutil -lint failed: {result.stderr}"

        with open(path, "rb") as f:
            return plistlib.load(f)
    finally:
        os.unlink(path)


def test_empty_shortcut_validates():
    """An empty shortcut passes plutil validation."""
    loaded = _build_and_validate([])
    assert loaded["WFWorkflowActions"] == []


def test_notification_shortcut_validates():
    """A shortcut with a comment and notification validates."""
    actions = [
        make_comment("This shortcut shows a notification."),
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
            "WFWorkflowActionParameters": {
                "WFNotificationActionBody": "Hello from test!",
                "WFNotificationActionTitle": "Test",
            },
        },
    ]
    loaded = _build_and_validate(actions)
    assert len(loaded["WFWorkflowActions"]) == 2


def test_variable_wiring_shortcut_validates():
    """A shortcut with variable references validates."""
    clip_uuid = new_uuid()
    actions = [
        make_comment("Get clipboard and show in notification."),
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.getclipboard",
            "WFWorkflowActionParameters": {"UUID": clip_uuid},
        },
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
            "WFWorkflowActionParameters": {
                "WFNotificationActionBody": make_attachment(clip_uuid, "Clipboard"),
                "WFNotificationActionTitle": "Clipboard Contents",
            },
        },
    ]
    loaded = _build_and_validate(actions)
    assert len(loaded["WFWorkflowActions"]) == 3


def test_control_flow_shortcut_validates():
    """A shortcut with if/repeat validates."""
    notify = {
        "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
        "WFWorkflowActionParameters": {
            "WFNotificationActionBody": "Inside block",
        },
    }
    if_actions = make_if_block("Has Any Value", None, [notify])
    repeat_actions = make_repeat_count(3, [notify])
    all_actions = [make_comment("Control flow test.")] + if_actions + repeat_actions
    _build_and_validate(all_actions)


def test_text_with_variable_shortcut_validates():
    """A shortcut with WFTextTokenString validates."""
    clip_uuid = new_uuid()
    actions = [
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.getclipboard",
            "WFWorkflowActionParameters": {"UUID": clip_uuid},
        },
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.notification",
            "WFWorkflowActionParameters": {
                "WFNotificationActionBody": make_text_with_variable(
                    "You copied: ", clip_uuid, "Clipboard"
                ),
            },
        },
    ]
    _build_and_validate(actions)
