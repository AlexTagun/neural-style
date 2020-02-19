import math
import time
from threading import Thread

import PIL
import PySimpleGUI as sg
from PIL import Image

import Data
from ImageManager import ImageManager

MAX_RENDER_OUT_SIDE = 1280


class Bar(Thread):
    def __init__(self, bar, log_text, max_iterations, max_step):
        Thread.__init__(self)
        self.name = "Loader"
        self.bar = bar
        self.log_text = log_text
        self.is_running = False
        self.max_iterations = max_iterations
        self.max_step = max_step
        print('Max step: ' + str(max_step))
        print('Max iterations: ' + str(max_iterations))

    def run(self):
        self.is_running = True
        while self.is_running:
            value = int(((Data.get_step() - 1) * self.max_iterations + Data.get_iteration()) * 1000 / (
                self.max_iterations * self.max_step))
            self.bar.update_bar(value)
            # print(str(Data.get_log()))
            log = "..."
            try:
                log = "Step " + str(Data.get_step()) + "/" + str(self.max_step) + " " + Data.get_log()
                print(log)
            except:
                log = "..."
            self.log_text.update(log)
            time.sleep(1)

    def stop(self):
        self.is_running = False


class ImageRenderer(Thread):
    def __init__(self, bar_thread, original_path, style_path, split_num_vertical, split_num_horizontal,
                 iterations):
        Thread.__init__(self)
        self.name = "ImageRenderer"
        self.imageManager = ImageManager(original_path, style_path, split_num_vertical, split_num_horizontal,
                                         iterations)
        self.bar_thread = bar_thread

    def run(self):
        self.imageManager.start()
        self.bar_thread.stop()


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
    [sg.Text('...', size=(45, 1), justification='center', key='log')],
    [sg.Button('Start', focus=True)]]

window = sg.Window('Стилизатор 30000', layout)

if __name__ == "__main__":
    bar = None
    while True:
        event, values = window.read(timeout=100)
        if event is None:
            if bar is not None:
                bar.stop()
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

            bar = Bar(window['progbar'], window['log'], iterations, vertical_pieces_count * horizontal_pieces_count)
            imageRenderer = ImageRenderer(
                bar,
                image_path,
                style_path,
                vertical_pieces_count,
                horizontal_pieces_count,
                iterations
            )

            Data.save_iteration(0)
            Data.save_step(0)
            Data.save_log("...")

            bar.start()
            imageRenderer.start()

        # sg.popup_ok('Done')
