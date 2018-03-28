#!/usr/bin/python

from __future__ import print_function

from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import GRU
from keras.models import load_model

from keras.constraints import Constraint
from keras import backend as K

import sys
import re
import numpy as np

def printVector(f, vector, name):
    v = np.reshape(vector, (-1));
    #print('static const float ', name, '[', len(v), '] = \n', file=f)
    f.write('static const rnn_weight {}[{}] = {{\n   '.format(name, len(v)))
    for i in range(0, len(v)):
        f.write('{}'.format(min(127, int(round(256*v[i])))))
        if (i!=len(v)-1):
            f.write(',')
        else:
            break;
        if (i%8==7):
            f.write("\n   ")
        else:
            f.write(" ")
    #print(v, file=f)
    f.write('\n};\n\n')
    return;

def printLayer(f, hf, layer):
    weights = layer.get_weights()
    printVector(f, weights[0], layer.name + '_weights')
    if len(weights) > 2:
        printVector(f, weights[1], layer.name + '_recurrent_weights')
    printVector(f, weights[-1], layer.name + '_bias')
    name = layer.name
    activation = re.search('function (.*) at', str(layer.activation)).group(1).upper()
    if len(weights) > 2:
        f.write('const GRULayer {} = {{\n   {}_bias,\n   {}_weights,\n   {}_recurrent_weights,\n   {}, {}, ACTIVATION_{}\n}};\n\n'
                .format(name, name, name, name, weights[0].shape[0], weights[0].shape[1]/3, activation))
        hf.write('#define {}_SIZE {}\n'.format(name.upper(), weights[0].shape[1]/3))
        hf.write('extern const GRULayer {};\n\n'.format(name));
    else:
        f.write('const DenseLayer {} = {{\n   {}_bias,\n   {}_weights,\n   {}, {}, ACTIVATION_{}\n}};\n\n'
                .format(name, name, name, weights[0].shape[0], weights[0].shape[1], activation))
        hf.write('#define {}_SIZE {}\n'.format(name.upper(), weights[0].shape[1]))
        hf.write('extern const DenseLayer {};\n\n'.format(name));


def mean_squared_sqrt_error(y_true, y_pred):
    return K.mean(K.square(K.sqrt(y_pred) - K.sqrt(y_true)), axis=-1)

def my_crossentropy(y_true, y_pred):
    return K.mean(2*K.abs(y_true-0.5) * K.binary_crossentropy(y_pred, y_true), axis=-1)

def mymask(y_true):
    return K.minimum(y_true+1., 1.)

def msse(y_true, y_pred):
    return K.mean(mymask(y_true) * K.square(K.sqrt(y_pred) - K.sqrt(y_true)), axis=-1)

def mycost(y_true, y_pred):
    return K.mean(mymask(y_true) * (10*K.square(K.square(K.sqrt(y_pred) - K.sqrt(y_true))) + K.square(K.sqrt(y_pred) - K.sqrt(y_true)) + 0.01*K.binary_crossentropy(y_pred, y_true)), axis=-1)

def my_accuracy(y_true, y_pred):
    return K.mean(2*K.abs(y_true-0.5) * K.equal(y_true, K.round(y_pred)), axis=-1)

class WeightClip(Constraint):
    def __init__(self, c=2, name='WeightClip'):
        self.c = c

    def __call__(self, p):
        return K.clip(p, -self.c, self.c)

    def get_config(self):
        return {'name': self.__class__.__name__, 'c': self.c}


model = load_model(sys.argv[1], custom_objects={'msse': msse, 'mean_squared_sqrt_error': mean_squared_sqrt_error, 'my_crossentropy': my_crossentropy, 'mycost': mycost, 'WeightClip': WeightClip})

weights = model.get_weights()

f = open(sys.argv[2], 'w')
hf = open(sys.argv[3], 'w')

f.write('/*This file is automatically generated from a Keras model*/\n\n')
f.write('#ifdef HAVE_CONFIG_H\n#include "config.h"\n#endif\n\n#include "rnn.h"\n\n')

hf.write('/*This file is automatically generated from a Keras model*/\n\n')
hf.write('#ifndef RNN_DATA_H\n#define RNN_DATA_H\n\n#include "rnn.h"\n\n')

layer_list = []
for i, layer in enumerate(model.layers):
    if len(layer.get_weights()) > 0:
        printLayer(f, hf, layer)
    if len(layer.get_weights()) > 2:
        layer_list.append(layer.name)

hf.write('struct RNNState {\n')
for i, name in enumerate(layer_list):
    hf.write('  float {}_state[{}_SIZE];\n'.format(name, name.upper())) 
hf.write('};\n')

hf.write('\n\n#endif\n')

f.close()
hf.close()

