
from os import path
import json
import time

import numpy as np
from sklearn.preprocessing import OrdinalEncoder
from sklearn.model_selection import train_test_split

import src.models.NNArchitecture as NNA
from src.data.BalancedData import BalancedData


def eval_wrapper(setting_name, proj_root, train_files, test_files=[], label_column='bin_label', 
                text_vars=[], categ_vars=[], num_vars=[], bin_vars=[], nn_settings=None):
    print(f"/// New config run: '{setting_name}' ///")
    # >  Load data
    # |- Train Data
    times = {}
    times['start'] = time.time()
    print("> Loading TRAINING data...")
    train_loader = BalancedData(proj_root=proj_root, file_paths=train_files)
    train_loader.load_data()
    train_df = train_loader.get_all_data_df()

    train_df['bin_label'] = train_df.apply(lambda x: NNA.binarize_label(x), axis=1)
    times['train-data-loaded'] = time.time()
    # |- Test Data
    if len(test_files)>0:
        print("> Loading TEST data...")
        test_loader = BalancedData(proj_root=proj_root, file_paths=test_files)
        test_loader.load_data()
        test_df = test_loader.get_all_data_df()

        test_df['bin_label'] = test_df.apply(lambda x: NNA.binarize_label(x), axis=1)
    else: 
        print("> Splitting df into test and train set.")
        train_df, test_df = train_test_split(train_df, test_size=0.3, random_state=42)
        train_df = train_df.copy() # Avoid SettingWithCopy Warning from pandas
        test_df = test_df.copy()
    times['test-data-loaded'] = time.time()

    N_CLASSES = len(train_df[label_column].unique())
    print(f"  Found {N_CLASSES} classes to predict.")

    # >  Preprocess data
    # |- Encode labels
    print("> Encoding labels...")
    oe = OrdinalEncoder()
    #oe = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    np_labels = train_df[label_column].to_numpy().reshape(-1, 1)
    oe.fit(np_labels)
    train_df[label_column] = oe.transform(np_labels)
    test_df[label_column] = oe.transform(test_df[label_column].to_numpy().reshape(-1,1))
    
    test_df.head()

    # |- Create TF datasets
    print("> Creating tf.DataSets...")
    train_ds = NNA.df_to_dataset(train_df, label_column, batch_size=128)
    test_ds = NNA.df_to_dataset(test_df, label_column, batch_size=128)

    times['data-ready'] = time.time()
    # >  Setup model
    print("> Setting up model...")
    # |- Combine features
    encoded_features, all_inputs = NNA.combine_input_pipelines(categ_vars, text_vars, num_vars, bin_vars, train_ds, nn_settings)
    
    # |- Create model
    model = NNA.create_model(encoded_features, all_inputs, N_CLASSES,
                            n_units=nn_settings['classifier']['n_units'],
                            n_layers=nn_settings['classifier']['n_layers'],
                            dropout=nn_settings['classifier']['dropout'])
    times['model-ready'] = time.time()
    # >  Train model
    print("> Training model...")
    NNA.fit_model(model, train_ds, test_ds, epochs=nn_settings['fitting']['n_epochs'] ,early_stopping=True)
    times['model-trained'] = time.time()
    # >  Save model
    print("> Saving model...")
    model.save(path.join(proj_root, "models", "neural_nets", setting_name))
    times['model-saved'] = time.time()

    # >  Eval model on test data
    print("> Evaluating model on test data...")
    eval_dict = NNA.create_eval_dict(test_df, label_column, oe, model)
    times['model-tested'] = time.time()
    
    eval_dict['times'] = times
    # >  Save eval metrics
    eval_path = path.join(proj_root, "models", "neural_nets_eval", f"{setting_name}_eval.json")
    print(f"> Saving eval metrics under {eval_path}...")
    with open(eval_path, "w") as f:
        json.dump(eval_dict, f, indent=4, default=convert)

    print(f"## Work done for current setting '{setting_name}' ##")
    return 

def convert(o):
    if isinstance(o, np.int64): return int(o)  
    raise TypeError