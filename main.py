import PySimpleGUI as sg
from ImageManager import ImageManager
from threading import Thread
import time
import Data
from Data import UserData


class Bar(Thread):
    def __init__(self, bar, log_text, max_iterations, max_step):
        Thread.__init__(self)
        self.name = "Loader"
        self.bar = bar
        self.log_text = log_text
        self.is_running = False
        self.max_iterations = max_iterations
        self.max_step = max_step
        print(max_step)
        print(max_iterations)

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

layout = [
    [sg.Text('image path', size=(10, 1)), sg.Input(image_path), sg.FileBrowse()],
    [sg.Text('style path', size=(10, 1)), sg.Input(style_path), sg.FileBrowse()],
    [sg.Text('ver_split', size=(10, 1)), sg.InputText(ver_split)],
    [sg.Text('hor_split', size=(10, 1)), sg.InputText(hor_split)],
    [sg.Text('iterations', size=(10, 1)), sg.InputText(iterations)],
    [sg.ProgressBar(1000, orientation='h', size=(20, 20), key='progbar')],
    [sg.Text('...', size=(45, 1), justification='center', key='log')],
    [sg.Button('Render', focus=True)]]

window = sg.Window('Стилизатор 30000', layout)

if __name__ == "__main__":
    # bar = None
    while True:
        event, values = window.read(timeout=10)
        if event in (None, 'Quit'):
            bar.stop()
            break
        elif event == 'Render':
            Data.save_user_data(values[0], values[1], values[2], values[3], values[4])
            # print(int(values[2]) * int(values[3]) * int(values[4]))
            bar = Bar(window['progbar'], window['log'], int(values[4]),
                      int(values[2]) * int(values[3]))
            imageRenderer = ImageRenderer(bar, str(values[0]), str(values[1]),
                                          int(values[2]), int(values[3]), int(values[4]))

            Data.save_iteration(0)
            Data.save_step(0)
            Data.save_log("...")

            bar.start()
            imageRenderer.start()

        # All done!
        # sg.popup_ok('Done')
