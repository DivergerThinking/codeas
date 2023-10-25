import pandas as pd
from sklearn.metrics import mean_squared_error


class Evaluator:
    def evaluate(self, predictions, validation_dataset):
        actuals = pd.read_csv(validation_dataset)["target"].values
        if len(predictions) != len(actuals):
            raise ValueError("The datasets must have the same length.")

        mse = mean_squared_error(actuals, predictions)
        print(f"MSE: {mse:.2f}")
