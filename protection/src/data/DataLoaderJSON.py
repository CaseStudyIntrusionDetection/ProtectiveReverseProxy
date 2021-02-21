from os import path
import json
import pandas as pd
import numpy as np

from src.data.DataLoader import DataLoader
from src.data.HTTPRequest import HTTPRequest
from src.transformation.HTTPTransformer import HTTPTransformer
from src.transformation.HTTPHeaders import transform_header_dict, HTTP_RELEVANT_HEADERS

class DataLoaderJSON(DataLoader):

    def __init__(self, file_path, proj_root):
        """Constructor.

        Args:
            file_path (str): path from !project root!
        """
        self.proj_root = proj_root
        self.path = path.join(proj_root, file_path)
        self.data_loaded = False

    def load_wrapper(self):
        """Wraps the loading steps.
        """
        self.extract_data()
        self.data_loaded = True

    def extract_data(self):
        """Extract the data from the specified file & converts it into a python object.
        """
        with open(self.path) as f:
            file_string = f.read()
        self.data_dict = json.loads(file_string)

    def data_to_dataframe(self):
        """Transforms the data dict into a pandas dataframe. 

        Returns:
            pd.DataFrame: data
        """
        return pd.json_normalize(self.data_dict)

    def data_to_structured_dict_list(self):
        reqs = []
        for x in self.data_dict:
            request = x['request']
            
            uri_obj = HTTPTransformer.uri_transformation_wrapper(request['uri'])
            r = {
                "label": "no zap id",
                "original-zap-id": x['header']['X-ZAP-Scan-ID'] if 'X-ZAP-Scan-ID' in x['header'] else "no zap id",
                "method": request['method'],
                "uri-path": uri_obj['path'],
                "uri-query": uri_obj['query'],
                "body": "" if request['body'] == "" else HTTPTransformer.handle_body(request['body']),
                "request-length": x['header']["Content-Length"] if "Content-Length" in x['header'] else -1,
                "uri-length": len(request['uri']),
                "body-length": len(request['body'])
            }

            header_dict = transform_header_dict(x['header'], headers=HTTP_RELEVANT_HEADERS)
            r = {**r, **header_dict}

            reqs.append(r)

        return reqs
    
    def data_to_structured_df(self):
        reqs = self.data_to_structured_dict_list()
        df = pd.DataFrame(reqs)

        df['request-length'] = df['request-length'].astype(np.float32)
        df['label'] = df['label'].astype('str')

        return df
        
