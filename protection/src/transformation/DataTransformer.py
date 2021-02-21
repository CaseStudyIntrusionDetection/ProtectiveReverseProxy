from abc import ABC, abstractmethod


class DataTransformer(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def data_transformation_wrapper(self, data_in):
        """Wrapper for the data transformation routine.

        Args:
            data_in (any): Input data to be transfomed.

        Returns:
            any: Transformed output data.
        """
        return None
