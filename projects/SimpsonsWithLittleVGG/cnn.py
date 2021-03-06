#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 22:33:37 2020
CNN con modelo modificado de la VGG16, más simple.
Usado para clasificar personajes de la serie Simpons.
@author: david
"""

from __future__ import print_function
import keras
from keras.preprocessing.image import ImageDataGenerator
from keras.preprocessing import image
from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout, Activation, Flatten, BatchNormalization
from keras.layers import Conv2D, MaxPooling2D
from keras.layers.advanced_activations import ELU
from keras.utils.vis_utils import plot_model
from keras.optimizers import RMSprop, SGD, Adam
from keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import os
from os import listdir
from os.path import isfile, join
import re
import sklearn
from sklearn.metrics import classification_report, confusion_matrix
import cv2

num_classes = 20
img_rows, img_cols = 32, 32
batch_size = 16

train_data_dir = "/home/david/datasets/simpsons/train"
validation_data_dir = "/home/david/datasets/simpsons/validation"

# Vamos a usar algo de aumento de datos
train_datagen = ImageDataGenerator(
        rescale = 1. / 255,
        rotation_range = 30,
        width_shift_range = 0.3,
        height_shift_range = 0.3,
        horizontal_flip = True,
        fill_mode = 'nearest'
    )

validation_datagen = ImageDataGenerator(rescale = 1. / 255)

train_generator = train_datagen.flow_from_directory(
        train_data_dir,
        target_size = (img_rows, img_cols),
        batch_size = batch_size,
        class_mode = 'categorical'
    )

validation_generator = validation_datagen.flow_from_directory(
        validation_data_dir,
        target_size = (img_rows, img_cols),
        batch_size = batch_size,
        class_mode = 'categorical'
    )

# Construimos el modelo (LittleVGG)
model = Sequential()

# First Conv-ReLU layer
model.add(Conv2D(64, (3, 3), padding='same', input_shape=(img_rows, img_cols, 3)))
model.add(Activation('relu'))
model.add(BatchNormalization())

# Second Conv-ReLU layer
model.add(Conv2D(64, (3, 3), padding = 'same', input_shape = (img_rows, img_cols, 3)))
model.add(Activation('relu'))
model.add(BatchNormalization())

# Max Pooling with Dropout
model.add(MaxPooling2D(pool_size = (2,2)))
model.add(Dropout(0.2))

# 3rd set of CONV-ReLU layers
model.add(Conv2D(128, (3,3), padding='same'))
model.add(Activation('relu'))
model.add(BatchNormalization())

# 4th set of CONV-ReLU layers
model.add(Conv2D(128, (3,3), padding='same'))
model.add(Activation('relu'))
model.add(BatchNormalization())

# Max Pooling with Dropout
model.add(MaxPooling2D(pool_size=(2,2)))
model.add(Dropout(0.2))

# 5th set of CONV-ReLU layers
model.add(Conv2D(256, (3,3), padding='same'))
model.add(Activation('relu'))
model.add(BatchNormalization())

# 6th set of CONV-ReLU layers
model.add(Conv2D(256, (3,3), padding='same'))
model.add(Activation('relu'))
model.add(BatchNormalization())

# Max Pooling with Dropout
model.add(MaxPooling2D(pool_size=(2,2)))
model.add(Dropout(0.2))

# First set of FC or Dense Layers
model.add(Flatten())
model.add(Dense(256))
model.add(Activation('relu'))
model.add(BatchNormalization())
model.add(Dropout(0.5))

# Second set of FC or Dense Layers
model.add(Dense(256))
model.add(Activation('relu'))
model.add(BatchNormalization())
model.add(Dropout(0.5))

# Final Dense layer
model.add(Dense(num_classes))
model.add(Activation("softmax"))

print(model.summary())

# Mostrar la arquitectura de la red neuronal
plot_model(model, to_file="littleVGG.png", show_shapes=True, show_layer_names=True)
img = mpimg.imread("littleVGG.png")
plt.figure(figsize = (100, 70))
imgplot = plt.imshow(img)

# Creamos los callbacks para el entrenamiento
checkpoint = ModelCheckpoint(
        "/home/david/datasets/simpsons/models/simpsons_little_vgg.h5",
        monitor="val_loss",
        mode="min",
        save_best_only=True,
        verbose=1
    )

earlystop = EarlyStopping(
        monitor='val_loss',
        min_delta=0,
        patience=3,
        verbose=1,
        restore_best_weights = True
    )

reduce_lr = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.2,
        patience=3,
        verbose=1,
        min_delta=0.00001
    )

# we put our call backs into a callback list
callbacks = [earlystop, checkpoint, reduce_lr]

# Guardamos el modelo
model.compile(
        optimizer = Adam(lr=0.01),
        loss='categorical_crossentropy',
        metrics = ['accuracy']
    )


# Entrenamos la red
nb_train_samples = 19548
nb_validation_samples = 990
epochs = 3

history = model.fit_generator(
        train_generator,
        steps_per_epoch = nb_train_samples // batch_size,
        epochs = epochs,
        callbacks = callbacks,
        validation_data = validation_generator,
        validation_steps = nb_validation_samples // batch_size
    )

# Análisis de rendimiento
# Se requiere recrear el generador de validación con shuffle = false
validation_generator = validation_datagen.flow_from_directory(
        validation_data_dir,
        target_size = (img_rows, img_cols),
        batch_size = batch_size,
        class_mode = 'categorical',
        shuffle = False
    )

class_labels = validation_generator.class_indices
class_labels = {v: k for k, v in class_labels.items()}
classes = list(class_labels.values())

nb_train_samples = 19548
nb_validation_samples = 990

# Matriz de confusión y reporte de clasificación
Y_pred = model.predict_generator(
        validation_generator, nb_validation_samples // batch_size+1
    )
y_pred = np.argmax(Y_pred, axis=1)

print('Confusion Matrix')
print(confusion_matrix(validation_generator.classes, y_pred))
print('Classification Report')
target_names = list(class_labels.values())
print(classification_report(validation_generator.classes, y_pred, target_names=target_names))

plt.figure(figsize=(8,8))
cnf_matrix = confusion_matrix(validation_generator.classes, y_pred)

plt.imshow(cnf_matrix, interpolation='nearest')
plt.colorbar()
tick_marks = np.arange(len(classes))
_ = plt.xticks(tick_marks, classes, rotation=90)
_ = plt.yticks(tick_marks, classes)


# Cargamos el modelo
classifier = load_model('/home/david/datasets/simpsons/models/simpsons_little_vgg.h5')


## TEST
def draw_test(name, pred, im, true_label):
    BLACK = [0,0,0]
    expanded_image = cv2.copyMakeBorder(
            im, 160, 0, 0, 300, cv2.BORDER_CONSTANT, value=BLACK
        )
    cv2.putText(
            expanded_image, "predicted - " + pred, (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2
        )
    cv2.putText(
            expanded_image, "true - " + true_label, (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2
        )
    cv2.imshow(name, expanded_image)

def getRandomImage(path, img_width, img_height):
    """function loads a random images from a random folder in our test path """
    folders = list(
            filter(lambda x: os.path.isdir(os.path.join(path, x)), os.listdir(path))
        )
    random_directory = np.random.randint(0,len(folders))
    path_class = folders[random_directory]
    file_path = path + path_class
    file_names = [f for f in listdir(file_path) if isfile(join(file_path, f))]
    random_file_index = np.random.randint(0,len(file_names))
    image_name = file_names[random_file_index]
    final_path = file_path + "/" + image_name
    return image.load_img(
        final_path, target_size = (img_width, img_height)), final_path, path_class


# dimensions of our images
img_width, img_height = 32, 32

files = []
predictions = []
true_labels = []

# predicting images
for i in range(0, 10):
    path = '/home/david/datasets/simpsons/validation/'
    img, final_path, true_label = getRandomImage(path, img_width, img_height)
    files.append(final_path)
    true_labels.append(true_label)
    x = image.img_to_array(img)
    x = x * 1./255
    x = np.expand_dims(x, axis=0)
    images = np.vstack([x])
    classes = classifier.predict_classes(images, batch_size=10)
    predictions.append(classes)

for i in range(0, len(files)):
    image = cv2.imread((files[i]))
    image = cv2.resize(image, None, fx=5, fy=5, interpolation = cv2.INTER_CUBIC)
    draw_test("Prediction", class_labels[predictions[i][0]], image, true_labels[i])
    cv2.waitKey(0)

cv2.destroyAllWindows()
