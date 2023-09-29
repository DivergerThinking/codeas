import pytest
import pandas as pd
from demo.pipeline import Pipeline

@pytest.fixture
def pipeline():
    return Pipeline()

def test_load_data(pipeline):
    file_path = "data.csv"
    pipeline.load_data(file_path)
    assert pipeline.data is not None

def test_load_data_exception(pipeline):
    file_path = "invalid_file.csv"
    with pytest.raises(Exception):
        pipeline.load_data(file_path)

def test_explore_data(pipeline, capsys):
    pipeline.data = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    pipeline.explore_data()
    captured = capsys.readouterr()
    assert "Data Exploration:" in captured.out
    assert "count  3.000000  3.000000" in captured.out

def test_explore_data_no_data(pipeline, capsys):
    pipeline.explore_data()
    captured = capsys.readouterr()
    assert "No data loaded for exploration." in captured.out

def test_clean_data(pipeline):
    pipeline.data = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    pipeline.clean_data()
    assert pipeline.data.shape == (3, 2)

def test_clean_data_no_data(pipeline):
    pipeline.clean_data()
    assert pipeline.data is None

def test_filter_data(pipeline):
    pipeline.data = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    condition = pipeline.data['A'] > 2
    pipeline.filter_data(condition)
    assert pipeline.data.shape == (1, 2)

def test_filter_data_no_data(pipeline):
    pipeline.filter_data(None)
    assert pipeline.data is None

def test_aggregate_data(pipeline):
    pipeline.data = pd.DataFrame({'A': [1, 1, 2], 'B': [4, 5, 6]})
    group_by = 'A'
    aggregations = {'B': 'sum'}
    pipeline.aggregate_data(group_by, aggregations)
    assert pipeline.data.shape == (2, 1)
    assert pipeline.data['B'].tolist() == [9, 6]

def test_aggregate_data_no_data(pipeline):
    pipeline.aggregate_data(None, None)
    assert pipeline.data is None

def test_export_data(pipeline, tmp_path):
    pipeline.data = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    output_path = tmp_path / "export.csv"
    pipeline.export_data(output_path)
    assert output_path.exists()

def test_export_data_exception(pipeline, tmp_path):
    pipeline.data = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    output_path = tmp_path / "nonexistent_folder/export.csv"
    with pytest.raises(Exception):
        pipeline.export_data(output_path)

def test_export_data_no_data(pipeline, tmp_path):
    output_path = tmp_path / "export.csv"
    pipeline.export_data(output_path)
    assert not output_path.exists()