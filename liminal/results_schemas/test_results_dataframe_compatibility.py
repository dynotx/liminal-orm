from unittest.mock import patch

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base

from liminal.orm.base_results_model import BaseResultsModel


def test_results_dataframe_supports_declared_dependency_versions() -> None:
    test_base = declarative_base()

    class ExampleRow(test_base):  # type: ignore[valid-type,misc]
        __tablename__ = "example_result_rows"

        id = Column(Integer, primary_key=True)
        name = Column(String)

    engine = create_engine("sqlite://")
    test_base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(ExampleRow(name="example"))
        session.commit()

        with patch.object(
            BaseResultsModel, "query", return_value=session.query(ExampleRow)
        ):
            dataframe = BaseResultsModel.df(session)

    assert dataframe.to_dict(orient="records") == [{"id": 1, "name": "example"}]
