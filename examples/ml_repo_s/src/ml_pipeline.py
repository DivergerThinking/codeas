import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


class ProcessingPipeline:
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


class Predictor:
    def __init__(self):
        self.data = None
        self.X = None
        self.y = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.model = None

    def load_data(self, file_path):
        try:
            self.data = pd.read_csv(file_path)
            print("Data loaded successfully.")
        except Exception as e:
            print(f"Error loading data: {str(e)}")

    def feature_engineering(self, target_column, drop_columns=None):
        if drop_columns:
            self.data = self.data.drop(drop_columns, axis=1)
        self.X = self.data.drop(target_column, axis=1)
        self.y = self.data[target_column]

    def train_test_split(self, test_size=0.2, random_state=42):
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=test_size, random_state=random_state
        )

    def train_model(self, model_class=RandomForestClassifier, **model_params):
        self.model = model_class(**model_params)
        self.model.fit(self.X_train, self.y_train)

    def evaluate_model(self):
        if self.model:
            y_pred = self.model.predict(self.X_test)
            accuracy = accuracy_score(self.y_test, y_pred)
            report = classification_report(self.y_test, y_pred)
            return accuracy, report
        else:
            return "Model has not been trained yet."

    def predict(self, input_data):
        if self.model:
            input_df = pd.DataFrame(input_data, index=[0])
            prediction = self.model.predict(input_df)
            return prediction
        else:
            return "Model has not been trained yet."


if __name__ == "__main__":
    pipeline = ProcessingPipeline()
    pipeline.load_data("sample_data.csv")
    pipeline.explore_data()
    pipeline.clean_data()
    pipeline.filter_data(condition=(pipeline.data["column_name"] > 10))
    pipeline.aggregate_data(
        group_by="group_column", aggregations={"value_column": "mean"}
    )
    pipeline.export_data("output_data.csv")

    predictor = Predictor()
    predictor.load_data("sample_data.csv")
    predictor.feature_engineering(
        target_column="target_column", drop_columns=["column_to_drop"]
    )
    predictor.train_test_split(test_size=0.2, random_state=42)
    predictor.train_model(model_class=RandomForestClassifier, n_estimators=100)
    accuracy, report = predictor.evaluate_model()
    new_data = {"feature1": "value1", "feature2": "value2"}
    prediction = predictor.predict(new_data)
