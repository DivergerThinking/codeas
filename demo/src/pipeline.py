import pandas as pd


class Pipeline:
    def __init__(self):
        self.data = None

    def load_data(self, file_path):
        try:
            self.data = pd.read_csv(file_path)
            print("Data loaded successfully.")
        except Exception as e:
            print(f"Error loading data: {str(e)}")

    def explore_data(self):
        if self.data is not None:
            print("Data Exploration:")
            print(self.data.describe())
        else:
            print("No data loaded for exploration.")

    def clean_data(self):
        if self.data is not None:
            print("Data Cleaning:")
            self.data = self.data.drop_duplicates()
            self.data = self.data.dropna()
            print("Data cleaned.")
        else:
            print("No data loaded for cleaning.")

    def filter_data(self, condition):
        if self.data is not None:
            print("Data Filtering:")
            self.data = self.data[condition]
            print("Data filtered.")
        else:
            print("No data loaded for filtering.")

    def aggregate_data(self, group_by, aggregations):
        if self.data is not None:
            print("Data Aggregation:")
            self.data = self.data.groupby(group_by).agg(aggregations)
            print("Data aggregated.")
        else:
            print("No data loaded for aggregation.")

    def export_data(self, output_path):
        if self.data is not None:
            try:
                self.data.to_csv(output_path, index=False)
                print("Data exported successfully.")
            except Exception as e:
                print(f"Error exporting data: {str(e)}")
        else:
            print("No data available for export.")


if __name__ == "__main__":
    # Example usage of the Pipeline class
    pipeline = Pipeline()
    pipeline.load_data("sample_data.csv")
    pipeline.explore_data()
    pipeline.clean_data()
    pipeline.transform_data()
    pipeline.filter_data(condition=(pipeline.data["column_name"] > 10))
    pipeline.aggregate_data(
        group_by="group_column", aggregations={"value_column": "mean"}
    )
    pipeline.export_data("output_data.csv")
