import os

from PIL import Image

import Data
import neural_style as Stylist


class ImageManager:
    original_name = ""
    style_path = ""
    work_folder_path = ""
    original_path = ""
    folder_name = ""
    save_path = ""
    split_num_vertical = 0
    split_num_horizontal = 0
    iterations = 0
    crop_delta = 50
    alpha_delta = 50

    def __init__(self, original_path, style_path, split_num_vertical, split_num_horizontal,
                 iterations):
        self.work_folder_path = "Cash"
        dir = os.path.join(self.work_folder_path)
        if not os.path.exists(dir):
            os.mkdir(dir)
        self.original_path = original_path
        self.original_name = str(original_path).split('/')[-1]
        self.style_path = style_path
        self.split_num_vertical = split_num_vertical
        self.split_num_horizontal = split_num_horizontal
        self.iterations = iterations
        self.folder_name = self.original_name.split(".")[0]
        dir = os.path.join(self.work_folder_path, self.folder_name)
        if not os.path.exists(dir):
            os.mkdir(dir)
        self.save_path = self.work_folder_path + "/" + self.folder_name + "/"

    def start(self):
        self.cut_vertical()
        self.cut_horizontal()
        for i in range(0, self.split_num_vertical):
            for j in range(0, self.split_num_horizontal):
                Data.save_step(Data.get_step() + 1)
                Data.save_iteration(1)
                Data.save_log("...")
                self.render(self.save_path + self.folder_name + "-" + str(i) + "/" + self.folder_name + "-" + str(
                    i) + "_" + str(j) + ".png")
        self.add_alpha_horizontal()
        self.concut_horizontal()
        self.add_alpha_vertical()
        self.concut_vertical()

    def render(self, path):
        options = type('Anonymous options', (object,), {
            "content": path,
            "styles": [self.style_path],
            "output": path,
            "iterations": self.iterations,
            "overwrite": True,

            "network": 'imagenet-vgg-verydeep-19.mat',
            "checkpoint_iterations": None,
            "checkpoint_output": None,
            "width": None,
            "style_scales": None,
            "style_blend_weights": None,
            "initial": None,
            "initial_noiseblend": 0,
            "preserve_colors": None,
            "content_weight": 5e0,
            "content_weight_blend": 1,
            "style_weight": 5e2,
            "style_layer_weight_exp": 1,
            "tv_weight": 1e2,
            "learning_rate": 1e1,
            "beta1": 0.9,
            "beta2": 0.999,
            "epsilon": 1e-08,
            "pooling": 'max',
            "print_iterations": None,
            "progress_plot": None,
            "progress_write": None,
        })()
        Stylist.stylyze(options)

    def cut_vertical(self):
        original = Image.open(self.original_path)
        original = original.convert("RGBA")
        width, height = original.size
        split_dist = width / self.split_num_vertical
        for i in range(0, self.split_num_vertical):
            x = split_dist * i
            y = 0
            w = split_dist + x
            h = height + y
            cut_image = self.crop_vertical(original, x, y, w, h)
            cut_image.save(self.save_path + self.folder_name + "-" + str(i) + ".png", "PNG")

    def crop_vertical(self, image, x, y, w, h):
        delta = self.crop_delta
        x -= delta
        w += delta
        if (x < 0): x = 0
        image_width = image.size[0]
        if (w > image_width): w = image_width
        return image.crop((x, y, w, h))

    def cut_horizontal(self):
        for i in range(0, self.split_num_vertical):
            original = Image.open(self.save_path + self.folder_name + "-" + str(i) + ".png")
            original = original.convert("RGBA")
            width, height = original.size
            split_dist = height / self.split_num_horizontal

            dir = os.path.join(self.save_path, self.folder_name + "-" + str(i))
            if not os.path.exists(dir):
                os.mkdir(dir)

            for j in range(0, self.split_num_horizontal):
                x = 0
                y = split_dist * j
                w = width + x
                h = split_dist + y
                cut_image = self.crop_horizontal(original, x, y, w, h)
                cut_image.save(dir + "/" + self.folder_name + "-" + str(i) + "_" + str(j) + ".png", "PNG")

    def crop_horizontal(self, image, x, y, w, h):
        delta = self.crop_delta
        y -= delta
        h += delta
        if (y < 0): y = 0
        image_height = image.size[1]
        if (h > image_height): h = image_height
        return image.crop((x, y, w, h))

    def concut_vertical(self):
        images = []
        width = 0
        height = 0
        for i in range(0, self.split_num_vertical):
            images.append(Image.open(self.save_path + self.folder_name + "-" + str(i) + ".png"))
            if i == 0:
                width += images[i].size[0] - self.crop_delta
            elif i == self.split_num_vertical - 1:
                width += images[i].size[0] - self.crop_delta
            else:
                width += images[i].size[0] - 2 * self.crop_delta
        height += images[0].size[1]
        result_image = Image.new('RGBA', (width, height))

        x = 0
        for i in range(0, self.split_num_vertical):
            if i == 0:
                result_image.paste(images[i], (x, 0))
                x += images[i].size[0] - self.crop_delta
            elif i == self.split_num_vertical - 1:
                result_image.paste(images[i], (x - self.crop_delta, 0), images[i])
                x += images[i].size[0] - self.crop_delta
            else:
                result_image.paste(images[i], (x - self.crop_delta, 0), images[i])
                x += images[i].size[0] - 2 * self.crop_delta
        result_image.putalpha(255)
        result_image.save(self.save_path + "result.png", "PNG")

    def concut_horizontal(self):
        for i in range(0, self.split_num_vertical):
            images = []
            width = 0
            height = 0
            for j in range(0, self.split_num_horizontal):
                images.append(
                    Image.open(self.save_path + self.folder_name + "-" + str(i) + "/" + self.folder_name + "-" + str(
                        i) + "_" + str(j) + ".png"))
                if j == 0:
                    height += images[j].size[1] - self.crop_delta
                elif j == self.split_num_vertical - 1:
                    height += images[j].size[1] - self.crop_delta
                else:
                    height += images[j].size[1] - 2 * self.crop_delta
            width += images[0].size[0]
            result_image = Image.new('RGBA', (width, height))

            y = 0
            for j in range(0, self.split_num_horizontal):
                if j == 0:
                    result_image.paste(images[j], (0, y))
                    y += images[j].size[1] - self.crop_delta
                elif j == self.split_num_horizontal - 1:
                    result_image.paste(images[j], (0, y - self.crop_delta), images[j])
                    y += images[j].size[1] - self.crop_delta
                else:
                    result_image.paste(images[j], (0, y - self.crop_delta), images[j])
                    y += images[j].size[1] - 2 * self.crop_delta
            result_image.putalpha(255)
            result_image.save(self.save_path + self.folder_name + "-" + str(i) + ".png", "PNG")

    def add_alpha_vertical(self):
        delta = self.alpha_delta
        for i in range(0, self.split_num_vertical):
            image = Image.open(self.save_path + self.folder_name + "-" + str(i) + ".png")
            image = image.convert("RGBA")
            if (i == 0):
                image = self.add_alpha_right(image, delta)
            elif (i == self.split_num_vertical - 1):
                image = self.add_alpha_left(image, delta)
            else:
                image = self.add_alpha_right(image, delta)
                image = self.add_alpha_left(image, delta)
            image.save(self.save_path + self.folder_name + "-" + str(i) + ".png", "PNG")

    def add_alpha_right(self, image, delta):
        width, height = image.size
        for x in range(width - delta, width):
            alpha = int((width - x) / delta * 255)
            for y in range(height):
                pixel = image.getpixel((x, y))
                image.putpixel((x, y), (pixel[0], pixel[1], pixel[2], alpha))
        return image

    def add_alpha_left(self, image, delta):
        width, height = image.size
        for x in range(delta):
            alpha = int(x / delta * 255)
            for y in range(height):
                pixel = image.getpixel((x, y))
                image.putpixel((x, y), (pixel[0], pixel[1], pixel[2], alpha))
        return image

    def add_alpha_horizontal(self):
        delta = self.alpha_delta
        for i in range(0, self.split_num_vertical):
            for j in range(0, self.split_num_horizontal):
                image = Image.open(
                    self.save_path + self.folder_name + "-" + str(i) + "/" + self.folder_name + "-" + str(
                        i) + "_" + str(j) + ".png")
                image = image.convert("RGBA")
                if (j == 0):
                    image = self.add_alpha_down(image, delta)
                elif (j == self.split_num_horizontal - 1):
                    image = self.add_alpha_up(image, delta)
                else:
                    image = self.add_alpha_down(image, delta)
                    image = self.add_alpha_up(image, delta)
                image.save(self.save_path + self.folder_name + "-" + str(i) + "/" + self.folder_name + "-" + str(
                    i) + "_" + str(j) + ".png", "PNG")

    def add_alpha_up(self, image, delta):
        width, height = image.size
        for y in range(delta):
            alpha = int(y / delta * 255)
            for x in range(width):
                pixel = image.getpixel((x, y))
                image.putpixel((x, y), (pixel[0], pixel[1], pixel[2], alpha))
        return image

    def add_alpha_down(self, image, delta):
        width, height = image.size
        for y in range(height - delta, height):
            alpha = int((height - y) / delta * 255)
            for x in range(width):
                pixel = image.getpixel((x, y))
                image.putpixel((x, y), (pixel[0], pixel[1], pixel[2], alpha))
        return image


if __name__ == '__main__':
    imageManager = ImageManager("examples/1-content.jpg", "examples/1-style.jpg", 4, 4, 10)
    imageManager.start()
