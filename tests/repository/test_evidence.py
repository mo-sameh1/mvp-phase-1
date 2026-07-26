from backend.repository import (
    create_evidence_source,
    create_legacy_system,
    list_evidence_sources,
)


def test_evidence_source_create_is_idempotent(session):
    system = create_legacy_system(session, name="Demo")

    first = create_evidence_source(
        session,
        system_id=system.id,
        source_type="code",
        location="/evidence/code/payment.py",
        description="Initial description",
    )
    second = create_evidence_source(
        session,
        system_id=system.id,
        source_type="code",
        location="/evidence/code/payment.py",
        description="Updated description",
    )

    assert first.id == second.id
    assert second.description == "Updated description"
    assert list_evidence_sources(session, system_id=system.id) == [second]
