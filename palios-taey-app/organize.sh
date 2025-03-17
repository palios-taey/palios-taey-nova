#!/bin/bash
# organize.sh - Reorganize files for deployment

set -e  # Exit on any error

echo "Organizing files for deployment..."

# Find the source directory 
if [ -d "../src" ]; then
  SRC_DIR="../src"
elif [ -d "src" ]; then
  SRC_DIR="src"
else
  echo "ERROR: Could not find src directory"
  exit 1
fi

echo "Found source directory: $SRC_DIR"

# Create local structure if needed
mkdir -p src/palios_taey/core
mkdir -p src/palios_taey/memory
mkdir -p src/palios_taey/models
mkdir -p src/palios_taey/routing
mkdir -p config/model_capabilities

# Create package __init__ files
touch src/__init__.py
touch src/palios_taey/__init__.py
touch src/palios_taey/core/__init__.py
touch src/palios_taey/memory/__init__.py
touch src/palios_taey/models/__init__.py
touch src/palios_taey/routing/__init__.py

# Copy the core files
if [ -d "$SRC_DIR/palios_taey/core" ]; then
  echo "Copying core files..."
  cp $SRC_DIR/palios_taey/core/errors.py src/palios_taey/core/
  cp $SRC_DIR/palios_taey/core/utils.py src/palios_taey/core/
else
  echo "WARNING: Core module not found"
fi

# Copy the memory files
if [ -d "$SRC_DIR/palios_taey/memory" ]; then
  echo "Copying memory files..."
  cp $SRC_DIR/palios_taey/memory/service.py src/palios_taey/memory/
  cp $SRC_DIR/palios_taey/memory/models.py src/palios_taey/memory/
else
  echo "WARNING: Memory module not found"
fi

# Copy the models files
if [ -d "$SRC_DIR/palios_taey/models" ]; then
  echo "Copying models files..."
  cp $SRC_DIR/palios_taey/models/registry.py src/palios_taey/models/
  cp -r $SRC_DIR/palios_taey/models/capabilities* config/model_capabilities/ 2>/dev/null || true
else
  echo "WARNING: Models module not found"
fi

# Copy the routing files
if [ -d "$SRC_DIR/palios_taey/routing" ]; then
  echo "Copying routing files..."
  cp $SRC_DIR/palios_taey/routing/router.py src/palios_taey/routing/
else
  echo "WARNING: Routing module not found"
fi

# List the copied files to verify
echo "Copied files:"
find src -type f | grep -v __init__.py | sort
find config -type f | sort

echo "File organization complete!"
