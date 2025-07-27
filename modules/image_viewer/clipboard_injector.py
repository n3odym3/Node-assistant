from PIL import Image
import io
import win32clipboard
import numpy as np

class ClipboardInjector:
    def send_image(self, image:np.ndarray)->None:
        """
        Sends an image to the clipboard.

        Parameters:
            image (numpy.ndarray): The image to be sent.
        """
        image_pil = Image.fromarray(image)
        output = io.BytesIO()
        image_pil.save(output, format='BMP')
        data = output.getvalue()[14:]
        output.close()
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()

    def send_text(self,data):
        """
        Set the text data to the clipboard.

        Parameters:
            data (str): The text data to be set to the clipboard.
        """
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(data)
        win32clipboard.CloseClipboard()
clipboardinjector = ClipboardInjector() 

