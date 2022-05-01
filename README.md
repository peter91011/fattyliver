## Key - Value Extraction
A Pytorch implementation of Key-Value Extraction based on the paper "Scaling Up Open Tagging from Tens to Thousands: Comprehension Empowered Attribute Value Extraction from Product Title" (ACL 2019). [[pdf]](https://www.aclweb.org/anthology/P19-1514.pdf)

### Requirements:
* torch: 1.8.1+cu111
* Flask: 1.1.2
* transformers: 4.8.2
* nltk: 3.5

### Structure of code
``` 
docs                                # Store some documents and slides about the model
   |-- Key-Value Extraction.pptx
model_serving                       # This folder are used for model serving in production stage
   |-- models                       # The model codes under this fodler are same in the model_training
   |   |-- crf.py
   |   |-- layers.py
   |   |-- tagging_model.py
model_training
   |-- data                         # Store the training and testing dataset
   |   |-- ehr
   |   |   |-- dataset_test.json
   |   |   |-- dataset_train.json
   |-- src                          # source code for model training
   |   |-- app.py                   # flask demo for demonstration
   |   |-- config.py                # model config file used for loading parameters for inference
   |   |-- data_loader.py           # load the training dataset to convert the features
   |   |-- data_processor.py        # data processing for feature converting
   |   |-- evaluate.py              # evaluate the model performacne
   |   |-- inference.py             # main code for model inference used web demo not by production
   |   |-- main.py                  # main function for training ad evaluating the model
   |   |-- metrics.py               # BIO taging performacne metrics
   |   |-- models                   # core model files including layers and model
   |   |   |-- crf.py
   |   |   |-- layers.py
   |   |   |-- tagging_model.py
   |   |-- static                   # static files for web demo
   |   |   |-- app.css
   |   |   |-- app.js
   |   |   |-- loading.gif
   |   |-- templates                # html template for web demo
   |   |   |-- index.html
   |   |-- trainer.py               # functions for model training and optmization
   |   |-- utils.py                 # utility functions
requirements.txt
```

### Preparing Training Dataset
The dataset is located at the folder /model_training/data/ehr. The whole dataset is a list saved with JSON format as shown below. 
```
[sample_1, sample_2, ..., sample_n]
```
Each sample is dictionary format, which has three keys:
* "content": input sentence with string format
* "attribute": input key with string format
* "values": a list contains all the values corresponding to the key ("attribute") that appeared in the content. Each value is three length list with the ["start position", "end position", value] format. Here, the "end position" is the actual position of value plus one. Hence, you just need content [start: end] to extract value in Python.
```
{
    "content": string,
    "attribute": string,
    "values": [value_1, value_2, ..., value_n]
}
```

Here is a piece of example dataset extracted from train dataset
```
[   
    ...
    {
        "content": "female. HPI Patient with mild sleep apnea AHI 11.9 increase in supine posture. Right lateral AHI 2.3 left lateral 4.5. Patient currently on CPAP 4-14 cm EPR 2. ",
        "attribute": "AHI",
        "values": [
            [
                46,
                50,
                "11.9"
            ]
        ]
    },
    ...
]
```
In the file data_processor.py, it will label the data sample into BIO format based on start and end position automatically, as shown below,
```
['female.', 'HPI', 'Patient', 'with', 'mild', 'sleep', 'apnea', 'AHI', '11.9', 'increase', 'in', 'supine', 'posture.', 'Right', 'lateral', 'AHI', '2.3', 'left', 'lateral', '4.5.', 'Patient', 'currently', 'on', 'CPAP', '4-14', 'cm', 'EPR', '2', '.']
['O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'B-a', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O', 'O']
``` 

After preparing your training dataset, you need to put your dataset under the folder ("data/").

### Train and Evaluate
The file main.py is the main entry to train and evaluate the model. Please read the code to know the parameters you can configure to train the model. Here are the most common parameters to tune when training a model
* num_train_epochs: the training epochs
* max_seq_length: the length of context with the unit in token
* max_attr_length: the length of attribute with unit in token
* data_dir: specify the input data directory
* output_dir: specify the output directory where the model and performance results are saved. And the default output folder will be /outputs
* do_train: wheter to train a model 
* do_eval: whether to run evaluation on the test set.
This is an example to train and evaluate the model simultaneously.
```
cd model_training/src
python main.py --data_dir ../data/ehr/ --num_train_epochs 50 --do_train --do_eval --train_batch_size 32 --max_seq_length 80 --max_attr_length 8
```
This is an example to evaluate the model only, if you already have trained a model, and evaluate with a new test datatest
```
cd model_training/src
python main.py --data_dir ../data/ehr/ --do_eval --eval_batch_size 8 --max_seq_length 80 --max_attr_length 8
```
After finishing the training and evaluation, the model outputs and performance results will be saved under the folder /outputs, if you use the default output directory

### Demo
There is a web demo to demonstrate the model using Flask. You can run the demo after training a model.

To run the demo, you need to configure the config file (model_training/src/config.py) based on the trained model. Here is an example of config file
```
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
MODEL_DIR = os.path.join(ROOT_PATH, "../outputs")
BERT_MODEl = 'bert-base-uncased'
PORT_NUMBER = 8006
MAX_SEQ_LEN = 80
MAX_ATTR_LEN = 8
BATCH_SIZE = 16
LABEL_LIST = ['B-a', 'I-a', 'O', '[CLS]', '[SEP]']
DEVICE = torch.device("cpu")
```
Then, you can use run the demo with these commands
```
cd model_training/src
python app.py
```
You can access this demo through web browser (http://XXX.XXX.XXX.XXX:8006/), and the port number should be same as you configured in config.py. If everything goes well, you will see a demo as below,

![ScreenShot](/docs/app_demo.PNG)

### Inference