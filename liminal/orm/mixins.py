from sqlalchemy import DATETIME, Boolean, Numeric, String
from sqlalchemy import Column as SqlColumn


class EntryMixin:
    display_id = SqlColumn("display_id$", String, nullable=True)
    review_completed_at = SqlColumn("review_completed_at$", DATETIME, nullable=True)
    review_initial_requested_at = SqlColumn(
        "review_initial_requested_at$", DATETIME, nullable=True
    )
    review_process_type = SqlColumn("review_process_type$", String, nullable=True)
    review_process_version_id = SqlColumn(
        "review_process_version_id$", String, nullable=True
    )
    review_process = SqlColumn("review_process$", String, nullable=True)
    review_requested_at = SqlColumn("review_requested_at$", DATETIME, nullable=True)
    review_status_changed_at = SqlColumn(
        "review_status_changed_at$", DATETIME, nullable=True
    )
    review_status = SqlColumn("review_status$", String, nullable=True)
    workflow_id = SqlColumn("workflow_id$", String, nullable=True)


class CustomEntityMixin:
    file_registry_id = SqlColumn("file_registry_id$", String, nullable=True)
    is_registered = SqlColumn("is_registered$", Boolean, nullable=True)
    project_id = SqlColumn("project_id$", String, nullable=True)
    type = SqlColumn("type$", String, nullable=True)
    validation_status = SqlColumn("validation_status$", String, nullable=True)


class DnaOligoMixin:
    # bases = SqlColumn("bases$", String, nullable=True)
    file_registry_id = SqlColumn("file_registry_id$", String, nullable=True)
    is_registered = SqlColumn("is_registered$", Boolean, nullable=True)
    project_id = SqlColumn("project_id$", String, nullable=True)
    type = SqlColumn("type$", String, nullable=True)
    validation_status = SqlColumn("validation_status$", String, nullable=True)


class RnaOligoMixin:
    # bases = SqlColumn("bases$", String, nullable=True)
    file_registry_id = SqlColumn("file_registry_id$", String, nullable=True)
    is_registered = SqlColumn("is_registered$", Boolean, nullable=True)
    project_id = SqlColumn("project_id$", String, nullable=True)
    type = SqlColumn("type$", String, nullable=True)
    validation_status = SqlColumn("validation_status$", String, nullable=True)


class DnaSequenceMixin:
    # bases = SqlColumn("bases$", String, nullable=True)
    # bases_length_exceeds_limit = SqlColumn("bases_length_exceeds_limit$", Boolean, nullable=True)
    file_registry_id = SqlColumn("file_registry_id$", String, nullable=True)
    is_registered = SqlColumn("is_registered$", Boolean, nullable=True)
    project_id = SqlColumn("project_id$", String, nullable=True)
    type = SqlColumn("type$", String, nullable=True)
    validation_status = SqlColumn("validation_status$", String, nullable=True)


class RnaSequenceMixin:
    # bases = SqlColumn("bases$", String, nullable=True)
    # bases_length_exceeds_limit = SqlColumn("bases_length_exceeds_limit$", Boolean, nullable=True)
    file_registry_id = SqlColumn("file_registry_id$", String, nullable=True)
    is_registered = SqlColumn("is_registered$", Boolean, nullable=True)
    project_id = SqlColumn("project_id$", String, nullable=True)
    type = SqlColumn("type$", String, nullable=True)
    validation_status = SqlColumn("validation_status$", String, nullable=True)


class AaSequenceMixin:
    # amino_acids = SqlColumn("amino_acids$", String, nullable=True)
    # amino_acids_length_exceeds_limit = SqlColumn("amino_acids_length_exceeds_limit$", Boolean, nullable=True)
    file_registry_id = SqlColumn("file_registry_id$", String, nullable=True)
    is_registered = SqlColumn("is_registered$", Boolean, nullable=True)
    project_id = SqlColumn("project_id$", String, nullable=True)
    type = SqlColumn("type$", String, nullable=True)
    validation_status = SqlColumn("validation_status$", String, nullable=True)


class MixtureMixin:
    allow_measured_ingredients = SqlColumn(
        "allow_measured_ingredients$", Boolean, nullable=True
    )
    amount = SqlColumn("amount$", Numeric, nullable=True)
    file_registry_id = SqlColumn("file_registry_id$", String, nullable=True)
    is_registered = SqlColumn("is_registered$", Boolean, nullable=True)
    project_id = SqlColumn("project_id$", String, nullable=True)
    type = SqlColumn("type$", String, nullable=True)
    validation_status = SqlColumn("validation_status$", String, nullable=True)


class MoleculeMixin:
    canonical_smiles = SqlColumn("canonical_smiles$", String, nullable=True)
    file_registry_id = SqlColumn("file_registry_id$", String, nullable=True)
    is_registered = SqlColumn("is_registered$", Boolean, nullable=True)
    project_id = SqlColumn("project_id$", String, nullable=True)
    type = SqlColumn("type$", String, nullable=True)
    validation_status = SqlColumn("validation_status$", String, nullable=True)
