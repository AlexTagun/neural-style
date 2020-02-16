import PySimpleGUI as sg
from ImageManager import ImageManager
from threading import Thread
import time
import Data
from Data import UserData


class Bar(Thread):
    def __init__(self, bar):
        Thread.__init__(self)
        self.name = "Loader"
        self.bar = bar
        self.is_running = False

    def run(self):
        self.is_running = True
        while self.is_running:
            value = Data.get_bar_value()
            self.bar.update_bar(value)
            print(value)
            time.sleep(1)

    def stop(self):
        self.is_running = False


class ImageRenderer(Thread):
    def __init__(self, original_path, style_path, split_num_vertical, split_num_horizontal,
                 iterations):
        Thread.__init__(self)
        self.name = "ImageRenderer"
        self.imageManager = ImageManager(original_path, style_path, split_num_vertical, split_num_horizontal,
                                         iterations)

    def run(self):
        self.imageManager.start()


# image_path = ""
# style_path = ""
# ver_split = ""
# hor_split = ""
# iterations = ""
user_data = Data.get_user_data()
image_path = user_data.image_path
style_path = user_data.style_path
ver_split = user_data.ver_split
hor_split = user_data.hor_split
iterations = user_data.iterations

sg.theme('Light Blue 2')

layout = [[sg.Text('А?')],
          [sg.Text('image path', size=(10, 1)), sg.Input(image_path), sg.FileBrowse()],
          [sg.Text('style path', size=(10, 1)), sg.Input(style_path), sg.FileBrowse()],
          [sg.Text('ver_split', size=(10, 1)), sg.InputText(ver_split)],
          [sg.Text('hor_split', size=(10, 1)), sg.InputText(hor_split)],
          [sg.Text('iterations', size=(10, 1)), sg.InputText(iterations)],
          [sg.ProgressBar(10, orientation='h', size=(20, 20), key='progbar')],
          [sg.Button('Render', focus=True)]]

window = sg.Window('Стилизатор 30000', layout)
bar = Bar(window['progbar'])

if __name__ == "__main__":
    Data.save_bar_state(0)
    while True:
        event, values = window.read(timeout=10)
        if event in (None, 'Quit'):
            bar.stop()
            break
        elif event == 'Render':
            Data.save_user_data(values[0], values[1], values[2], values[3], values[4])
            imageRenderer = ImageRenderer(str(values[0]), str(values[1]),
                                          int(values[2]), int(values[3]), int(values[4]))

            bar.start()
            imageRenderer.start()

        # All done!
        # sg.popup_ok('Done')
