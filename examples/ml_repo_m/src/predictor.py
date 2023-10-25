import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


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

    def train(
        self,
        training_data,
        target_column,
        model_class=RandomForestClassifier,
        **model_params,
    ):
        self.data = training_data
        self.split_train_test(target_column)
        self.model = model_class(**model_params)
        self.model.fit(self.X_train, self.y_train)

    def predict(self, input_dataset):
        input_data = pd.read_csv(input_dataset)
        if self.model:
            input_df = pd.DataFrame(input_data, index=[0])
            prediction = self.model.predict(input_df)
            return prediction
        else:
            return "Model has not been trained yet."

    def split_train_test(self, target_column, test_size=0.2, random_state=42):
        self.X = self.data.drop(target_column, axis=1)
        self.y = self.data[target_column]
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=test_size, random_state=random_state
        )
