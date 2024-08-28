"""
This is a simple script used to generate the image of tiles with different number
"""

from PIL import Image, ImageDraw, ImageFont

white_tile_img = Image.open("./assets/white_tile.png")
black_tile_img = Image.open("./assets/black_tile.png")

for tile_color in ("white_tile", "black_tile"):
    if tile_color == "white_tile":
        fill_color = (0, 0, 0)
        image = white_tile_img
    else:
        fill_color = (255, 255, 255)
        image = black_tile_img

    for tile_number in range(0, 10):
        temp_image = image.copy()
        draw = ImageDraw.Draw(temp_image)
        text = str(tile_number)
        font = ImageFont.truetype("segoeui.ttf", size=120)
        x0, y0, x1, y1 = draw.textbbox(xy=[0, 0], text=text, font=font)
        text_width = x1 - x0
        text_height = y1 - y0
        image_width, image_height = temp_image.size
        text_position = (
            (image_width - text_width) // 2,
            ((image_height - text_height) // 2) - 45,
        )
        draw.text(text_position, text, font=font, fill=fill_color)
        temp_image.save("./assets/" + tile_color + "_" + str(tile_number) + ".png")

    for tile_number in range(10, 12):
        temp_image = image.copy()
        draw = ImageDraw.Draw(temp_image)
        text = str(tile_number)
        font = ImageFont.truetype("segoeui.ttf", size=100)
        x0, y0, x1, y1 = draw.textbbox(xy=[0, 0], text=text, font=font)
        text_width = x1 - x0
        text_height = y1 - y0
        image_width, image_height = temp_image.size
        text_position = (
            (image_width - text_width) // 2,
            ((image_height - text_height) // 2) - 35,
        )
        draw.text(text_position, text, font=font, fill=fill_color)
        temp_image.save("./assets/" + tile_color + "_" + str(tile_number) + ".png")
