from src.evaluator import Evaluator
from src.predictor import Predictor
from src.processor import Processor


def main():
    processor = Processor()
    processed_data = processor.process(file_path="data.csv")
    predictor = Predictor()
    predictor.train(training_data=processed_data, target_column="target")
    predictions = predictor.predict(input_dataset="input.csv")
    evaluator = Evaluator()
    evaluator.evaluate(predictions=predictions, validation_dataset="validations.csv")
