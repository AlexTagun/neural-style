from PIL import Image
import os


class ImageManager:
    original_name = ""
    style_name = ""
    work_folder_path = ""
    folder_name = ""
    save_path = ""
    num_of_split = 0
    iterations = 0
    crop_delta = 50
    alpha_delta = 50

    def __init__(self, work_folder_path, original_name, style_name, num_of_split, iterations):
        self.work_folder_path = work_folder_path
        self.original_name = original_name
        self.style_name = style_name
        self.num_of_split = num_of_split
        self.iterations = iterations
        self.folder_name = self.original_name.split(".")[0]
        dir = os.path.join(self.work_folder_path, self.folder_name)
        if not os.path.exists(dir):
            os.mkdir(dir)
        self.save_path = self.work_folder_path + "/" + self.folder_name + "/"

    def start(self):
        self.cut()
        for i in range(0, self.num_of_split):
            self.render(self.save_path + self.folder_name + "-" + str(i) + ".png")
        self.add_alpha()
        self.concut()


    def render(self, path):
        cmd = ""
        cmd += "python neural_style.py"
        cmd += " --content " + path
        cmd += " --styles " + self.work_folder_path + "/" + self.style_name
        cmd += " --output " + path
        cmd += " --iterations " + str(self.iterations)
        cmd += " --overwrite"
        print(cmd)
        os.system(cmd)

    def cut(self):

        original = Image.open(self.work_folder_path + "/" + self.original_name)
        original = original.convert("RGBA")
        width, height = original.size
        split_dist = width / self.num_of_split
        for i in range(0, self.num_of_split):
            x = split_dist * i
            y = 0
            w = split_dist + x
            h = height + y
            cut_image = self.crop(original, x, y, w, h)
            cut_image.save(self.save_path + self.folder_name + "-" + str(i) + ".png", "PNG")

    def concut(self):
        images = []
        width = 0
        height = 0
        for i in range(0, self.num_of_split):
            images.append(Image.open(self.save_path + self.folder_name + "-" + str(i) + ".png"))
            if i == 0:
                width += images[i].size[0] - self.crop_delta
            elif i == self.num_of_split - 1:
                width += images[i].size[0] - self.crop_delta
            else:
                width += images[i].size[0] - 2 * self.crop_delta
        height += images[0].size[1]
        result_image = Image.new('RGBA', (width, height))

        x = 0
        for i in range(0, self.num_of_split):
            if i == 0:
                result_image.paste(images[i], (x, 0))
                x += images[i].size[0] - self.crop_delta
            elif i == self.num_of_split - 1:
                result_image.paste(images[i], (x - self.crop_delta, 0), images[i])
                x += images[i].size[0] - self.crop_delta
            else:
                result_image.paste(images[i], (x - self.crop_delta, 0), images[i])
                x += images[i].size[0] - 2 * self.crop_delta
            # result_image.paste(images[i], (x, 0))
            # x += images[i].size[0]
        result_image.putalpha(255)
        result_image.save(self.save_path + "result.png", "PNG")

    def crop(self, image, x, y, w, h):
        delta = self.crop_delta
        x -= delta
        w += delta
        if (x < 0): x = 0
        image_width = image.size[0]
        if (w > image_width): w = image_width
        return image.crop((x, y, w, h))

    def add_alpha(self):
        delta = self.alpha_delta
        for i in range(0, self.num_of_split):
            image = Image.open(self.save_path + self.folder_name + "-" + str(i) + ".png")
            image = image.convert("RGBA")
            if (i == 0):
                image = self.add_alpha_right(image, delta)
            elif (i == self.num_of_split - 1):
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


if __name__ == '__main__':
    imageManager = ImageManager("examples", "1-content.jpg", "1-style.jpg", 4, 300)
    imageManager.start()
    # imageManager.concut()
    # imageManager.cut()
    # imageManager.add_alpha()

    # os.system(
    #     "python neural_style.py --content examples/1-content/1-content-3.png --styles examples/1-style.jpg --output examples/1-content/1-content-3.png --iterations 1 --overwrite")
    # print("end")
