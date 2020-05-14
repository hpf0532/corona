# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/5/14 下午4:08
# File: capcha_code.py
# IDE: PyCharm

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random


def check_code(width=180, height=40, char_length=4, font_file='backend/static/font/kumo.ttf', font_size=35):
    code = []
    img = Image.new(mode='RGB', size=(width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img, mode='RGB')

    def rndChar():
        """
        生成随机字母数字
        :return:
        """
        tmp_list = []
        for i in range(4):
            u = chr(random.randint(65, 90))  # 大写字母
            l = chr(random.randint(97, 122))  # 小写字母
            n = str(random.randint(0, 9))  # 数字

            tmp = random.choice([u, l, n])
            tmp_list.append(tmp)

        return random.choice(tmp_list)

    def rndColor():
        """
        生成随机颜色
        :return:
        """
        return (random.randint(0, 255), random.randint(10, 255), random.randint(64, 255))

    # 写文字
    font = ImageFont.truetype(font_file, font_size)
    for i in range(char_length):
        char = rndChar()
        code.append(char)
        h = random.randint(0, 4)
        draw.text([i * width / char_length, h], char, font=font, fill=rndColor())

    # 写干扰点
    for i in range(40):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=rndColor())

    # 写干扰圆圈
    for i in range(40):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=rndColor())
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.arc((x, y, x + 4, y + 4), 0, 90, fill=rndColor())

    # 画干扰线
    for i in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)

        draw.line((x1, y1, x2, y2), fill=rndColor())

    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return img, ''.join(code)


if __name__ == '__main__':
    image_object, code = check_code()

    # 把图片写入文件
    print(code)

    with open('code.png', 'wb') as f:
        image_object.save(f, format='png')
