import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd = 'C:\Program Files\Tesseract-OCR/tesseract.exe'


def ocr_core(img):
    
    text = pytesseract.image_to_string(img)
    return text



# get grayscale
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


# noise removal
def remove_noise(image):
    return cv2.medianBlur(image,5)

# thresholding 
def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

def tes_global(img):
    img = get_grayscale(img)
    img = thresholding(img)
    img = remove_noise(img)

    return ocr_core(img)