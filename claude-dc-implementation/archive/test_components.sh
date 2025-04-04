#!/bin/bash

# Test dashboard components
echo "Testing Dashboard Components..."
echo "============================"

# 1. Test Enhanced Transcript Processor
echo "Testing Enhanced Transcript Processor..."
cd "$(dirname "$0")"
python3 -m src.processor.test_transcript_processor
echo ""

# 2. Test Bach Router
echo "Testing Bach Router..."
cd "$(dirname "$0")"
python3 -m src.dashboard.bach_router
echo ""

# 3. Test MCP Connector
echo "Testing MCP Connector..."
cd "$(dirname "$0")"
python3 -m src.dashboard.dashboard_mcp_connector
echo ""

echo "All tests complete!"
