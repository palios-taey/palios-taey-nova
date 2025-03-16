#!/bin/bash

# Script to verify documentation system setup

echo "Verifying PALIOS-TAEY Documentation System Setup..."
echo "------------------------------------------------"

# Check directory structure
echo "Checking directory structure..."
DIRECTORIES=(
  "docs/claude"
  "docs/ai-ai"
  "docs/framework"
  "docs/charter"
  "docs/protocols"
  "docs/implementation"
  "docs/deployment"
  "docs/history"
  "docs/templates"
  "scripts/documentation"
)

for dir in "${DIRECTORIES[@]}"; do
  if [ -d "$dir" ]; then
    echo "✓ $dir exists"
  else
    echo "✗ ERROR: $dir does not exist"
  fi
done

# Check template files
echo -e "\nChecking template files..."
TEMPLATES=(
  "docs/templates/claude_template.md"
  "docs/templates/ai_ai_template.md"
  "docs/templates/framework_template.md"
  "docs/templates/implementation_template.md"
)

for template in "${TEMPLATES[@]}"; do
  if [ -f "$template" ]; then
    echo "✓ $template exists"
  else
    echo "✗ ERROR: $template does not exist"
  fi
done

# Check script files
echo -e "\nChecking script files..."
SCRIPTS=(
  "scripts/documentation/create_document.sh"
  "scripts/documentation/update_document.sh"
  "scripts/documentation/verify_document.sh"
  "scripts/documentation/reorganize_documents.sh"
  "scripts/documentation/generate_mapping.sh"
  "scripts/documentation/doc_stats.sh"
  "scripts/documentation/verify_setup.sh"
)

for script in "${SCRIPTS[@]}"; do
  if [ -f "$script" ]; then
    if [ -x "$script" ]; then
      echo "✓ $script exists and is executable"
    else
      echo "⚠ WARNING: $script exists but is not executable"
    fi
  else
    echo "✗ ERROR: $script does not exist"
  fi
done

# Check core documentation files
echo -e "\nChecking core documentation files..."
CORE_DOCS=(
  "docs/claude/document_structure.md"
  "docs/claude/documentation_quality_protocol.md"
  "docs/README.md"
  "docs/documentation_status.md"
)

for doc in "${CORE_DOCS[@]}"; do
  if [ -f "$doc" ]; then
    echo "✓ $doc exists"
  else
    echo "✗ ERROR: $doc does not exist"
  fi
done

# Check mapping file
echo -e "\nChecking document mapping file..."
if [ -f "docs/document_mapping.txt" ]; then
  mapping_count=$(grep -v "^#" "docs/document_mapping.txt" | grep -v "^$" | wc -l)
  echo "✓ docs/document_mapping.txt exists with $mapping_count mappings"
else
  echo "✗ ERROR: docs/document_mapping.txt does not exist"
fi

# Verify script functionality
echo -e "\nVerifying script functionality..."

# Test create_document.sh
if [ -f "scripts/documentation/create_document.sh" ] && [ -x "scripts/documentation/create_document.sh" ]; then
  echo "✓ create_document.sh script is available"
else
  echo "✗ ERROR: create_document.sh script is missing or not executable"
fi

# Test verify_document.sh
if [ -f "scripts/documentation/verify_document.sh" ] && [ -x "scripts/documentation/verify_document.sh" ]; then
  echo "✓ verify_document.sh script is available"
else
  echo "✗ ERROR: verify_document.sh script is missing or not executable"
fi

echo -e "\nDocumentation system verification complete!"
echo "Run './scripts/documentation/doc_stats.sh' for detailed documentation statistics."
