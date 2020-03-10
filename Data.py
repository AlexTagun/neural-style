import os


class UserData:
    def __init__(self, image_path, style_path, width, iterations, max_side, style_layer_weight_exp,
                 content_weight_blend):
        self.image_path = image_path
        self.style_path = style_path
        self.width = width
        self.iterations = iterations
        self.max_side = max_side
        self.style_layer_weight_exp = style_layer_weight_exp
        self.content_weight_blend = content_weight_blend


def get_step():
    with open("step.txt", "r") as inp:
        for line in inp:
            return int(line)


def save_step(value):
    with open("step.txt", "w") as document1:
        document1.writelines(str(value))


def save_user_data(image_path, style_path, width, iterations, max_side, style_layer_weight_exp, content_weight_blend):
    with open("data.txt", "w") as document1:
        document1.writelines(image_path + '\n'
                             + style_path + '\n'
                             + str(width) + '\n'
                             + str(iterations) + '\n'
                             + str(max_side) + '\n'
                             + str(style_layer_weight_exp) + '\n'
                             + str(content_weight_blend) + '\n')


def get_user_data():
    path = os.path.join("data.txt")
    if not os.path.exists(path):
        image_path = ""
        style_path = ""
        width = "1280"
        iterations = "10"
        max_side = "400"
        style_layer_weight_exp = "1.0"
        content_weight_blend = "1.0"
        save_user_data(image_path, style_path, width, iterations, max_side, style_layer_weight_exp,
                       content_weight_blend)
    new_file_lines = []
    with open("data.txt", "r") as inp:
        for line in inp:
            line = line.split('\n')
            new_file_lines.append(line[0])
    return UserData(new_file_lines[0], new_file_lines[1], new_file_lines[2], new_file_lines[3], new_file_lines[4],
                    new_file_lines[5], new_file_lines[6])
