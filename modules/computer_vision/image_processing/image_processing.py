import numpy as np
import cv2

class Image_processing():
    # def change_contrast_brightness(self, frame, contrast_value, brightness_value):
    #     factor = (259 * (contrast_value + 255)) / (255 * (259 - contrast_value))
    #     adjusted = cv2.convertScaleAbs(frame, alpha=factor, beta=brightness_value)
    #     return adjusted

    def change_contrast_brightness(self, input_img, contrast, brightness):

        if brightness != 0:
            if brightness > 0:
                shadow = brightness
                highlight = 255
            else:
                shadow = 0
                highlight = 255 + brightness
            alpha_b = (highlight - shadow)/255
            gamma_b = shadow
            
            buf = cv2.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
        else:
            buf = input_img.copy()
        
        if contrast != 0:
            f = 131*(contrast + 127)/(127*(131-contrast))
            alpha_c = f
            gamma_c = 127*(1-f)
            
            buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)

        return buf
    
    def negative(self, input_img):
        return cv2.bitwise_not(input_img)