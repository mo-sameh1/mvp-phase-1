from backend.repository import (
    create_legacy_system,
    get_model_element,
    list_model_elements,
    upsert_model_element_index,
)


def test_upsert_model_element_index_is_idempotent(session):
    system = create_legacy_system(session, name="Demo")

    first = upsert_model_element_index(
        session,
        element_id="payment-service",
        system_id=system.id,
        layer="application",
        archimate_type="Application Service",
        name="Payment Service",
        git_path="systems/demo/as-is/application/payment-service.json",
        current_commit="abc123",
    )
    second = upsert_model_element_index(
        session,
        element_id="payment-service",
        system_id=system.id,
        layer="application",
        archimate_type="Application Component",
        name="Payment Service API",
        git_path="systems/demo/as-is/application/payment-service-api.json",
        current_commit="def456",
    )

    assert first.id == second.id
    assert get_model_element(session, "payment-service").archimate_type == "Application Component"
    assert len(list_model_elements(session, system_id=system.id)) == 1
    assert len(list_model_elements(session, system_id=system.id, layer="application")) == 1
