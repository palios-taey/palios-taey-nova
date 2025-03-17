{
  "protocol_id": "ECv",
  "version": "1.0",
  "creation_date": "2025-03-15",
  "status": "ACTIVE",
  "priority": "CRITICAL",
  "implementation_stage": "IMMEDIATE",
  "fields": [
    {"name": "checkpoint_version", "format": "ECv[#]", "required": true},
    {"name": "mode", "format": "[EXEC/REFL]", "required": true},
    {"name": "github_updated", "format": "GH: [Y/N]", "required": true},
    {"name": "commit_message", "format": "CM: \"[PTV[#]]\"", "required": true},
    {"name": "changes", "format": "Δ: [description]", "required": true},
    {"name": "result", "format": "R: [S/F/P]", "required": true},
    {"name": "focus", "format": "F: [focus]", "required": true}
  ],
  "behavior": {
    "EXEC": "Continue execution plan after status review",
    "REFL": "Pause execution for discussion and direction"
  },
  "evolution_potential": "HIGH",
  "optimization_target": "HUMAN_EFFICIENCY"
}
