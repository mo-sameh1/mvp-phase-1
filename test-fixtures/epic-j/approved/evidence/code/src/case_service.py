"""Tiny fictional service used by the Epic J acceptance fixture."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PermitCase:
    case_id: str
    applicant_id: str
    status: str


class CaseManagementSystem:
    """Application component that exposes the case handling service."""

    def submit_case(self, applicant_id: str) -> PermitCase:
        return PermitCase(
            case_id=f"CASE-{applicant_id}",
            applicant_id=applicant_id,
            status="submitted",
        )


class AuditPublisher:
    """Publishes a case-submitted audit event for downstream reporting."""

    def publish_case_submitted(self, permit_case: PermitCase) -> dict[str, str]:
        return {
            "event_type": "case_submitted",
            "case_id": permit_case.case_id,
            "status": permit_case.status,
        }
