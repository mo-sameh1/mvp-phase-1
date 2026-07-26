from backend.repository import (
    create_legacy_system,
    get_legacy_system,
    get_legacy_system_by_name,
)


def test_create_and_get_legacy_system(session):
    system = create_legacy_system(
        session,
        system_id="demo-legacy-system",
        name="Demo Legacy System",
        description="Synthetic MVP fixture",
    )

    assert get_legacy_system(session, system.id) == system
    assert get_legacy_system_by_name(session, "Demo Legacy System") == system
