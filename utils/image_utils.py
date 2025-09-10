# utils/image_utils.py
from PIL import Image, ImageDraw
import tkinter as tk
import io

def create_rounded_image(image, size=(186, 186), corner_radius=10):
    """Создаёт скруглённое изображение заданного размера."""
    if image is None:
        return None

    # Изменяем размер с сохранением пропорций
    image.thumbnail(size, Image.Resampling.LANCZOS)
    new_image = Image.new("RGBA", size, (0, 0, 0, 0))
    paste_x = (size[0] - image.width) // 2
    paste_y = (size[1] - image.height) // 2
    new_image.paste(image.convert("RGBA"), (paste_x, paste_y))

    # Создаём маску со скруглёнными углами
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size[0], size[1]], corner_radius, fill=255)

    # Применяем маску
    result = Image.new('RGBA', size, (0, 0, 0, 0))
    result.paste(new_image, (0, 0), mask)

    return result

def pil_to_photoimage(pil_image):
    """Конвертирует PIL.Image в PhotoImage для Tkinter."""
    if pil_image is None:
        return None
    with io.BytesIO() as output:
        pil_image.save(output, format="PNG")
        data = output.getvalue()
    return tk.PhotoImage(data=data)