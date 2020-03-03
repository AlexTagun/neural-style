# Copyright (c) 2015-2019 Anish Athalye. Released under GPLv3.

import math
import os
import re
from argparse import ArgumentParser
from collections import OrderedDict

import numpy as np
import scipy.misc
import tensorflow as tf
from PIL import Image

import vgg
from stylize import stylize, STYLE_LAYERS

# default arguments
CONTENT_WEIGHT = 5e0
CONTENT_WEIGHT_BLEND = 1
STYLE_WEIGHT = 5e2
TV_WEIGHT = 1e2
STYLE_LAYER_WEIGHT_EXP = 1
LEARNING_RATE = 1e1
BETA1 = 0.9
BETA2 = 0.999
EPSILON = 1e-08
STYLE_SCALE = 1.0
ITERATIONS = 1000
VGG_PATH = 'imagenet-vgg-verydeep-19.mat'
POOLING = 'max'


def build_parser():
    parser = ArgumentParser()
    parser.add_argument('--content',
            dest='content', help='content image',
            metavar='CONTENT', required=True)
    parser.add_argument('--style_images',
            dest='style_images',
            nargs='+', help='one or more style images',
            metavar='STYLE', required=True)
    parser.add_argument('--output',
            dest='output', help='output path',
            metavar='OUTPUT', required=True)
    parser.add_argument('--iterations', type=int,
            dest='iterations', help='iterations (default %(default)s)',
            metavar='ITERATIONS', default=ITERATIONS)
    parser.add_argument('--print-iterations', type=int,
            dest='print_iterations', help='statistics printing frequency',
            metavar='PRINT_ITERATIONS')
    parser.add_argument('--checkpoint-output',
            dest='checkpoint_output',
            help='checkpoint output format, e.g. output_{:05}.jpg or '
                 'output_%%05d.jpg',
            metavar='OUTPUT', default=None)
    parser.add_argument('--checkpoint-iterations', type=int,
            dest='checkpoint_iterations', help='checkpoint frequency',
            metavar='CHECKPOINT_ITERATIONS', default=None)
    parser.add_argument('--progress-write', default=False, action='store_true',
            help="write iteration progess data to OUTPUT's dir",
            required=False)
    parser.add_argument('--progress-plot', default=False, action='store_true',
            help="plot iteration progess data to OUTPUT's dir",
            required=False)
    parser.add_argument('--width', type=int,
            dest='width', help='output width',
            metavar='WIDTH')
    parser.add_argument('--style-scales', type=float,
            dest='style_scales',
            nargs='+', help='one or more style scales',
            metavar='STYLE_SCALE')
    parser.add_argument('--network',
            dest='network', help='path to network parameters (default %(default)s)',
            metavar='VGG_PATH', default=VGG_PATH)
    parser.add_argument('--content-weight-blend', type=float,
            dest='content_weight_blend',
            help='content weight blend, conv4_2 * blend + conv5_2 * (1-blend) '
                 '(default %(default)s)',
            metavar='CONTENT_WEIGHT_BLEND', default=CONTENT_WEIGHT_BLEND)
    parser.add_argument('--content-weight', type=float,
            dest='content_weight', help='content weight (default %(default)s)',
            metavar='CONTENT_WEIGHT', default=CONTENT_WEIGHT)
    parser.add_argument('--style-weight', type=float,
            dest='style_weight', help='style weight (default %(default)s)',
            metavar='STYLE_WEIGHT', default=STYLE_WEIGHT)
    parser.add_argument('--style-layer-weight-exp', type=float,
            dest='style_layer_weight_exp',
            help='style layer weight exponentional increase - '
                 'weight(layer<n+1>) = weight_exp*weight(layer<n>) '
                 '(default %(default)s)',
            metavar='STYLE_LAYER_WEIGHT_EXP', default=STYLE_LAYER_WEIGHT_EXP)
    parser.add_argument('--style-blend-weights', type=float,
            dest='style_blend_weights', help='style blending weights',
            nargs='+', metavar='STYLE_BLEND_WEIGHT')
    parser.add_argument('--tv-weight', type=float,
            dest='tv_weight',
            help='total variation regularization weight (default %(default)s)',
            metavar='TV_WEIGHT', default=TV_WEIGHT)
    parser.add_argument('--learning-rate', type=float,
            dest='learning_rate', help='learning rate (default %(default)s)',
            metavar='LEARNING_RATE', default=LEARNING_RATE)
    parser.add_argument('--beta1', type=float,
            dest='beta1', help='Adam: beta1 parameter (default %(default)s)',
            metavar='BETA1', default=BETA1)
    parser.add_argument('--beta2', type=float,
            dest='beta2', help='Adam: beta2 parameter (default %(default)s)',
            metavar='BETA2', default=BETA2)
    parser.add_argument('--eps', type=float,
            dest='epsilon', help='Adam: epsilon parameter (default %(default)s)',
            metavar='EPSILON', default=EPSILON)
    parser.add_argument('--initial',
            dest='initial', help='initial image',
            metavar='INITIAL')
    parser.add_argument('--initial-noiseblend', type=float,
            dest='initial_noiseblend',
            help='ratio of blending initial image with normalized noise '
                 '(if no initial image specified, content image is used) '
                 '(default %(default)s)',
            metavar='INITIAL_NOISEBLEND')
    parser.add_argument('--preserve-colors', action='store_true',
            dest='preserve_colors',
            help='style-only transfer (preserving colors) - if color transfer '
                 'is not needed')
    parser.add_argument('--pooling',
            dest='pooling',
            help='pooling layer configuration: max or avg (default %(default)s)',
            metavar='POOLING', default=POOLING)
    parser.add_argument('--overwrite', action='store_true', dest='overwrite',
            help='write file even if there is already a file with that name')
    return parser


