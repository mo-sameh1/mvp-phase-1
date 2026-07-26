from agents.archimate_metamodel import explain_rule, list_element_types


def print_result(title: str, result: dict) -> None:
    print(f"\n{title}")
    print(f"  status: {result['status']}")
    print(f"  valid: {result['valid']}")
    print(f"  citation: {result.get('citation')}")
    if "reason" in result:
        print(f"  reason: {result['reason']}")


def main() -> int:
    print("ArchiMate 3.2 metamodel smoke test")
    print(f"Application elements: {', '.join(list_element_types('application'))}")

    valid_element = explain_rule(layer="application", archimate_type="Application Component")
    wrong_layer = explain_rule(layer="business", archimate_type="Application Component")
    approved_relationship = explain_rule(
        source_type="Business Process",
        relationship_type="Specialization",
        target_type="Business Process",
    )
    unapproved_candidate = explain_rule(
        source_type="Application Service",
        relationship_type="Serving",
        target_type="Business Process",
    )

    print_result("Valid element lookup", valid_element)
    print_result("Wrong-layer lookup", wrong_layer)
    print_result("Approved relationship lookup", approved_relationship)
    print_result("Unapproved candidate relationship lookup", unapproved_candidate)

    checks = [
        valid_element["valid"] is True,
        wrong_layer["valid"] is False,
        approved_relationship["valid"] is True,
        unapproved_candidate["valid"] is False,
        unapproved_candidate["status"] == "needs_review",
    ]
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
