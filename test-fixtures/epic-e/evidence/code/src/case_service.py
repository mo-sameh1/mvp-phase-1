class CaseManagementSystem:
    """Coordinates permit case intake and review."""

    def submit_case(self, citizen_id: str, payload: dict) -> dict:
        case_record = {
            "citizen_id": citizen_id,
            "status": "submitted",
            "payload": payload,
        }
        return case_record


class CaseHandlingService:
    """Externally visible service for submitting and tracking cases."""

    def handle_submission(self, case_record: dict) -> str:
        return f"case:{case_record['citizen_id']}"
