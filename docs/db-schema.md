# MVP Database Schema

The MVP keeps full model artifacts in the GitHub model repository. The database stores system metadata, indexes, job status, evidence source references, and artifact approval state.

```mermaid
erDiagram
    legacy_systems {
        string id PK
        string name UK
        text description
    }

    model_element_index {
        string id PK
        string system_id FK
        string layer
        string archimate_type
        string name
        text git_path
        string current_commit
        datetime updated_at
    }

    artifact_versions {
        string id PK
        string system_id FK
        string commit_sha
        string phase
        string tag
        string author_type
        string run_id
        string approval_status
        string approved_by
        datetime approved_at
        int pr_number
        text pr_url
        datetime created_at
    }

    jobs {
        string id PK
        string system_id FK
        string phase
        string status
        string run_id
        text error_message
        datetime started_at
        datetime finished_at
    }

    evidence_sources {
        string id PK
        string system_id FK
        string source_type
        text location
        text description
        datetime added_at
    }

    legacy_systems ||--o{ model_element_index : indexes
    legacy_systems ||--o{ artifact_versions : versions
    legacy_systems ||--o{ jobs : runs
    legacy_systems ||--o{ evidence_sources : evidence
```

