from sqlalchemy.orm import RelationshipProperty, relationship

from liminal.orm.column import Column


def single_relationship(
    target_class_name: str, entity_link_field: Column, backref: str | None = None
) -> RelationshipProperty:
    """Wrapper for SQLAlchemy's relationship function. Liminal's recommendation for defining a relationship from
    a class to a linked entity field. This means the representation of that field is a single entity_id.

    Parameters
    ----------
    target_class_name : str
        Class name of the entity schema class that is being linked.
    entity_link_field : Column
        Column on the current class that links to the target class.
    backref : str | None, optional
        backref argument for the SQLAlchemy relationship. setting backrefcreates a new property on the related class that points back to the original class.
        This makes it easy to navigate the relationship in both directions without having to explicitly define the reverse relationship.

    Returns
    -------
    SQLAlchemy RelationshipProperty
    """
    return relationship(
        target_class_name,
        foreign_keys=entity_link_field,
        backref=backref if backref else None,
        uselist=False,
    )


def multi_relationship(
    target_class_name: str, current_class_name: str, entity_link_field_name: str
) -> RelationshipProperty:
    """Wrapper for SQLAlchemy's relationship function. Liminal's recommendation for defining a relationship from
    a class to a linked entity field that has is_multi=True. This means the representation of that field is a list of entity_ids.
    Parameters
    ----------
    target_class_name : str
        Class name of the entity schema class that is being linked.
    current_class_name : str
        Class name of the current class that this relationship is being defined on.
    entity_link_field_name : str
        Column on the current class that links to the target class.

    Returns
    -------
    SQLAlchemy RelationshipProperty
    """
    if target_class_name == current_class_name:
        return relationship(
            target_class_name,
            primaryjoin=f"remote({target_class_name}.id) == any_(foreign({current_class_name}.{entity_link_field_name}))",
            uselist=True,
        )
    return relationship(
        target_class_name,
        primaryjoin=f"{target_class_name}.id == any_(foreign({current_class_name}.{entity_link_field_name}))",
        uselist=True,
    )
