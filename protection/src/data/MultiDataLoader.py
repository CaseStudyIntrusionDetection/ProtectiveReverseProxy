from abc import ABC, abstractmethod
from glob import glob
from os import path
import pandas as pd
import numpy as np

from src.data.DataLoader import DataLoader

class MultiDataLoader(ABC):

    def __init__(self, data_loaders):
        """Constructor.

        Args:
            data_loaders (list): List of data loaders to handle.
        """
        self.data_loaders = data_loaders

    def load_wrapper(self):
        """Executes the `load_wrapper()`s of all given data loaders.
        """
        print("Loading data...")
        for loader in self.data_loaders:
            print(f">> Loading done from {loader.path}")
            loader.load_wrapper()

    @abstractmethod
    def merge_loaded_data(self):
        raise NotImplementedError("merge_loaded_data(...) not implemented.")


class MultiLoaderJSON(MultiDataLoader):
    def merge_loaded_data(self):
        """Merges the datasets loaded by the single data loaders.
        """
        self.all_data = []
        for loader in self.data_loaders:
            structured_data = loader.data_to_structured_dict_list()
            # Add origin to each request
            origin = path.basename(loader.path)
            for i, x in enumerate(structured_data):
                structured_data[i]["data_origin"] = origin
                structured_data[i]['data_tool'] = path.splitext(origin)[0].split("_")[-1].lower()
            self.all_data.extend(structured_data)
            
    def data_to_dataframe(self):
        """Converts the loaded data into a pandas dataframe.

        Returns:
            pd.DataFrame: merged loaded data
        """
        df = pd.json_normalize(self.all_data)
        df['request-length'] = df['request-length'].astype(np.float32)
        df['label'] = df['label'].astype('str')
        return df
            

def get_files_in_dir(path_to_dir, file_extension, proj_root=""):
    """Helper function: Lists all files with file extension `file_ext` in `path_to_dir` (from `proj_root`).

    Args:
        path_to_dir (str): path to directory to check for files
        file_extension (str): file extension to look for
        proj_root (str, optional): path to project root. Defaults to "".

    Returns:
        list of str: list of relative paths to found files(includes going up to `proj_root`)
    """
    if proj_root == "":
        files = glob(path.join(path_to_dir, "*."+file_extension))
    else:
        files = glob(path.join(proj_root, path_to_dir, "*."+file_extension))
    return files