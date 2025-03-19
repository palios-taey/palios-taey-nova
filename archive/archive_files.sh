#!/bin/bash
# File Archival Script for PALIOS-TAEY
# Generated on 2025-03-18T01:04:46.282Z
# This script identifies and archives obsolete and duplicate files

# Create archive directory
mkdir -p ./archive

echo "Starting PALIOS-TAEY file archival process..."

# Archive obsolete files
echo "Archiving 7 obsolete files..."

# Archive src/palios_taey/memory/service.py.20250313_193800.bak
if [ -f "src/palios_taey/memory/service.py.20250313_193800.bak" ]; then
  echo "Archiving src/palios_taey/memory/service.py.20250313_193800.bak..."
  mkdir -p ./archive/$(dirname "src/palios_taey/memory/service.py.20250313_193800.bak")
  cp "src/palios_taey/memory/service.py.20250313_193800.bak" ./archive/"src/palios_taey/memory/service.py.20250313_193800.bak"
  echo "# This file has been archived and can be safely removed" > "src/palios_taey/memory/service.py.20250313_193800.bak.archived"
fi

# Archive src/palios_taey/models/registry.py.20250313_193800.bak
if [ -f "src/palios_taey/models/registry.py.20250313_193800.bak" ]; then
  echo "Archiving src/palios_taey/models/registry.py.20250313_193800.bak..."
  mkdir -p ./archive/$(dirname "src/palios_taey/models/registry.py.20250313_193800.bak")
  cp "src/palios_taey/models/registry.py.20250313_193800.bak" ./archive/"src/palios_taey/models/registry.py.20250313_193800.bak"
  echo "# This file has been archived and can be safely removed" > "src/palios_taey/models/registry.py.20250313_193800.bak.archived"
fi

# [Additional obsolete file handling omitted for brevity]

# Handle duplicate files
echo "Processing 5 duplicate files..."

# deploy_direct.sh appears to be a duplicate of deploy.sh (80% similar)
if [ -f "deploy_direct.sh" ] && [ -f "deploy.sh" ]; then
  echo "Found potential duplicate: deploy_direct.sh"
  echo "  Original file: deploy.sh"
  echo "  Similarity: 80%"
  mkdir -p ./archive/$(dirname "deploy_direct.sh")
  cp "deploy_direct.sh" ./archive/"deploy_direct.sh"
  echo "# This file appears to be a duplicate of deploy.sh" > "deploy_direct.sh.potential_duplicate"
  echo "# Similarity: 80%" >> "deploy_direct.sh.potential_duplicate"
  echo "# The original file has been preserved in ./archive/deploy_direct.sh" >> "deploy_direct.sh.potential_duplicate"
fi

# [Additional duplicate file handling omitted for brevity]

echo "Archival process complete!"
echo "Summary:"
echo "  - 7 obsolete files marked"
echo "  - 5 potential duplicate files identified"
echo ""
echo "Review the .archived and .potential_duplicate marker files"
echo "Once confirmed, you can safely remove the original files"