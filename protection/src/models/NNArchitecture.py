import os

import numpy as np

import tensorflow as tf
from tensorflow.keras import layers

from tensorflow.keras.layers.experimental import preprocessing as exp_preprocessing
from tensorflow.keras.layers.experimental.preprocessing import TextVectorization

from tensorflow_addons.metrics.f_scores import F1Score


def binarize_label(row):
    return 'without zap-id' if row['label'] == "no zap id" else 'with zap-id'

def load_requests_wrapper(proj_root, load_type="balanced_ds", dataset_or_path=None):
    if load_type == "single_ds":
        from src.data.DataLoaderJSON import DataLoaderJSON
        #file_path = os.path.join("data", "dummy", "Scanner_ZAP_example.json")
        path = dataset_or_path if dataset_or_path is not None else os.path.join("data", "raw", "cms_1_zap.json")
        loader = DataLoaderJSON(path, proj_root)
        
        loader.load_wrapper()
        
        reqs = loader.data_dict
        
    elif load_type == "balanced_ds":
        dataset = dataset_or_path if dataset_or_path is not None else "cms"
        from src.data.BalancedData import BalancedData

        data = BalancedData(dataset, proj_root)
        data.load_data()

        reqs = data.get_all_data()
        
    
    return reqs


def load_df_wrapper(proj_root, load_type="balanced_ds", dataset_or_path=None):
    if load_type == "single_ds":
        from src.data.DataLoaderJSON import DataLoaderJSON
        #file_path = os.path.join("data", "dummy", "Scanner_ZAP_example.json")
        path = dataset_or_path if dataset_or_path is not None else os.path.join("data", "raw", "cms_1_zap.json")
        loader = DataLoaderJSON(path, proj_root)
        
        loader.load_wrapper()
        df = loader.data_to_dataframe()
        
        df = loader.data_to_structured_df()
        
    elif load_type == "balanced_ds":
        dataset = dataset_or_path if dataset_or_path is not None else "cms"
        from src.data.BalancedData import BalancedData

        data = BalancedData(dataset, proj_root)
        data.load_data()

        df = data.get_all_data_df()
        
    df['bin_label'] = df.apply(lambda x: binarize_label(x), axis=1)
    return df

def df_to_dataset(dataframe, label_column, shuffle=True, batch_size=32):
    """Transforms a pandas dataframe into a tensorflow dataset.

    Args:
        dataframe (pd.DataFrame): pandas dataframe to be transformed
        label_column (string): target label column name
        shuffle (bool, optional): shuffle dataset?. Defaults to True.
        batch_size (int, optional): batch size. Defaults to 32.

    Returns:
        tf.DataSet: A tensorflow dataset object
    """
    dataframe = dataframe.copy()
    labels = dataframe.pop(label_column)
    ds = tf.data.Dataset.from_tensor_slices((dict(dataframe), labels))
    if shuffle:
        ds = ds.shuffle(buffer_size=len(dataframe))
    ds = ds.batch(batch_size)
    ds = ds.prefetch(batch_size)
    return ds

def get_category_encoding_layer(name, dataset, dtype, max_tokens=None):
    """Creates everything that's needed for a categorical encoding input pipeline.

    Args:
        name (string): name of the feature
        dataset (tf.DataSet): tensorflow dataset
        dtype (string): datatype
        max_tokens (int, optional): maximum number of tokens. Defaults to None.

    Returns:
        lambda function: categorical input pipeline
    """
    # Create a StringLookup layer which will turn strings into integer indices
    if dtype == 'string':
        index = exp_preprocessing.StringLookup(max_tokens=max_tokens)
    else:
        index = exp_preprocessing.IntegerLookup(max_values=max_tokens)

    # Prepare a Dataset that only yields our feature
    feature_ds = dataset.map(lambda x, y: x[name])

    # Learn the set of possible values and assign them a fixed integer index.
    index.adapt(feature_ds)

    # Create a Discretization for our integer indices.
    encoder = exp_preprocessing.CategoryEncoding(max_tokens=index.vocab_size())

    # Prepare a Dataset that only yields our feature.
    feature_ds = feature_ds.map(index)

    # Learn the space of possible indices.
    encoder.adapt(feature_ds)

    # Apply one-hot encoding to our indices. The lambda function captures the
    # layer so we can use them, or include them in the functional model later.
    return lambda feature: encoder(index(feature))


