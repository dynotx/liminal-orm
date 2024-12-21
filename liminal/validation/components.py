import os
from datetime import datetime
from typing import Any

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from liminal.base.base_validation_filters import BaseValidatorFilters
from liminal.base.compare_operation import CompareOperation
from liminal.connection import BenchlingService
from liminal.entity_schemas.compare import compare_entity_schemas
from liminal.entity_schemas.operations import ArchiveEntitySchema
from liminal.enums import BenchlingReportLevel
from liminal.orm.base_model import BaseModel
from liminal.validation import BenchlingValidatorReport


def get_validator_reports(
    session: Session,
    benchling_sdk: BenchlingService,
    model_names: set[str] | None = None,
    base_filters: BaseValidatorFilters | None = None,
) -> list[BenchlingValidatorReport]:
    """Runs validation on a set of models. If no model names are provided, runs on all models.
    This starts by comparing schemas on Benchling's side to the model schemas. If the model doesn't match what is defined in Benchling,
    or the model passed in does not exist, add a BenchlingValidatorReport to the output describing the issue.

    Parameters
    ----------
    session : Session
        Benchling postgres session
    model_names : set[str] | None
        Set of model names to run the validator on. If empty, runs on all models.
    base_filters : BenchlingBaseValidatorFilters | None
        Collection of filters to apply when querying the Benchling postgres database for entities to validate.

    Returns
    -------
    A list of BenchlingValidatorReport objects, one for each model that went through validation.
    """
    all_reports: list[BenchlingValidatorReport] = []
    all_models = BaseModel.get_all_subclasses(model_names)
    model_comparison: dict[str, list[CompareOperation]] = compare_entity_schemas(
        benchling_sdk, model_names
    )
    invalid_model_names = [k for k in model_comparison.keys() if model_comparison[k]]
    for model in all_models:
        if model.__name__ in invalid_model_names:
            invalid_model_report = BenchlingValidatorReport(
                valid=False,
                message=f"Model {model.__name__} is invalid. {', '.join([compare_op.op.describe() for compare_op in model_comparison[model.__name__]])}",
                level=BenchlingReportLevel.HIGH,
                model="Out of Sync Models",
                entity_name=None,
                entity_id=None,
            )
            all_reports.append(invalid_model_report)
        else:
            reports = model.validate(session, base_filters)
            all_reports.extend(reports)
    if "Archive" in invalid_model_names:
        archive_ops: list[ArchiveEntitySchema] = [
            compare_op.op
            for compare_op in model_comparison["Archive"]
            if isinstance(compare_op.op, ArchiveEntitySchema)
        ]
        assert len(archive_ops) == len(model_comparison["Archive"])
        all_reports.append(
            BenchlingValidatorReport(
                valid=False,
                message=f"The following schemas are defined in Benchling but not defined as models: {', '.join([op.wh_schema_name for op in archive_ops])}",
                level=BenchlingReportLevel.HIGH,
                model="Out of Sync Models",
                entity_name=None,
                entity_id=None,
            )
        )
    return all_reports


def get_bv_file_name(suffix: str) -> str:
    """Generates a file name for the Benchling validation report. ex: bv_3202024154031.html"""
    return f"bv_{int(datetime.now().strftime('%m%d%Y%H%M%S'))}{suffix}"


def create_benchling_query_link(entity_registry_ids: list[str]) -> str:
    """Generates a benchling query link that opens up the registry page with entities pre-filtered based on the registry_ids passed in"""
    one_of_query_string = "%2C".join(id for id in entity_registry_ids)
    return f"https://dyno.benchling.com/dyno/f_/novto4U7-registry/?filter=bioentityLabels%3AIS_ONE_OF%3A{one_of_query_string}"


def get_model_data(
    model_name: str, reports: list[BenchlingValidatorReport]
) -> dict[str, Any]:
    """
    Given a model name and a list of BenchlingValidatorReport objects,
    returns data formatted for the Benchling validation summary template to ingest.
    """
    model_specific_reports = [r for r in reports if r.model == model_name]
    return {
        "model_name": model_name,
        "model_query": create_benchling_query_link(
            [r.registry_id for r in model_specific_reports if r.registry_id]
        ),
        "summary_by_level": {
            level: sum(1 for r in model_specific_reports if r.level == level)
            for level in sorted({r.level.value for r in model_specific_reports})
        },
        "entity_messages": [
            {
                "entity_name": r.entity_name,
                "error_message": r.message,
                "tissue_ontology": getattr(r, "tissue_ontology", None),
                "creator_name": r.creator_name,
                "web_url": r.web_url,
                "validator_name": r.validator_name,
                "level": r.level.value,
                "updated_date": r.updated_date.strftime("%m-%d-%Y")
                if r.updated_date
                else None,
            }
            for r in model_specific_reports
        ],
    }


def create_summary_html_report(
    reports: list[BenchlingValidatorReport], summary_file_name: str | None = None
) -> str:
    """Uses a Jinja2 template to create an HTML report from a list of BenchlingValidatorReport objects.
    If summary_file_name is not provided, it will be generated using the current timestamp.
    The summary report contains a summary of the validation results at a severity and validator type level,
    and includes a way to view individual entity errors.

    Parameters
    ----------
    reports : list[BenchlingValidatorReport]
        The list of BenchlingValidatorReport objects to create the summary report from.
    summary_file_name : str | None, optional
        The name of the file to save the summary report to. If None, will be generated using the current timestamp.

    Returns
    -------
    str
        The rendered HTML report from the Jinja2 template.
    """
    non_entity_models = ["Out of Sync Models"]
    if not summary_file_name:
        summary_file_name = get_bv_file_name(".html")
    env = Environment(
        loader=FileSystemLoader(
            os.path.join(os.path.dirname(__file__), "report_templates")
        )
    )
    template = env.get_template("benchling_validation_report_template.html")
    sorted_model_names = sorted({r.model for r in reports})
    plot_model_names = [
        model_name
        for model_name in sorted_model_names
        if model_name not in non_entity_models
    ]
    rendered_template = template.render(
        datetime=datetime.now().strftime("%m/%d/%Y"),
        summary_levels_table_data={
            "labels": plot_model_names,
            "data": {
                level: [
                    sum(
                        1
                        for report in reports
                        if report.model == model_name and report.level == level
                    )
                    for model_name in plot_model_names
                ]
                for level in sorted({report.level for report in reports})
            },
        },
        summary_validator_table_data={
            "labels": plot_model_names,
            "data": {
                validator_name: [
                    sum(
                        1
                        for report in reports
                        if report.model == model_name
                        and report.validator_name == validator_name
                    )
                    for model_name in plot_model_names
                ]
                for validator_name in sorted(
                    {r.validator_name for r in reports if r.validator_name}
                )
            },
        },
        validator_names=sorted({r.validator_name for r in reports if r.validator_name}),
        creator_names=sorted({r.creator_name for r in reports if r.creator_name}),
        model_data=[get_model_data(m, reports) for m in sorted_model_names],
        non_entity_models=non_entity_models,
    )
    return rendered_template
