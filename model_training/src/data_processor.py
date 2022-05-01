import os
import json
import copy
import nltk
import re
import json
from nltk.tokenize import WhitespaceTokenizer, TreebankWordTokenizer

class InputExample(object):
    def __init__(self, guid, context, attributes, labels):
        self.guid = guid
        self.context = context
        self.attributes = attributes
        self.labels = labels

    def __repr__(self):
        return str(self.to_json_string())

    def to_dict(self):
        """Serializes this instance to a Python dictionary."""
        output = copy.deepcopy(self.__dict__)
        return output

    def to_json_string(self):
        """Serializes this instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


class InputFeatures(object):
    def __init__(self, context_input_ids, context_input_mask, context_input_len,
                 attribute_input_ids, attribute_input_mask, attribute_input_len,
                 context_type_ids, attribute_type_ids, label_ids):
        self.context_input_ids = context_input_ids
        self.context_input_mask = context_input_mask
        self.context_input_len = context_input_len
        self.context_type_ids = context_type_ids
        self.attribute_input_ids = attribute_input_ids
        self.attribute_input_mask = attribute_input_mask
        self.attribute_input_len = attribute_input_len
        self.attribute_type_ids = attribute_type_ids
        self.label_ids = label_ids

    def __repr__(self):
        return str(self.to_json_string())

    def to_dict(self):
        """Serializes this instance to a Python dictionary."""
        output = copy.deepcopy(self.__dict__)
        return output

    def to_json_string(self):
        """Serializes this instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


class MedicalDataProcessor(object):
    def get_debug_examples(self, data_dir):
        return self._create_examples(self._read_data_span(os.path.join(data_dir, "dataset_debug.json")), 'train')

    def get_train_examples(self, data_dir):
        return self._create_examples(self._read_data_span(os.path.join(data_dir, "fatty_train_data.json")), 'train')

    def get_dev_examples(self, data_dir):
        return self._create_examples(self._read_data_span(os.path.join(data_dir, "dataset_dev.json")), 'dev')

    def get_test_examples(self, data_dir):
        return self._create_examples(self._read_data_span(os.path.join(data_dir, "fatty_test_data.json")), 'test')

    def get_labels(self):
        return ['B-a', 'I-a', 'O', '[CLS]', '[SEP]']

    def _word_tokenize(self, sentence):
        return nltk.word_tokenize(sentence)

    def _span_tokenize(self, sentence):
        return TreebankWordTokenizer().span_tokenize(sentence)

    def _get_value_offset(self, context_words, value):
        value_words = self._word_tokenize(value)
        value_no_space = ''.join(value_words)

        for i in range(len(context_words) - len(value_words) + 1):
            windows = context_words[i: i + len(value_words)]
            if value_words == windows:
                return i, i + len(value_words) - 1

            windows = ''.join(windows)
            if value_no_space in windows:
                return i, i + len(value_words) - 1

        raise Exception('Attribute Value Parsing Error, context: {}, '
                        'value: {}, sentence: {}, value tokens: {}'.format(context_words, value,
                                                                           " ".join(context_words), value_words))
    
    def _read_data_span(self, input_file):
        data = []
        with open(input_file, 'r') as fp:
            jsonObj = json.load(fp)

        for line in jsonObj:
            context = line['content']
            attribute = line['attribute']
            values = line['values']
            
            context_token_span = self._span_tokenize(context)
            attribute_token_span = self._span_tokenize(attribute)

            if len(values) == 0:
                context_words = [context[span[0]: span[1]] for span in context_token_span]
                labels = ['O'] * len(context_words)
            else:
                context_words = []
                labels = []
                value_idx = -1
                value_start = -1
                value_end = -1
                for span in context_token_span:
                    if span[0] > value_end and value_idx < len(values) - 1:
                        value_idx += 1
                        value_start = values[value_idx][0]
                        value_end = values[value_idx][1]
                        value = values[value_idx][2]
                        assert context[value_start: value_end] == value

                    if span[0] == value_start:
                        labels.append('B-a')
                    elif value_start < span[0] < span[1] <= value_end and (labels[-1] == 'B-a' or labels[-1] == 'I-a'):
                        labels.append('I-a')
                    elif value_start < span[0] and span[1] - 1 == value_end and (context[span[1] - 1] == '.' and labels[-1] == 'B-a' or labels[-1] == 'I-a'):
                        labels.append('I-a')
                    else:
                        labels.append('O')

                    context_words.append(context[span[0]: span[1]])

            attribute_words = [attribute[span[0]: span[1]] for span in attribute_token_span]
            assert len(labels) == len(context_words)
            data.append({"context": context_words, "labels": labels, 'attributes': attribute_words})
        return data

    def _read_data(self, input_file):
        data = []
        with open(input_file, 'r') as fp:
            jsonObj = json.load(fp)

        for line in jsonObj:
            context = line['content']
            attribute = line['attribute']
            value = line['value']

            context_words = self._word_tokenize(context)
            attribute_words = self._word_tokenize(attribute)
            labels = ['O'] * len(context_words)

            if value != '':
                assert value in context
                i, j = self._get_value_offset(context_words, value)
                if i == j:
                    labels[i] = 'B-a'
                else:
                    labels[i] = 'B-a'
                    labels[i + 1: j] = ['I-a'] * (j - i)

            assert len(labels) == len(context_words)
            print(context_words)
            print(labels)
            print()
            data.append({"context": context_words, "labels": labels, 'attributes': attribute_words})

        return data

    def _create_examples(self, data, data_type):
        examples = []
        for (i, line) in enumerate(data):
            guid = "%s-%s" % (data_type, i)
            context = line['context']
            attribute = line['attributes']
            labels = line['labels']
            examples.append(InputExample(guid=guid, context=context, attributes=attribute, labels=labels))
        return examples

