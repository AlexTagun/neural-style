import os


class UserData:
    def __init__(self, image_path, style_path, ver_split, hor_split, iterations):
        self.image_path = image_path
        self.style_path = style_path
        self.ver_split = ver_split
        self.hor_split = hor_split
        self.iterations = iterations


def get_bar_value():
    with open("bar_state.txt", "r") as inp:
        new_file_lines = []
        for line in inp:
            return int(line)


def save_bar_state(value):
    with open("bar_state.txt", "w") as document1:
        document1.writelines(str(value))


def save_user_data(image_path, style_path, ver_split, hor_split, iterations):
    with open("data.txt", "w") as document1:
        document1.writelines(image_path + '\n'
                             + style_path + '\n'
                             + str(ver_split) + '\n'
                             + str(hor_split) + '\n'
                             + str(iterations) + '\n')


def get_user_data():
    path = os.path.join("data.txt")
    if not os.path.exists(path):
        image_path = "select file"
        style_path = "select file"
        ver_split = "1"
        hor_split = "1"
        iterations = "1"
        save_user_data(image_path, style_path, ver_split, hor_split, iterations)
        return get_user_data()
    new_file_lines = []
    # i = 0
    with open("data.txt", "r") as inp:
        for line in inp:
            # print(i)
            # print(line)
            # i += 1
            line = line.split('\n')
            new_file_lines.append(line[0])
    return UserData(new_file_lines[0], new_file_lines[1], new_file_lines[2], new_file_lines[3], new_file_lines[4])
