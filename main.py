import ctypes
import math
import threading
from threading import Thread

import PIL
import PySimpleGUI as sg
from PIL import Image

import Data
from ImageManager import ImageManager

MAX_RENDER_OUT_SIDE = 800


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
                 iterations, out_width, callback):
        Thread.__init__(self)
        self.name = "ImageRenderer"
        self.imageManager = ImageManager(
            original_path,
            style_path,
            vertical_pieces_count,
            horizontal_pieces_count,
            iterations,
            out_width,
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
    out_h = out_width * ratio
    return math.ceil(out_w / MAX_RENDER_OUT_SIDE), math.ceil(out_h / MAX_RENDER_OUT_SIDE)



user_data = Data.get_user_data()

image_path = user_data.image_path
style_path = user_data.style_path
out_width = user_data.width
iterations = user_data.iterations

sg.theme('Light Blue 2')

layout = [
    [sg.Text('image path', size=(10, 1)), sg.Input(image_path, key='image_path'), sg.FileBrowse()],
    [sg.Text('style path', size=(10, 1)), sg.Input(style_path, key='style_path'), sg.FileBrowse()],
    [sg.Text('width', size=(10, 1)), sg.InputText(out_width, key='width')],
    [sg.Text('iterations', size=(10, 1)), sg.InputText(iterations, key='iterations')],
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
            out_width = int(out_width_str)
            iterations = int(iterations_str)

            Data.save_user_data(image_path, style_path, out_width, iterations)

            image_w, image_h = image.size
            vertical_pieces_count, horizontal_pieces_count = count_splits(image_w, image_h, out_width)

            progress = Progress(window['progbar'], window['log'], iterations, vertical_pieces_count * horizontal_pieces_count)
            imageRenderer = ImageRendererThread(
                image_path,
                style_path,
                vertical_pieces_count,
                horizontal_pieces_count,
                iterations,
                out_width,
                progress.update
            )

            Data.save_step(0)

            imageRenderer.start()
