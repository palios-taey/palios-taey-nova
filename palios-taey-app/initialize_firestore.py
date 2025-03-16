from google.cloud import firestore
import datetime

# Initialize Firestore client
db = firestore.Client(project='palios-taey-dev')

# Create memory system config
config_ref = db.collection('config').document('memory_system')
config_ref.set({
    'version': '1.0.0',
    'tiers': {
        'ephemeral': {'ttl_days': 0.5},
        'working': {'ttl_days': 14.0},
        'reference': {'ttl_days': 180.0},
        'archival': {'ttl_days': None}
    },
    'initial_setup': True
})

# Create default memory context
context_ref = db.collection('memory_contexts').document('default_context')
context_ref.set({
    'context_id': 'default_context',
    'name': 'Default Context',
    'description': 'Default context for PALIOS-TAEY system',
    'active_memory_ids': [],
    'metadata': {
        'created_at': datetime.datetime.now(),
        'updated_at': datetime.datetime.now(),
        'creator_id': 'system',
        'is_active': True
    }
})

print("Firestore initialized successfully!")
