# coding: utf-8
from scipy import misc
import numpy as np
import pandas as pd

#input parameters
single_side = 350
n_input = single_side * single_side
num_images = 1584

image_dir = 'images/processed_2/'

# Converting to matrix
train_im = np.zeros(shape=(num_images, n_input)) # initiate array
for i in range(1,num_images):
    im = misc.imread(image_dir + str(i) + ".jpg") # transform to matrix
    train_im[i-1] = im.ravel() # Shift index due to numpy's zero-indexing

# Importing data to matrix
train_csv = pd.read_csv('train.csv')
train_idx = train_csv['id'] - 1 # subtract 1 to take care of zero-indexing
train = train_im[train_idx] # extract training pictures from images

# Separate labels
labels = pd.get_dummies(train_csv['species']) # one-hot encoding
labels = labels.as_matrix() # convert dataframe to matrix

train_num = 800

# Shuffling data
temp = np.hstack((train, labels)) # combine matrix column-wise
np.random.shuffle(temp)

# Split train, test, and label matrixes
train = temp[:,:n_input][:train_num]
labels = temp[:,n_input:][:train_num]
test_image = temp[:,:n_input][train_num:]
test_labels = temp[:,n_input:][train_num:]

print "TRAIN"
print train.shape
print labels.shape
print "TEST"
print test_image.shape
print test_labels.shape

import tensorflow as tf

# Import MNIST data
#  from tensorflow.examples.tutorials.mnist import input_data
#  mnist = input_data.read_data_sets("MNIST_data/", one_hot=True)

# Parameters
learning_rate = 0.001
training_iters = 2000
batch_size = 100
display_step = 1

# Network Parameters
#  n_input = 784 # MNIST data input (img shape: 28*28)
#  n_classes = 10 # MNIST total classes (0-9 digits)
n_classes = 99
dropout = 0.75 # Dropout, probability to keep units

# tf Graph input
x = tf.placeholder(tf.float32, [None, n_input])
y = tf.placeholder(tf.float32, [None, n_classes])
keep_prob = tf.placeholder(tf.float32) #dropout (keep probability)

# Create some wrappers for simplicity
def conv2d(x, W, b, strides=1):
    # Conv2D wrapper, with bias and relu activation
    x = tf.nn.conv2d(x, W, strides=[1, strides, strides, 1], padding='SAME')
    x = tf.nn.bias_add(x, b)
    return tf.nn.relu(x)


def maxpool2d(x, k=2):
    # MaxPool2D wrapper
    return tf.nn.max_pool(x, ksize=[1, k, k, 1], strides=[1, k, k, 1],
                          padding='SAME')


# Create model
def conv_net(x, weights, biases, dropout):
    # Reshape input picture
    x = tf.reshape(x, shape=[-1, 28, 28, 1])

    # Convolution Layer
    conv1 = conv2d(x, weights['wc1'], biases['bc1'])
    # Max Pooling (down-sampling)
    conv1 = maxpool2d(conv1, k=2)

    # Convolution Layer
    conv2 = conv2d(conv1, weights['wc2'], biases['bc2'])
    # Max Pooling (down-sampling)
    conv2 = maxpool2d(conv2, k=2)

    # Fully connected layer
    # Reshape conv2 output to fit fully connected layer input
    fc1 = tf.reshape(conv2, [-1, weights['wd1'].get_shape().as_list()[0]])
    fc1 = tf.add(tf.matmul(fc1, weights['wd1']), biases['bd1'])
    fc1 = tf.nn.relu(fc1)
    # Apply Dropout
    fc1 = tf.nn.dropout(fc1, dropout)

    # Output, class prediction
    out = tf.add(tf.matmul(fc1, weights['out']), biases['out'])
    return out

# Store layers weight & bias
weights = {
    # 5x5 conv, 1 input, 32 outputs
    'wc1': tf.Variable(tf.random_normal([5, 5, 1, 32])),
    # 5x5 conv, 32 inputs, 64 outputs
    'wc2': tf.Variable(tf.random_normal([5, 5, 32, 64])),
    # fully connected, 7*7*64 inputs, 1024 outputs
    'wd1': tf.Variable(tf.random_normal([7*7*64, 1024])),
    # 1024 inputs, 10 outputs (class prediction)
    'out': tf.Variable(tf.random_normal([1024, n_classes]))
}

biases = {
    'bc1': tf.Variable(tf.random_normal([32])),
    'bc2': tf.Variable(tf.random_normal([64])),
    'bd1': tf.Variable(tf.random_normal([1024])),
    'out': tf.Variable(tf.random_normal([n_classes]))
}

# Construct model
pred = conv_net(x, weights, biases, keep_prob)

# Define loss and optimizer
cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=pred, labels=y))
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)

# Evaluate model
correct_pred = tf.equal(tf.argmax(pred, 1), tf.argmax(y, 1))
accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

# Initializing the variables
init = tf.initialize_all_variables()

# Launch the graph
with tf.Session() as sess:
    sess.run(init)
    #  step = 1
    step = 0
    # Keep training until reach max iterations
    repeater_modulus = train_num / batch_size
    while step * batch_size < training_iters:
        #  batch_x, batch_y = mnist.train.next_batch(batch_size)
        current_batch = step % repeater_modulus
        begin = current_batch * batch_size
        end = begin + batch_size
        batch_x = train[begin:end]
        batch_y = labels[begin:end]
        # Run optimization op (backprop)
        sess.run(optimizer, feed_dict={x: batch_x, y: batch_y,
                                       keep_prob: dropout})
        if step % display_step == 0:
            # Calculate batch loss and accuracy
            loss, acc = sess.run([cost, accuracy], feed_dict={x: batch_x,
                                                              y: batch_y,
                                                              keep_prob: 1.})
            print "Iter " + str(step*batch_size) + ", Minibatch Loss= " + \
                  "{:.6f}".format(loss) + ", Training Accuracy= " + \
                  "{:.5f}".format(acc)
        step += 1
    print "Optimization Finished!"

    # Calculate accuracy for 256 mnist test images
    print "Testing Accuracy:", \
        sess.run(accuracy, feed_dict={x: test_image, y: test_labels, keep_prob: 1.})
        #  sess.run(accuracy, feed_dict={x: mnist.test.images[:256],
                                      #  y: mnist.test.labels[:256],
                                      #  keep_prob: 1.})
