from .base import Source, LynerException
from .utility import parse_image

################################################################################
### TextSource
################################################################################

class TextSource(Source):

    def __init__(self, puzzle=None):
        self.puzzle = puzzle

    def get_puzzle(self):
        return self.puzzle

################################################################################
### ImageSource
################################################################################

class ImageSource(Source):

    def __init__(self, image=None):
        self.image = image

    def get_puzzle(self):
        if self.image is None:
            raise LynerException('No image has been provided')
        return parse_image(self.image)
