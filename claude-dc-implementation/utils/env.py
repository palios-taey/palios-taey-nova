# /utils/env.py
import os

def get_environment():
    """Detect which environment we're running in."""
    if os.path.exists('/home/jesse'):
        return 'jesse'
    elif os.path.exists('/home/computeruse'):
        return 'claude_dc'
    else:
        return 'unknown'

def get_paths():
    """Get environment-specific paths."""
    env = get_environment()
    if env == 'jesse':
        return {
            'secrets': '/home/jesse/secrets/palios-taey-secrets.json',
            'data': '/home/jesse/projects/palios-taey-nova/claude-dc-implementation/data',
            'repo': '/home/jesse/projects/palios-taey-nova/claude-dc-implementation'
        }
    elif env == 'claude_dc':
        return {
            'secrets': '/home/computeruse/secrets/palios-taey-secrets.json',
            'data': '/home/computeruse/github/palios-taey-nova/claude-dc-implementation/data',
            'repo': '/home/computeruse/github/palios-taey-nova/claude-dc-implementation'
        }
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return {
            'secrets': os.path.join(base_dir, 'palios-taey-secrets.json'),
            'data': os.path.join(base_dir, 'data'),
            'repo': base_dir
        }
