# firestore.tf - Firestore configuration for PALIOS-TAEY Memory System

# Create a Firestore database in native mode
resource "google_firestore_database" "palios_taey_db" {
  name                      = "(default)"
  project                   = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  location_id               = var.firestore_location
  type                      = "FIRESTORE_NATIVE"
  point_in_time_recovery_enabled = true

  depends_on = [google_project_service.required_apis]
}

# Create basic collections for the Memory System
resource "google_firestore_document" "memory_system_config" {
  project     = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  collection  = "config"
  document_id = "memory_system"
  
  fields = jsonencode({
    version = {
      stringValue = "1.0.0"
    },
    tiers = {
      mapValue = {
        fields = {
          ephemeral = {
            mapValue = {
              fields = {
                ttl_days = {
                  doubleValue = 0.5
                }
              }
            }
          },
          working = {
            mapValue = {
              fields = {
                ttl_days = {
                  doubleValue = 14.0
                }
              }
            }
          },
          reference = {
            mapValue = {
              fields = {
                ttl_days = {
                  doubleValue = 180.0
                }
              }
            }
          },
          archival = {
            mapValue = {
              fields = {
                ttl_days = {
                  nullValue = null
                }
              }
            }
          }
        }
      }
    },
    initial_setup = {
      booleanValue = true
    }
  })

  depends_on = [google_firestore_database.palios_taey_db]
}

# Create an initial context for Memory System
resource "google_firestore_document" "default_context" {
  project     = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  collection  = "memory_contexts"
  document_id = "default_context"
  
  fields = jsonencode({
    context_id = {
      stringValue = "default_context"
    },
    name = {
      stringValue = "Default Context"
    },
    description = {
      stringValue = "Default context for PALIOS-TAEY system"
    },
    active_memory_ids = {
      arrayValue = {
        values = []
      }
    },
    metadata = {
      mapValue = {
        fields = {
          created_at = {
            timestampValue = "2025-03-01T00:00:00Z"
          },
          updated_at = {
            timestampValue = "2025-03-01T00:00:00Z"
          },
          creator_id = {
            stringValue = "system"
          },
          is_active = {
            booleanValue = true
          }
        }
      }
    }
  })

  depends_on = [google_firestore_database.palios_taey_db]
}

# Create a transcript context for Transcript Processor
resource "google_firestore_document" "transcript_context" {
  project     = var.create_project ? google_project.palios_taey_project[0].project_id : var.project_id
  collection  = "memory_contexts"
  document_id = "transcript_context"
  
  fields = jsonencode({
    context_id = {
      stringValue = "transcript_context"
    },
    name = {
      stringValue = "Transcript Analysis"
    },
    description = {
      stringValue = "Context for storing and analyzing transcript data"
    },
    active_memory_ids = {
      arrayValue = {
        values = []
      }
    },
    metadata = {
      mapValue = {
        fields = {
          created_at = {
            timestampValue = "2025-03-01T00:00:00Z"
          },
          updated_at = {
            timestampValue = "2025-03-01T00:00:00Z"
          },
          creator_id = {
            stringValue = "system"
          },
          is_active = {
            booleanValue = true
          }
        }
      }
    }
  })

  depends_on = [google_firestore_database.palios_taey_db]
}