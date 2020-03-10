import ctypes
import math
import threading
from threading import Thread

import PIL
import PySimpleGUI as sg
from PIL import Image

import Data
from ImageManager import ImageManager

MAX_RENDER_OUT_SIDE = 400


class Progress:
    def __init__(self, bar, log_text, max_iterations, max_step):
        self.name = "Loader"
        self.bar = bar
        self.log_text = log_text
        self.is_running = False
        self.max_iterations = max_iterations
        self.max_step = max_step
        print('Max step: ' + str(max_step))
        print('Max iterations: ' + str(max_iterations))

    def update(self, iteration, log_text):
        value = int(((Data.get_step() - 1) * self.max_iterations + iteration) * 1000 / (
            self.max_iterations * self.max_step))
        self.bar.update_bar(value)
        log = "..."
        try:
            text = log_text.split('(')
            log = "Step " + str(Data.get_step()) + "/" + str(self.max_step) + " " + text[0] + "\n" + \
                  "(" + text[1]
            print(log)
        except:
            log = "..."
        self.log_text.update(log)

    def stop(self):
        self.is_running = False


class ImageRendererThread(Thread):
    def __init__(self, original_path, style_path, vertical_pieces_count, horizontal_pieces_count,
                 iterations, out_width, style_layer_weight_exp, content_weight_blend, callback):
        Thread.__init__(self)
        self.name = "ImageRenderer"
        self.imageManager = ImageManager(
            original_path,
            style_path,
            vertical_pieces_count,
            horizontal_pieces_count,
            iterations,
            out_width,
            style_layer_weight_exp,
            content_weight_blend,
            callback
        )

    def run(self):
        self.imageManager.start()

    def raise_exc(self, exception):
        assert self.isAlive(), "thread must be started"
        for tid, tobj in threading._active.items():
            if tobj is self:
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exception))
                if res == 0:
                    print("nonexistent thread id, trying x32 case")

                    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exception))
                    if res == 0:
                        print("still nonexistent thread id")
                    elif res > 1:
                        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
                        print("PyThreadState_SetAsyncExc failed")
                elif res > 1:
                    # """if it returns a number greater than one, you're in trouble,
                    # and you should call it again with exc=NULL to revert the effect"""
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), 0)
                    print("PyThreadState_SetAsyncExc failed")
                return

    def terminate(self):
        self.raise_exc(SystemExit)


def count_splits(orig_w, orig_h, out_w):
    ratio = orig_h / orig_w
    out_h = out_w * ratio
    scale_factor = out_w / orig_w
    max_side_with_delta = MAX_RENDER_OUT_SIDE

    first_h_count = math.ceil(out_w / max_side_with_delta)
    piece_content_w = orig_w / first_h_count
    ImageManager.crop_delta = math.ceil(piece_content_w / 6)

    print("Resulting crop delta: " + str(ImageManager.crop_delta))

    max_side_without_delta = MAX_RENDER_OUT_SIDE - ImageManager.crop_delta * scale_factor * 2

    print("Resulting max side including delta: " + str(max_side_without_delta))
    if max_side_without_delta <= 0:
        raise ValueError("Too big scale with too small max side")
    return math.ceil(out_w / max_side_without_delta), math.ceil(out_h / max_side_without_delta)


user_data = Data.get_user_data()

image_path = user_data.image_path
style_path = user_data.style_path
out_width = user_data.width
iterations = user_data.iterations
max_side = user_data.max_side
style_layer_weight_exp = user_data.style_layer_weight_exp
content_weight_blend = user_data.content_weight_blend

sg.theme('Light Blue 2')

layout = [
    [sg.Text('image path', size=(10, 1)), sg.Input(image_path, key='image_path'), sg.FileBrowse()],
    [sg.Text('style path', size=(10, 1)), sg.Input(style_path, key='style_path'), sg.FileBrowse()],
    [sg.Text('width', size=(10, 1)), sg.InputText(out_width, key='width')],
    [sg.Text('iterations', size=(10, 1)), sg.InputText(iterations, key='iterations')],
    [sg.Text('max side', size=(10, 1)), sg.InputText(max_side, key='max_side')],
    [sg.Text('style_layer_weight_exp', size=(10, 1)),
     sg.InputText(style_layer_weight_exp, key='style_layer_weight_exp')],
    [sg.Text('content_weight_blend', size=(10, 1)), sg.InputText(content_weight_blend, key='content_weight_blend')],
    [sg.ProgressBar(1000, orientation='h', size=(20, 20), key='progbar')],
    [sg.Text('...', size=(59, 2), justification='left', key='log')],
    [sg.Button('Start', focus=True)]]

window = sg.Window('Стилизатор 30000', layout)

if __name__ == "__main__":
    imageRenderer = None
    while True:
        event, values = window.read(timeout=100)
        if event is None:
            if imageRenderer is not None:
                imageRenderer.terminate()
            break
        elif event == 'Start':
            image_path = values['image_path']
            style_path = values['style_path']

            try:
                image = Image.open(image_path)
                style = Image.open(style_path)
            except FileNotFoundError as e:
                print('Image and style files should exist')
                continue
            except PIL.UnidentifiedImageError as e:
                print('Image and style should be images')
                continue

            out_width_str = values['width']
            iterations_str = values['iterations']
            max_side_str = values['max_side']
            out_width = int(out_width_str)
            iterations = int(iterations_str)
            max_side = int(max_side_str)
            style_layer_weight_exp = float(values['style_layer_weight_exp'])
            content_weight_blend = float(values['content_weight_blend'])

            Data.save_user_data(image_path, style_path, out_width, iterations, max_side, style_layer_weight_exp,
                                content_weight_blend)

            MAX_RENDER_OUT_SIDE = max_side

            image_w, image_h = image.size
            try:
                vertical_pieces_count, horizontal_pieces_count = count_splits(image_w, image_h, out_width)
            except ValueError as e:
                window['log'].update(e.args[0])
                continue

            progress = Progress(window['progbar'], window['log'], iterations,
                                vertical_pieces_count * horizontal_pieces_count)
            imageRenderer = ImageRendererThread(
                image_path,
                style_path,
                vertical_pieces_count,
                horizontal_pieces_count,
                iterations,
                out_width,
                style_layer_weight_exp,
                content_weight_blend,
                progress.update
            )

            Data.save_step(0)

            imageRenderer.start()
