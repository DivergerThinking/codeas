# Predictor Documentation

## Introduction
The `Predictor` class is designed to train a machine learning model and make predictions on new input datasets. It utilizes the `RandomForestClassifier` algorithm from the `sklearn.ensemble` module for training the model.

## Inputs
The `Predictor` class requires the following inputs:

* `training_data`: A pandas DataFrame containing the training dataset.
* `target_column`: The name of the target column in the training dataset.
* `model_class` (optional): The class of the machine learning model to be used for training. Default is `RandomForestClassifier`.
* `**model_params` (optional): Additional parameters to be passed to the model class during initialization.

## Outputs
The `Predictor` class provides the following outputs:

* `prediction`: The predicted values for the input dataset.

## Usage
To use the `Predictor` class, follow these steps:

1. Create an instance of the `Predictor` class.
2. Train the model using the `train` method, providing the training data and target column.
3. Make predictions on new input datasets using the `predict` method.

Example code:

```python
# Create an instance of the Predictor class
predictor = Predictor()

# Train the model
training_data = pd.read_csv('training_data.csv')
target_column = 'target'
predictor.train(training_data, target_column)

# Make predictions on new input dataset
input_dataset = 'input_data.csv'
predictions = predictor.predict(input_dataset)
print(predictions)
```

Please note that before making predictions, the model must be trained using the `train` method. If the model has not been trained yet, the `predict` method will return the message "Model has not been trained yet."