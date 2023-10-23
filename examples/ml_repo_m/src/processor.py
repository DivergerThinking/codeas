import pandas as pd


class Processor:
    def __init__(self):
        self.data = None

    def process(self, file_path, condition=None):
        self.load_data(file_path)
        self.clean_data()
        if condition:
            self.filter_data(condition)
        return self.data

    def load_data(self, file_path):
        try:
            self.data = pd.read_csv(file_path)
        except Exception as e:
            print(f"Error loading data: {str(e)}")

    def clean_data(self):
        if self.data is not None:
            self.data = self.data.drop_duplicates()
            self.data = self.data.dropna()

    def filter_data(self, condition):
        if self.data is not None:
            self.data = self.data[condition]