def fmt_imsave(fmt, iteration):
    if re.match(r'^.*\{.*\}.*$', fmt):
        return fmt.format(iteration)
    elif '%' in fmt:
        return fmt % iteration
    else:
        raise ValueError("illegal format string '{}'".format(fmt))


def stylyze(options, callback):

    parser = build_parser()
    if options is None:
        key = 'TF_CPP_MIN_LOG_LEVEL'
        if key not in os.environ:
            os.environ[key] = '2'

        options = parser.parse_args()

    if not os.path.isfile(options.network):
        parser.error("Network %s does not exist. (Did you forget to "
                     "download it?)" % options.network)

    if [options.checkpoint_iterations,
        options.checkpoint_output].count(None) == 1:
        parser.error("use either both of checkpoint_output and "
                     "checkpoint_iterations or neither")

    if options.checkpoint_output is not None:
        if re.match(r'^.*(\{.*\}|%.*).*$', options.checkpoint_output) is None:
            parser.error("To save intermediate images, the checkpoint_output "
                         "parameter must contain placeholders (e.g. "
                         "`foo_{}.jpg` or `foo_%d.jpg`")

    content_image_arr = [imread(i) for i in options.content]
    style_images = [imread(style) for style in options.styles]

    width_arr = options.width
    for i in range(len(content_image_arr)):
        width = width_arr[i]
        content_image = content_image_arr[i]
        if width is not None:
            new_shape = (int(math.floor(float(content_image.shape[0]) /
                    content_image.shape[1] * width)), width)
            content_image = scipy.misc.imresize(content_image, new_shape)
            content_image_arr[i] = content_image
        target_shape = content_image.shape
        for j in range(len(style_images)):
            style_scale = STYLE_SCALE
            if options.style_scales is not None:
                style_scale = options.style_scales[j]
            style_images[j] = scipy.misc.imresize(style_images[j], style_scale *
                    target_shape[1] / style_images[j].shape[1])

    style_blend_weights = options.style_blend_weights
    if style_blend_weights is None:
        # default is equal weights
        style_blend_weights = [1.0/len(style_images) for _ in style_images]
    else:
        total_blend_weight = sum(style_blend_weights)
        style_blend_weights = [weight/total_blend_weight
                               for weight in style_blend_weights]

    initial_arr = content_image_arr

    # try saving a dummy image to the output path to make sure that it's writable
    output_arr = options.output
    for output in output_arr:
        if os.path.isfile(output) and not options.overwrite:
            raise IOError("%s already exists, will not replace it without "
                          "the '--overwrite' flag" % output)
        try:
            imsave(output, np.zeros((500, 500, 3)))
        except:
            raise IOError('%s is not writable or does not have a valid file '
                          'extension for an image file' % output)

    vgg_weights, vgg_mean_pixel = vgg.load_net(options.network)

    style_shapes = [(1,) + style.shape for style in style_images]
    content_features = {}
    style_features = [{} for _ in style_images]

    layer_weight = 1.0
    style_layers_weights = {}
    for style_layer in STYLE_LAYERS:
        style_layers_weights[style_layer] = layer_weight
        layer_weight *= options.style_layer_weight_exp

    # normalize style layer weights
    layer_weights_sum = 0
    for style_layer in STYLE_LAYERS:
        layer_weights_sum += style_layers_weights[style_layer]
    for style_layer in STYLE_LAYERS:
        style_layers_weights[style_layer] /= layer_weights_sum

    g = tf.Graph()

    # compute style features in feedforward mode
    for i in range(len(style_images)):
        g = tf.Graph()
        with g.as_default(), g.device('/cpu:0'), tf.Session() as sess:
            image = tf.placeholder('float', shape=style_shapes[i])
            net = vgg.net_preloaded(vgg_weights, image, options.pooling)
            style_pre = np.array([vgg.preprocess(style_images[i], vgg_mean_pixel)])
            for layer in STYLE_LAYERS:
                features = net[layer].eval(feed_dict={image: style_pre})
                features = np.reshape(features, (-1, features.shape[3]))
                gram = np.matmul(features.T, features) / features.size
                style_features[i][layer] = gram

    initial_content_noise_coeff = 1.0 - options.initial_noiseblend

    for i in range(len(content_image_arr)):
        Data.save_step(Data.get_step() + 1)
        loss_arrs = None
        for iteration, image, loss_vals in stylize(
            initial=initial_arr[i],
            content=content_image_arr[i],
            preserve_colors=options.preserve_colors,
            iterations=options.iterations,
            content_weight=options.content_weight,
            content_weight_blend=options.content_weight_blend,
            tv_weight=options.tv_weight,
            learning_rate=options.learning_rate,
            beta1=options.beta1,
            beta2=options.beta2,
            epsilon=options.epsilon,
            pooling=options.pooling,
            initial_content_noise_coeff=initial_content_noise_coeff,
            style_images=style_images,
            style_layers_weights=style_layers_weights,
            style_weight=options.style_weight,
            style_blend_weights=style_blend_weights,
            g=g,
            vgg_weights=vgg_weights,
            vgg_mean_pixel=vgg_mean_pixel,
            content_features=content_features,
            style_features=style_features,
            print_iterations=options.print_iterations,
            checkpoint_iterations=options.checkpoint_iterations,
            callback=callback
        ):
            if (image is not None) and (options.checkpoint_output is not None):
                imsave(fmt_imsave(options.checkpoint_output, iteration), image)
            if (loss_vals is not None) \
                    and (options.progress_plot or options.progress_write):
                if loss_arrs is None:
                    itr = []
                    loss_arrs = OrderedDict((key, []) for key in loss_vals.keys())
                for key,val in loss_vals.items():
                    loss_arrs[key].append(val)
                itr.append(iteration)


        imsave(options.output[i], image)

        if options.progress_write:
            fn = "{}/progress.txt".format(os.path.dirname(options.output[i]))
            tmp = np.empty((len(itr), len(loss_arrs)+1), dtype=float)
            tmp[:,0] = np.array(itr)
            for ii,val in enumerate(loss_arrs.values()):
                tmp[:,ii+1] = np.array(val)
            np.savetxt(fn, tmp, header=' '.join(['itr'] + list(loss_arrs.keys())))


        if options.progress_plot:
            import matplotlib
            matplotlib.use('Agg')
            from matplotlib import pyplot as plt
            fig,ax = plt.subplots()
            for key, val in loss_arrs.items():
                ax.semilogy(itr, val, label=key)
            ax.legend()
            ax.set_xlabel("iterations")
            ax.set_ylabel("loss")
            fig.savefig("{}/progress.png".format(os.path.dirname(options.output[i])))


def imread(path):
    img = scipy.misc.imread(path).astype(np.float)
    if len(img.shape) == 2:
        # grayscale
        img = np.dstack((img,img,img))
    elif img.shape[2] == 4:
        # PNG with alpha channel
        img = img[:,:,:3]
    return img


def imsave(path, img):
    img = np.clip(img, 0, 255).astype(np.uint8)
    Image.fromarray(img).save(path, quality=95)


if __name__ == '__main__':
    raise Exception("Running from terminal not acceptable")
