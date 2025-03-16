# PALIOS-TAEY Documentation System

## Overview

This directory contains the complete documentation for the PALIOS-TAEY system, organized in an audience-aware structure that optimizes for both AI and human consumption.

## Directory Structure

```
docs/
├── claude/              # Claude-to-Claude optimized documents
├── ai-ai/               # Cross-model AI documentation
├── framework/           # Core frameworks and methodologies
├── charter/             # Charter and principles
├── protocols/           # Communication and process protocols
├── implementation/      # Technical implementation guides
├── deployment/          # Deployment and operations documentation
├── history/             # Historical records and evolution
└── templates/           # Document templates
```

## Key Documents

- **Document Structure**: [/docs/claude/document_structure.md](/docs/claude/document_structure.md)
- **Quality Protocol**: [/docs/claude/documentation_quality_protocol.md](/docs/claude/documentation_quality_protocol.md)
- **Documentation Status**: [/docs/documentation_status.md](/docs/documentation_status.md)

## Automation Scripts

The documentation system includes automation scripts in `/scripts/documentation/`:

- **create_document.sh**: Create new documents from templates
- **update_document.sh**: Update existing documents
- **verify_document.sh**: Verify document format and links
- **reorganize_documents.sh**: Reorganize documents into the new structure
- **generate_mapping.sh**: Generate a mapping file for reorganization
- **doc_stats.sh**: Generate documentation statistics

## Templates

Standard templates for different document types are available in `/docs/templates/`:

- **claude_template.md**: Template for Claude-to-Claude documents
- **ai_ai_template.md**: Template for AI-AI communication documents
- **framework_template.md**: Template for framework documents
- **implementation_template.md**: Template for implementation guides

## Usage Guidelines

1. **Creating New Documents**: Use the create_document.sh script with the appropriate template
   ```bash
   ./scripts/documentation/create_document.sh -t claude -n document_name -p docs/claude -d "Description"
   ```

2. **Updating Documents**: Use the update_document.sh script
   ```bash
   ./scripts/documentation/update_document.sh -f docs/claude/document_name.md -r
   ```

3. **Verifying Documents**: Use the verify_document.sh script
   ```bash
   ./scripts/documentation/verify_document.sh -d docs/claude
   ```

4. **Document Migration**: Use the reorganize_documents.sh script with a mapping file
   ```bash
   ./scripts/documentation/reorganize_documents.sh -m docs/document_mapping.txt
   ```

## Human Error Prevention

When adding terminal commands to documentation:

1. Place each significant command (especially `cat` commands) in its own code block
2. The command must be the first line in the code block
3. Include a comment indicating "copy entire box" at the end of the first line
4. Provide verification steps after command execution

For detailed guidelines, see the [Documentation Quality Protocol](/docs/claude/documentation_quality_protocol.md).
