import PySimpleGUI as sg
from ImageManager import ImageManager

sg.theme('Light Blue 2')

layout = [[sg.Text('А?')],
          [sg.Text('image path', size=(10, 1)), sg.Input(), sg.FileBrowse()],
          [sg.Text('style path', size=(10, 1)), sg.Input(), sg.FileBrowse()],
          [sg.Text('num_of_split', size=(10, 1)), sg.InputText()],
          [sg.Text('iterations', size=(10, 1)), sg.InputText()],
          [sg.ProgressBar(1000, orientation='h', size=(20, 20), key='progbar')],
          [sg.Button('Render', focus=True)]]

window = sg.Window('Где пиво?', layout)

while True:
    event, values = window.read(timeout=10)
    if event in (None, 'Quit'):
        break
    elif event == 'Render':
        imageManager = ImageManager(str(values[0]).split('/')[-1], str(values[1]).split('/')[-1],
                                    int(values[2]), int(values[3]))
        imageManager.start()

        for i in range(1000):
            window['progbar'].update_bar(i + 1)

        # All done!
        # sg.popup_ok('Done')

