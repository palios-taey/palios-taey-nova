# Claude DC File Structure Guide

This document explains the organization of files and directories for Claude DC's environment.

## Directory Structure

The Claude DC environment is organized to maintain clear separation of concerns and make updates easier:

```
/home/computeruse/               # Claude DC's root directory
├── bin/                        # Executable scripts
│   ├── backup_current_env.sh   # Script to backup the live environment
│   ├── deploy_to_production.sh # Script to deploy changes to production
│   ├── run_claude_dc.py        # Main launcher script  
│   ├── run_dev_container.sh    # Script to start development container
│   ├── test_dev_environment.py # Test for dev environment
│   └── test_phase2_features.py # Test for Phase 2 features
├── cache/                      # Cache files for Claude DC
│   └── cache.md                # Main cache file
├── computer_use_demo/          # Core Claude DC implementation code
│   ├── loop.py                 # Agent loop for Claude DC
│   ├── requirements.txt        # Python dependencies
│   ├── streamlit.py            # UI application
│   └── tools/                  # Tool implementations
├── references/                 # Reference documentation
├── secrets/                    # API keys and sensitive information
├── test_environment/           # Testing directory
└── utils/                      # Utility modules and functions
    ├── config/                 # Configuration files
    └── token_manager.py        # Token management utilities
```

## Key Components

### Core Directories
- `computer_use_demo/`: Contains the primary Claude DC implementation code
- `bin/`: Contains executable scripts (with symlinks in the root directory)
- `utils/`: Contains utility functions and configuration
- `references/`: Contains reference documentation

### Key Files
- `run_claude_dc.py`: Main launcher for Claude DC
- `loop.py`: The agent loop implementation
- `streamlit.py`: The UI application

## How Files Are Deployed

1. The repository is cloned to `/home/computeruse/github/palios-taey-nova/`
2. Files are copied from the repository to their appropriate locations
3. The `claude_dc_quick_setup.sh` script handles this copying automatically
4. Critical scripts in `bin/` are symlinked to the root directory for convenience

## Adding New Files

When adding new files to the system:

1. **Executables/Scripts**: Place in the `bin/` directory
2. **Utilities**: Place in the `utils/` directory
3. **References**: Place in the `references/` directory
4. **Documentation**: Place in the repository root with `.md` extension

Because the `claude_dc_quick_setup.sh` script copies entire directories, you don't need to modify it when adding new files to existing directories.

## Important Notes

- Scripts in `bin/` are automatically made executable and symlinked to the root
- Documentation files (*.md) are automatically copied to the root directory
- The `computer_use_demo/` directory is handled separately and should be deployed carefully to avoid disrupting the live environment
- When moving files between directories, update the symlinks if necessary

This structure makes updates easier and more maintainable by using a consistent directory organization and automatic copying of full directories.