import tensorflow as tf
import keras.backend as K
import keras
from keras.datasets import mnist
from keras.models import Model
from keras.layers import Conv2D, Dense, Flatten, Input, MaxPooling2D, Lambda, Layer

def set_gpu_config(device = "0",fraction=0.25):
    config = tf.ConfigProto()
    config.gpu_options.per_process_gpu_memory_fraction = fraction
    config.gpu_options.visible_device_list = device
    K.set_session(tf.Session(config=config))


class ODEBlock(Model):
    def __init__(self, filters, kernel_size):
        self.t = K.constant([0],dtype="float32")

        x = Input((None,None,filters))
        y = Lambda(self.concat_t)(x)
        y = Conv2D(filters,kernel_size,padding="same",activation="relu")(y)
        y = Lambda(self.concat_t)(y)
        y = Conv2D(filters,kernel_size,padding="same",activation="relu")(y)
        super(ODEBlock, self).__init__(x, y)

    def concat_t(self,x):
        new_shape = tf.concat([tf.shape(x)[:-1], tf.ones((1,), "int32")], axis=0)
        t = tf.ones(shape=new_shape) * tf.reshape(self.t, (1, 1, 1, 1))
        return tf.concat([x, t], axis=-1)

    def call(self, x):
        return tf.contrib.integrate.odeint(self.ode_func, x, K.constant([0, 1],dtype="float32"), rtol=1e-3, atol=1e-3)[1]

    def ode_func(self, x, t):
        self.t = t
        return super(ODEBlock, self).call(x)


def build_model(input_shape, num_classes):
    x = Input(input_shape)
    y = Conv2D(32, (3, 3), activation='relu')(x)
    y = MaxPooling2D((2,2))(y)
    y = Conv2D(64, (3, 3), activation='relu')(y)
    y = MaxPooling2D((2,2))(y)
    y = ODEBlock(64, (3, 3))(y)
    y = Flatten()(y)
    y = Dense(num_classes, activation='softmax')(y)
    return Model(x,y)


set_gpu_config("0",0.25)

batch_size = 128
num_classes = 10
epochs = 10
image_shape = (28, 28, 1)

(x_train, y_train), (x_test, y_test) = mnist.load_data()
x_train = x_train.astype('float32') / 255.0
x_test = x_test.astype('float32') / 255.0

x_train = x_train.reshape((-1,) + image_shape)
x_test = x_test.reshape((-1,) + image_shape)

y_train = keras.utils.to_categorical(y_train, num_classes)
y_test  = keras.utils.to_categorical(y_test, num_classes)


model = build_model(image_shape, num_classes)

model.compile(loss=keras.losses.categorical_crossentropy,
              optimizer=keras.optimizers.Adam(),
              metrics=['accuracy'])

model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=epochs,
          verbose=1,
          validation_data=(x_test, y_test))


score = model.evaluate(x_test, y_test, verbose=0)
print('Test loss:', score[0])
print('Test accuracy:', score[1])