from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import ModelElementIndex, utc_now


def upsert_model_element_index(
    session: Session,
    *,
    element_id: str,
    system_id: str,
    layer: str,
    archimate_type: str,
    name: str,
    git_path: str,
    current_commit: str,
) -> ModelElementIndex:
    element = session.get(ModelElementIndex, element_id)
    if element is None:
        element = ModelElementIndex(
            id=element_id,
            system_id=system_id,
            layer=layer,
            archimate_type=archimate_type,
            name=name,
            git_path=git_path,
            current_commit=current_commit,
        )
        session.add(element)
    else:
        element.system_id = system_id
        element.layer = layer
        element.archimate_type = archimate_type
        element.name = name
        element.git_path = git_path
        element.current_commit = current_commit
        element.updated_at = utc_now()

    session.flush()
    return element


def get_model_element(session: Session, element_id: str) -> ModelElementIndex | None:
    return session.get(ModelElementIndex, element_id)


def list_model_elements(
    session: Session, *, system_id: str, layer: str | None = None
) -> list[ModelElementIndex]:
    statement = select(ModelElementIndex).where(ModelElementIndex.system_id == system_id)
    if layer is not None:
        statement = statement.where(ModelElementIndex.layer == layer)
    return list(
        session.scalars(statement.order_by(ModelElementIndex.layer, ModelElementIndex.name))
    )
