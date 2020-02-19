import os


class UserData:
    def __init__(self, image_path, style_path, width, iterations):
        self.image_path = image_path
        self.style_path = style_path
        self.width = width
        self.iterations = iterations


def get_iteration():
    with open("iteration.txt", "r") as inp:
        for line in inp:
            return int(line)


def save_iteration(value):
    with open("iteration.txt", "w") as document1:
        document1.writelines(str(value))


def get_step():
    with open("step.txt", "r") as inp:
        for line in inp:
            return int(line)


def save_log(value):
    with open("log.txt", "w") as document1:
        document1.writelines(str(value))


def get_log():
    with open("log.txt", "r") as inp:
        for line in inp:
            return line


def save_step(value):
    with open("step.txt", "w") as document1:
        document1.writelines(str(value))


def save_user_data(image_path, style_path, width, iterations):
    with open("data.txt", "w") as document1:
        document1.writelines(image_path + '\n'
                             + style_path + '\n'
                             + str(width) + '\n'
                             + str(iterations) + '\n')


def get_user_data():
    path = os.path.join("data.txt")
    if not os.path.exists(path):
        image_path = ""
        style_path = ""
        width = "1280"
        iterations = "10"
        save_user_data(image_path, style_path, width, iterations)
    new_file_lines = []
    with open("data.txt", "r") as inp:
        for line in inp:
            line = line.split('\n')
            new_file_lines.append(line[0])
    return UserData(new_file_lines[0], new_file_lines[1], new_file_lines[2], new_file_lines[3])
