"""Part 2 schema for the non-deterministic hypotension finding.

This is the SDK equivalent of Part 1's `Output Contract` prose in
intradialytic-hypotension-review/SKILL.md. The difference: this one is
enforced by the API via a forced tool call, not just requested in text.
"""

JUDGMENT_POINT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["documented", "evidence_gap"],
        },
        "citation": {
            "type": "string",
            "description": "Exact quoted text supporting the status, or empty string if evidence_gap.",
        },
    },
    "required": ["status", "citation"],
}

FINDING_TOOL = {
    "name": "submit_hypotension_finding",
    "description": (
        "Submit the four-point judgment on whether a synthetic ICHD "
        "hypotension event was adequately documented. Call this exactly "
        "once with your final judgment -- do not call it speculatively."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "trigger_present": {
                "type": "boolean",
                "description": "True if treatment_note documents a hypotension-type event at all.",
            },
            "judgment_points": {
                "type": "object",
                "properties": {
                    "recognized": JUDGMENT_POINT_SCHEMA,
                    "corrective_action": JUDGMENT_POINT_SCHEMA,
                    "reassessed": JUDGMENT_POINT_SCHEMA,
                    "physician_notified": JUDGMENT_POINT_SCHEMA,
                },
                "required": [
                    "recognized",
                    "corrective_action",
                    "reassessed",
                    "physician_notified",
                ],
            },
            "draft_question": {
                "type": "string",
                "description": "The question routed to the human reviewer.",
            },
            "prohibited_inference": {
                "type": "string",
                "description": "Standard disclaimer: no diagnosis/code/severity/payment inferred.",
            },
        },
        "required": [
            "trigger_present",
            "judgment_points",
            "draft_question",
            "prohibited_inference",
        ],
    },
}