def get_text_encoding_layer(name, dataset, 
                            max_features=100, max_len=20, embedding_dim=20,
                            layer_type="bi_rnn", n_units=20, dropout=0.3):
    """Creates everything that is needed for a textual input pipeline.

    Args:
        name (string): name of the feature
        dataset (tf.DataSet): tensorflow dataset
        max_features (int, optional): Maximum vocab size. Defaults to 100.
        max_len (int, optional): Sequence length to pad the outputs to. Defaults to 20.
        embedding_dim (int, optional): Embedding dimension. Defaults to 20.
        layer_type (str, optional): layer type to use (e.g., rnn, bi_rnn, gru, cnn). Defaults to "bi_rnn".
        n_units (int, optional): number of units within that layer. Defaults to 20.
        dropout (float, optional): dropout percentage. Defaults to 0.3.

    Returns:
        lambda function: textual input pipeline
    """
    # max_features = 100  # Maximum vocab size.
    # max_len = 20  # Sequence length to pad the outputs to.
    # embedding_dim = 20
    
    vec_layer = TextVectorization(
        max_tokens=max_features,
        output_mode='int',
        output_sequence_length=max_len)
    
    text_ds = dataset.map(lambda x, y: x[name])
    
    vec_layer.adapt(text_ds)
    
    embedding_layer = layers.Embedding(max_features + 1, embedding_dim)
    
    dropout_layer = layers.Dropout(0.4)
    
    if layer_type == "cnn":
        # Conv1D + global max pooling
        conv_layer = layers.Conv1D(n_units, 5, padding='valid', activation='relu', strides=3)
        max_pooling_layer = layers.GlobalMaxPooling1D()
    
        return lambda feature: max_pooling_layer(conv_layer(dropout_layer(embedding_layer(vec_layer(feature)))))
    
    elif layer_type == "rnn":
        rnn_layer = layers.SimpleRNN(units=n_units, activation='relu', dropout=dropout)
        
        return lambda feature: rnn_layer(dropout_layer(embedding_layer(vec_layer(feature))))
    
    elif layer_type == "bi_rnn":
        bi_rnn_layer = layers.Bidirectional(layers.SimpleRNN(units=n_units, activation='relu', dropout=dropout))
        
        return lambda feature: bi_rnn_layer(dropout_layer(embedding_layer(vec_layer(feature))))
    
    elif layer_type == "gru":
        gru_layer = layers.Bidirectional(layers.GRU(units=n_units, activation='relu', dropout=dropout))
        
        return lambda feature: gru_layer(dropout_layer(embedding_layer(vec_layer(feature))))
        

def get_normalization_layer(name, dataset):
    """Create everything that is needed for a numerical input pipeline.

    Args:
        name (string): name of the feature
        dataset (tf.DataSet): tensorflow dataaset

    Returns:
        lambda function: numerical input pipeline
    """
    # Create a Normalization layer for our feature.
    normalizer = exp_preprocessing.Normalization()

    # Prepare a Dataset that only yields our feature.
    feature_ds = dataset.map(lambda x, y: x[name])

    # Learn the statistics of the data.
    normalizer.adapt(feature_ds)

    return normalizer


def get_binary_vector_input(name, dataset):
    rescaling = exp_preprocessing.Rescaling(scale=2, offset=-1)

    # Prepare a Dataset that only yields our feature.
    feature_ds = dataset.map(lambda x, y: x[name])

    # Learn the statistics of the data.
    rescaling.adapt(feature_ds)

    return rescaling


def combine_input_pipelines(categ_vars, text_vars, numerical_vars, bin_vars, train_ds, settings=None):
    """Combines the input pipelines for the given features.

    Args:
        categ_vars (list of strings): list of categorical feature names
        text_vars (list of strings): list of textual feature names
        numerical_vars (list of strings): list of numerical feature names
        bin_vars (list of strings): list of binary feature names
        train_ds (tf.DataSet): tensorflow dataset
        settings (dict): settings dictionary

    Returns:
        tuple of lists: encoded_features, all_inputs
    """
    
    encoded_features = []
    all_inputs = []

    # Categorical columns
    for col in categ_vars:
        print(f"  Building CATEGORICAL input pipeline for variable '{col}'")
        # Create input object
        categorical_col = tf.keras.Input(shape=(1,), name=col, dtype='string')
        # Create layer
        encoding_layer = get_category_encoding_layer(col, train_ds, dtype='string', max_tokens=5)
        # Give input to layer (adapt)
        encoded_method_col = encoding_layer(categorical_col)
        
        all_inputs.append(categorical_col)
        encoded_features.append(encoded_method_col)

    # Text columns
    for col in text_vars:
        print(f"  Building TEXTUAL input pipeline for variable '{col}'")

        text_col = tf.keras.Input(shape=(1,), dtype=tf.string, name=col)
        encoding_layer = get_text_encoding_layer(col, train_ds ,
                                                max_features=settings['text']['max_features'],
                                                max_len=settings['text']['max_len'], 
                                                embedding_dim=settings['text']['embedding_dim'],
                                                layer_type=settings['text']['layer_type'], 
                                                n_units=settings['text']['n_units'], 
                                                dropout=settings['text']['dropout']) if settings is not None else \
                                get_text_encoding_layer(col, train_ds)                    
        encoded_text_col = encoding_layer(text_col)
        
        all_inputs.append(text_col)
        encoded_features.append(encoded_text_col)
        

    # Numerical Columns
    for col in numerical_vars:
        print(f"  Building NUMERICAL input pipeline for variable '{col}'")
        num_col = tf.keras.Input(shape=(1,), name=col)
        norm_layer = get_normalization_layer(col, train_ds)
        encoded_num_col = norm_layer(num_col)
        
        all_inputs.append(num_col)
        encoded_features.append(encoded_num_col)

    # Binary Vectors Columns
    for col in bin_vars:
        print(f"  Building BINARY VECTOR input pipeline for variable '{col}'")
        bin_col = tf.keras.Input(shape=(1,), name=col)
        bin_layer = get_binary_vector_input(col, train_ds)
        encoded_bin_col = bin_layer(bin_col)
        
        all_inputs.append(bin_col)
        encoded_features.append(encoded_bin_col)

    print("> All input pipelines built.")
    return encoded_features, all_inputs