class TaggingProcessor(object):
    def get_debug_examples(self, data_dir):
        return self._create_examples(self._read_data(os.path.join(data_dir, "opentags.debug")), 'train')

    def get_train_examples(self, data_dir):
        return self._create_examples(self._read_data(os.path.join(data_dir, "opentags.train")), 'train')

    def get_dev_examples(self, data_dir):
        return self._create_examples(self._read_data(os.path.join(data_dir, "opentags.dev")), 'dev')

    def get_test_examples(self, data_dir):
        return self._create_examples(self._read_data(os.path.join(data_dir, "opentags.test")), 'test')

    def get_labels(self):
        return ['B-a', 'I-a', 'O', '[CLS]', '[SEP]']

    def _word_tokenize(self, sentence):
        return nltk.word_tokenize(sentence)

    def _get_value_offset(self, context_words, value):
        value_words = self._word_tokenize(value)
        value_no_space = ''.join(value_words)

        for i in range(len(context_words) - len(value_words) + 1):
            windows = context_words[i: i + len(value_words)]
            if value_words == windows:
                return i, i + len(value_words) - 1

            windows = ''.join(windows)
            if value_no_space in windows:
                return i, i + len(value_words) - 1

        raise Exception('Attribute Value Parsing Error, context: {}, '
                        'value: {}, sentence: {}, value tokens: {}'.format(context_words, value,
                                                                           " ".join(context_words), value_words))

    def _read_data(self, input_file):
        data = []
        with open(input_file, 'r') as fp:
            for line in fp.readlines():
                line = line.strip().split('\01')

                context = line[0].strip()
                attribute = line[1].strip()
                value = line[2].strip()

                context_words = self._word_tokenize(context)
                attribute_words = self._word_tokenize(attribute)
                labels = ['O'] * len(context_words)

                if value != 'NULL':
                    assert value in context
                    i, j = self._get_value_offset(context_words, value)
                    if i == j:
                        labels[i] = 'B-a'
                    else:
                        labels[i] = 'B-a'
                        labels[i + 1: j] = ['I-a'] * (j - i)

                data.append({"context": context_words, "labels": labels, 'attributes': attribute_words})

        return data

    def _create_examples(self, data, data_type):
        examples = []
        for (i, line) in enumerate(data):
            guid = "%s-%s" % (data_type, i)
            context = line['context']
            attribute = line['attributes']
            labels = line['labels']
            examples.append(InputExample(guid=guid, context=context, attributes=attribute, labels=labels))
        return examples

