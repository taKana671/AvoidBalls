from enum import Enum, auto

import pandas as pd
import numpy as np
import cv2

from panda3d.core import Point2, Vec2


DIR = 'terrains/heightfield_texts'
IMG_DIR = 'terrains'


class Images(Enum):

    TOP_LEFT = auto()
    TOP_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_RIGHT = auto()

    @property
    def file_path(self):
        name = self.name.lower()
        return f'{IMG_DIR}/{name}.png'


class Tile:
    """
    Args
        center (Point2)
    """

    def __init__(self, image, center, size=256):
        self.image = image
        self.center = center
        self.origin = center - Vec2(128, 128)
        self.size = size

    def convert_pixel_coords(self, start=138, end=150):
        img = cv2.imread(self.image.file_path)
        # pixel_coords = set((x, y) for x, y, _ in zip(*np.where(img == 160)))
        pixel_coords = set((x, y) for x, y, _ in zip(*np.where((img > start) & (img < end))))
        # print('pixel_coords', pixel_coords)

        for px, py in pixel_coords:
            print('pixel coords', px, py)
            x = py - 128

            if 0 <= px <= 128:
                y = 128 - px
            else:
                y = -(px - 128)

            yield (x, y)


class HeightfieldTiles:

    def __init__(self):
        self._tiles = [
            Tile(Images.TOP_LEFT, Vec2(-128, 128)),
            Tile(Images.TOP_RIGHT, Vec2(128, 128)),
            Tile(Images.BOTTOM_LEFT, Vec2(-128, -128)),
            Tile(Images.BOTTOM_RIGHT, Vec2(128, -128))
        ]

        self.tile_size = 256
        self.dir = 'terrains'
        # self.file = altitude_file_path

    def __iter__(self):
        yield from self._tiles
        # for tile in self._tiles:
        #     yield tile

    def find_size(self, current, size=1):
        size *= 2
        if size >= current:
            return size + 1
        return self.find_size(current, size)

    def enlarge(self, arr, edge=-1, mirror=False):
        bottom = np.flipud(arr[edge:, :]) if mirror else arr[edge:, :]
        arr = np.concatenate([arr, bottom], 0)
        right = np.fliplr(arr[:, edge:]) if mirror else arr[:, edge:]
        arr = np.concatenate([arr, right], 1)
        return arr

    def crop(self, img, h=257, w=257):
        """Crop a image to 257 * 257 area by default from the top left
           so that one row of pixels in the middle will always overlap.
           Args:
            img (numpy.ndarray): heightfield
        """
        top_l = img[:h, :w]
        top_r = img[:h, w - 1:w * 2 - 1]
        bottom_l = img[h - 1:h * 2 - 1, :w]
        bottom_r = img[h - 1:h * 2 - 1, w - 1:w * 2 - 1]

        cv2.imwrite(Images.TOP_LEFT.file_path, top_l)
        cv2.imwrite(Images.TOP_RIGHT.file_path, top_r)
        cv2.imwrite(Images.BOTTOM_LEFT.file_path, bottom_l)
        cv2.imwrite(Images.BOTTOM_RIGHT.file_path, bottom_r)

    def get_array(self, path):
        df = pd.read_csv(path, header=None).replace('e', 0)
        return df.values

    def make_heightfield_images(self, arr):
        arr = np.interp(arr, (arr.min(), arr.max()), (0, 256 * 256))
        arr = self.enlarge(arr)
        img = arr.astype(np.uint16)
        # import pdb; pdb.set_trace()
        cv2.imwrite('terrains/heightfield.png', img)
        self.crop(img)

    def concat_from_files(self, file_list):
        arr = np.concatenate(
            [np.concatenate([self.get_array(f'{DIR}/{file}') for file in files], 1) for files in file_list], 0
        )
        self.make_heightfield_images(arr)

    def concat_from_url(self, z, x, y):
        url = 'https://cyberjapandata.gsi.go.jp/xyz/dem/{}/{}/{}.txt'

        li = [
            [[x, y], [x + 1, y]],
            [[x, y + 1], [x + 1, y + 1]]
        ]
        arr = np.concatenate(
            [np.concatenate([self.get_array(url.format(z, x, y)) for x, y in sub], 1) for sub in li], 0
        )
        self.make_heightfield_images(arr)

    def mirror(self, file):
        top_l = self.get_array(f'{DIR}/{file}')
        top_r = np.fliplr(top_l)
        top = np.concatenate([top_l, top_r], 1)
        bottom = np.flipud(top)
        arr = np.concatenate([top, bottom], 0)
        self.make_heightfield_images(arr)

    # def convert_pixel_coords(self, file_path, start=138, end=150):
    #     img = cv2.imread(file_path)
    #     # pixel_coords = set((x, y) for x, y, _ in zip(*np.where(img == 160)))
    #     pixel_coords = set((x, y) for x, y, _ in zip(*np.where((img > start) & (img < end))))
    #     # print('pixel_coords', pixel_coords)

    #     for px, py in pixel_coords:
    #         print('pixel coords', px, py)
    #         x = py - 128

    #         if 0 <= px <= 128:
    #             y = 128 - px
    #         else:
    #             y = -(px - 128)

    #         yield (x, y)



if __name__ == '__main__':
    # Heightfield('terrains/heightfield_texts/14516_6445.txt').make_image()
    # Heightfield('terrains/heightfield_texts/14516_6445.txt').make_img2()

    li = [
        ['14517_6447.txt', '14518_6447.txt'],
        ['14517_6448.txt', '14518_6448.txt'],
    ]

    HeightfieldTiles().concat_from_files(li)
    # Heightfield().mirror_image('14515_6445.txt')

    # Heightfield().concat_from_url(14, 14525, 6396)