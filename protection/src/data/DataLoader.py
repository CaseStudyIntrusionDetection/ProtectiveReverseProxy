from abc import ABC, abstractmethod

class DataLoader(ABC):

    def __init__(self):
        self.data_loaded = False
        pass

    @abstractmethod
    def load_wrapper(self):
        """Wraps the extraction steps.
        """
        pass

    @abstractmethod
    def extract_data(self):
        """Loads the data from the disk.
        
        Returns:
            str: Loaded data
        """
        return ""

    @abstractmethod
    def data_to_dataframe(self, data_str):
        """Converts the data into a dataframe. 

        Args:
            data_str (str): loaded data

        Returns:
            pd.dataframe: dataframe data
        """
        return None