def create_model(encoded_features, all_inputs, n_classes, n_units=128, n_layers=1, dropout=0.3):
    """Creates & compiles the tensorflow model

    Args:
        encoded_features (list): list of encoded features (created with `combine_input_pipelines`)
        all_inputs (list): list of all inputs (created with `combine_input_pipelines`)
        n_classes (int): number of target classes
        n_units (int, optional): number of units to use in the final fully connected layers. Defaults to 128.
        n_layers (int, optional): number of final fully connected layers. Defaults to 1.
        dropout (float, optional): dropout percentage after each final fully connected layer. Defaults to 0.3.

    Returns:
        tf model: the compiled tensorflow model
    """
    all_features = tf.keras.layers.concatenate(encoded_features)
    for i in range(n_layers):
        if i == 0:
            x = tf.keras.layers.Dense(n_units, activation="relu")(all_features)
        else: 
            x = tf.keras.layers.Dense(n_units, activation="relu")(x)
        x = tf.keras.layers.Dropout(dropout)(x)
    output = tf.keras.layers.Dense(n_classes, activation='softmax')(x)
    model = tf.keras.Model(all_inputs, output)
    model.compile(optimizer='adam',
                loss="sparse_categorical_crossentropy",
                metrics=["accuracy",
                        #F1Score(n_classes, "micro")
                        ])
    model.summary()
    return model


def create_model_graph(model):
    """Create the model plot for a given model.

    Args:
        model (tensorflow model): model to be represented.

    Returns:
        plot: plot created by `tf.keras.utils.plot_model`
    """
    return tf.keras.utils.plot_model(model, show_shapes=True, rankdir="LR")


def fit_model(model, train_ds, test_ds, epochs= 30, early_stopping=True):
    """Fit a given model given a train and test dataset.

    Args:
        model (tensorflow model): tf model to be trained
        train_ds (tf.DataSet): training data
        test_ds (tf.DataSet): test data
        epochs (int, optional): max number of epochs. Defaults to 30.
        early_stopping (bool, optional): flag whether to use early stopping. Defaults to True.
    """
    from tensorflow.keras.callbacks import EarlyStopping

    callbacks = [] if not early_stopping else [EarlyStopping(monitor='val_accuracy', patience=5)]

    model.fit(train_ds, epochs=epochs, validation_data=test_ds, callbacks=callbacks)


def create_eval_dict(test_df, label_column, oe, model):
    """Create an evaluation dict.

    Args:
        test_df (pd.DataFrame): test data
        label_column (string): target feature name
        oe ([type]): Ordinal encoder used for target feature conversion
        model (tf model): model to evaluate

    Returns:
        dict: dict containing some evaluation statistics
    """
    eval_ds = df_to_dataset(test_df, label_column, batch_size=128, shuffle=False)
    y_true = np.concatenate([y for x,y in eval_ds])
    y_pred = tf.argmax(model.predict(eval_ds), axis=1)

    from sklearn.metrics import classification_report
    eval_dict = classification_report(y_true, y_pred, 
                                      output_dict=True)

    # Transform labels in classification_report
    for trans_label in [0.0, 1.0]:
        inversed_label = oe.inverse_transform([[trans_label]])[0][0]
        eval_dict[inversed_label] = eval_dict.pop(str(trans_label))

    from sklearn.metrics import confusion_matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    cm_dict = {"tn": tn, "fp": fp, "fn": fn, "tp": tp}

    eval_dict["cm"]=cm_dict

    true_value_counts = test_df[label_column].value_counts().to_dict()
    eval_dict['true_counts'] = true_value_counts
    eval_dict['label_order'] = [x for x in oe.categories_[0]]

    return eval_dict