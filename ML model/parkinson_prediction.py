from tensorflow import keras
import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd
from keras.layers import *
from keras import backend as K
from keras.regularizers import l2
from keras.optimizers import Adam
from keras.optimizers import RMSprop
from keras.models import Model,load_model
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import ReduceLROnPlateau,EarlyStopping
from skimage import exposure
from PIL import Image
import cv2

#Image data generation
train_datagen = ImageDataGenerator(rescale = 1./255, 
                                  shear_range = 0.2, 
                                  zoom_range = 0.2, 
                                  horizontal_flip = True)

test_datagen = ImageDataGenerator(rescale = 1./255)

spiral_train_generator = train_datagen.flow_from_directory('spiral/training',
                                                   target_size = (128,128),
                                                   batch_size = 32,
                                                   class_mode = 'binary')

spiral_test_generator = test_datagen.flow_from_directory('spiral/testing',
                                                   target_size = (128,128),
                                                   batch_size = 32,
                                                   class_mode = 'binary')
wave_train_generator = train_datagen.flow_from_directory('wave/training',
                                                   target_size = (128,128),
                                                   batch_size = 32,
                                                   class_mode = 'binary')

wave_test_generator = test_datagen.flow_from_directory('wave/testing',
                                                   target_size = (128,128),
                                                   batch_size = 32,
                                                   class_mode = 'binary')

# Spiral model
spiral_model = keras.Sequential([
        layers.Conv2D(32,(3,3),input_shape=(128, 128, 3),activation='relu'),
        layers.MaxPooling2D(pool_size=(2,2)),
        layers.Conv2D(32,(3,3),activation='relu'),
        layers.MaxPooling2D(pool_size=(2,2)),
        layers.Flatten(),
        layers.Dense(activation='relu',units=128),
        layers.Dense(activation='sigmoid',units=1),
])

early_stopping = keras.callbacks.EarlyStopping(
    patience=10,
    min_delta=0.001,
    restore_best_weights=True,
)

spiral_model.compile(
    optimizer=Adam(lr=0.01),
    loss='binary_crossentropy',
    metrics=['accuracy'],
)

# Model fitting
history =spiral_model.fit_generator(
        spiral_train_generator,
        steps_per_epoch=spiral_train_generator.n//spiral_train_generator.batch_size,
        epochs=48,
        validation_data=spiral_test_generator,
        validation_steps=spiral_test_generator.n//spiral_test_generator.batch_size,
        callbacks=early_stopping)

# Uncomment this to plot the accuracy
# plt.ylabel('Accuracy')
# plt.plot(history.history['accuracy'], color = 'blue', label='Training Accuracy')

# Waves model
wave_model = keras.Sequential([
        layers.Conv2D(32,(3,3),input_shape=(128, 128, 3),activation='relu'),
        layers.MaxPooling2D(pool_size=(2,2)),
        layers.Conv2D(32,(3,3),activation='relu'),
        layers.MaxPooling2D(pool_size=(2,2)),
        layers.Flatten(),
        layers.Dense(activation='relu',units=128),
        layers.Dense(activation='sigmoid',units=1),
])

early_stopping = keras.callbacks.EarlyStopping(
    patience=10,
    min_delta=0.001,
    restore_best_weights=True,
)

wave_model.compile(
    optimizer=Adam(lr=0.01),
    loss='binary_crossentropy',
    metrics=['accuracy'],
)

# Model fitting
history =wave_model.fit_generator(
        wave_train_generator,
        steps_per_epoch=wave_train_generator.n//spiral_train_generator.batch_size,
        epochs=48,
        validation_data=wave_test_generator,
        validation_steps=wave_test_generator.n//wave_test_generator.batch_size,
        callbacks=early_stopping)

# Uncomment this to plot the accuracy
# plt.ylabel('Accuracy')
# plt.plot(history.history['accuracy'], color = 'blue', label='Training Accuracy')

doc_input = concatenate([spiral_model.output,wave_model.output])
dense_doc_1 = Dense(69,activation='relu')(doc_input)
dense_doc_2 = Dense(1,activation='sigmoid')(dense_doc_1)

def multiple_generators(gen1,gen2):
    while True:
        X1 = gen1.next()
        X2 = gen2.next()
        yield [X1[0], X2[0]], ((X1[1]+X2[1])/2)
            
input_generator = multiple_generators(spiral_train_generator,wave_train_generator)       
test_generator = multiple_generators(spiral_train_generator,wave_train_generator)      

def disable_trainable(model):
    for layer in model.layers:
        layer.trainable = False
        
disable_trainable(spiral_model)
disable_trainable(wave_model)

spiral_model.compile(optimizer=RMSprop(lr=5.11089622e-5), loss='binary_crossentropy', metrics=['accuracy'])
wave_model.compile(optimizer=RMSprop(lr=5.11089622e-5), loss='binary_crossentropy', metrics=['accuracy'])

doctor_model = Model(inputs=[spiral_model.input,wave_model.input],outputs=dense_doc_2)
doctor_model.compile(optimizer=RMSprop(lr=0.001), loss='binary_crossentropy', metrics=['accuracy'])

batch_size=24

doctor_model.fit_generator(input_generator,
                           validation_data=test_generator,
                           epochs=48,
                           steps_per_epoch=(2000//batch_size),
                           validation_steps=(800//batch_size),
                           verbose=1)

doctor_model.save('./custom_model_doctor.h5')
