import win32clipboard 
import time
import io
from PIL import Image, UnidentifiedImageError
from pillow_heif import register_heif_opener

register_heif_opener()

class Clipbaord:
    def __init__(self):
        self.PNG_FORMAT = win32clipboard.RegisterClipboardFormat("PNG")
    
    def __open_clipboard(self, retries: int = 10, delay: float = 0.05) -> bool:
        for _ in range(retries):
            try:
                win32clipboard.OpenClipboard()
                return True
            except:
                time.sleep(delay)
                continue

    def set_text(self, text: str) -> bool:
        if not self.__open_clipboard():
            return False
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()

    def set_image(self, data: bytes) -> bool:
        try:
            img = Image.open(io.BytesIO(data))
            img.load()
        except UnidentifiedImageError as e:
            raise ValueError("Corrupt image") from e

        has_alpha = "A" in img.getbands() or "transparency" in img.info
        if has_alpha:
            rgba = img.convert("RGBA")
            png_source = rgba
            rgb = Image.new("RGB", rgba.size, (255, 255, 255))
            rgb.paste(rgba, mask=rgba.getchannel("A"))
        else:
            rgb = img.convert("RGB")
            png_source = rgb

        bmp_buf = io.BytesIO()
        rgb.save(bmp_buf, format="BMP")
        dib_bytes = bmp_buf.getvalue()[14:] 

        png_buf = io.BytesIO()
        png_source.save(png_buf, format="PNG")
        png_bytes = png_buf.getvalue()

        if not self.__open_clipboard():
            return False
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dib_bytes)
            win32clipboard.SetClipboardData(self.PNG_FORMAT, png_bytes)
        finally:
            win32clipboard.CloseClipboard()
        