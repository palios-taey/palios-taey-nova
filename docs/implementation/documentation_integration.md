# Implementation Guide: Documentation System Integration

## Purpose
This guide provides instructions for integrating the PALIOS-TAEY documentation system with existing development workflows and processes.

## Prerequisites
- Existing PALIOS-TAEY repository
- Bash shell environment
- Basic understanding of markdown formatting
- Permission to modify documentation and scripts

## Implementation Steps
1. **Install Documentation Structure**
   ```bash
   # Create required directories - copy entire box
   mkdir -p docs/claude docs/ai-ai docs/framework docs/charter docs/protocols docs/implementation docs/deployment docs/history docs/templates
   mkdir -p scripts/documentation
   ```

2. **Install Automation Scripts**
   ```bash
   # Set permissions for all documentation scripts - copy entire box
   chmod +x scripts/documentation/*.sh
   ```

3. **Generate Initial Mapping**
   ```bash
   # Run the mapping generator - copy entire box
   ./scripts/documentation/generate_mapping.sh
   ```

4. **Review and Adjust Mapping**
   - Open docs/document_mapping.txt
   - Review the generated mappings
   - Adjust as needed for your specific documentation structure

5. **Run Reorganization (Dry Run)**
   ```bash
   # Perform a dry run of the reorganization - copy entire box
   ./scripts/documentation/reorganize_documents.sh -m docs/document_mapping.txt -d
   ```

6. **Run Actual Reorganization**
   ```bash
   # Perform the actual reorganization - copy entire box
   ./scripts/documentation/reorganize_documents.sh -m docs/document_mapping.txt
   ```

7. **Verify Document Structure**
   ```bash
   # Verify documentation structure - copy entire box
   ./scripts/documentation/verify_document.sh -d docs
   ```

8. **Generate Documentation Statistics**
   ```bash
   # Generate statistics on the new structure - copy entire box
   ./scripts/documentation/doc_stats.sh
   ```

## Integration with Development Workflow

### CI/CD Integration
Add documentation verification to your CI/CD pipeline:

```yaml
# Documentation verification job
documentation-verification:
  runs-on: ubuntu-latest
  steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Verify documentation
      run: ./scripts/documentation/verify_document.sh -d docs
    
    - name: Generate documentation statistics
      run: ./scripts/documentation/doc_stats.sh
```

### Pre-Commit Hooks
Set up a pre-commit hook to verify documentation changes:

```bash
# Create pre-commit hook for documentation verification - copy entire box
cat > .git/hooks/pre-commit <<'EOF'
#!/bin/bash

# Get a list of staged markdown files in the docs directory
STAGED_DOCS=$(git diff --cached --name-only --diff-filter=ACMR | grep "^docs/.*\.md$")

if [ -n "$STAGED_DOCS" ]; then
  echo "Verifying documentation changes..."
  
  # Check each staged document
  for doc in $STAGED_DOCS; do
    ./scripts/documentation/verify_document.sh -f "$doc"
    if [ $? -ne 0 ]; then
      echo "Documentation verification failed for $doc"
      echo "Please fix the issues before committing"
      exit 1
    fi
  done
fi

exit 0
EOF

chmod +x .git/hooks/pre-commit
```

### Documentation Review Process
Implement a documentation review process in your pull request template:

```markdown
## Documentation Changes
- [ ] Documentation follows the established templates
- [ ] All commands are isolated in individual code blocks
- [ ] Verification steps are included for all commands
- [ ] Internal links have been verified
- [ ] Documentation has been verified with verify_document.sh
```

## Troubleshooting

### Broken Links After Reorganization
If you encounter broken links after reorganization:

```bash
# Find and report all broken links - copy entire box
find docs -name "*.md" -type f -exec grep -l "\[.*\](\/docs\/.*\.md)" {} \; | while read -r file; do
  links=$(grep -o '\[.*\](\/docs\/.*\.md)' "$file" | sed 's/.*(\(\/docs\/.*\.md\))/\1/')
  for link in $links; do
    link_path="${link:1}"
    if [ ! -f "$link_path" ]; then
      echo "Broken link in $file: $link"
    fi
  done
done
```

### Template Issues
If you encounter issues with document templates:

1. Verify template files exist in docs/templates/
2. Check permissions on template files
3. Run the create_document.sh script with debug output:
   ```bash
   bash -x ./scripts/documentation/create_document.sh -t claude -n test_doc -p docs/claude
   ```

### Script Permission Issues
If you encounter permission issues with scripts:

```bash
# Reset permissions on all scripts - copy entire box
find scripts/documentation -name "*.sh" -exec chmod +x {} \;
```

## Related Components
- [Document Structure](/docs/claude/document_structure.md): Comprehensive documentation structure
- [Quality Protocol](/docs/claude/documentation_quality_protocol.md): Documentation quality guidelines
- [Templates Directory](/docs/templates/): Document templates
