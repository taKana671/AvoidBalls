import itertools
from enum import Enum, auto

import pandas as pd
import numpy as np
import cv2

from panda3d.core import Point2, Vec2


TERRAIN_DIR = 'terrains'


class Areas(Enum):

    LOWLAND = auto()
    PLAIN = auto()
    MOUNTAIN = auto()
    SUBALPINE = auto()
    ALPINE = auto()


class Tile:
    """
    Args
        center (Point2)
    """

    def __init__(self, file, quadrant, size):
        self.file = file
        self.center = quadrant * (size / 2)
        self.quadrant = quadrant
        self.size = size

    def get_generators(self):
        img = cv2.imread(self.file)
        row, col, _ = img.shape

        yield self.generate(img, 50, Areas.LOWLAND)     # lowground zone
        yield self.generate(img, 90, Areas.PLAIN)       # plain
        yield self.generate(img, 130, Areas.MOUNTAIN)   # mountain zone
        yield self.generate(img, 160, Areas.SUBALPINE)  # subalpine zone
        yield self.generate(img, 200, Areas.ALPINE)     # alpine zone

    def generate(self, img, color, area):
        for x, y in set((x, y) for x, y, _ in zip(*np.where(img == color))):
            cx, cy = self.change_pixel_to_cartesian(x, y)
            yield cx, cy, area

    def count_pixels(self, start, end):
        img = cv2.imread(self.file)

        if start < 0:
            start = 0
        if end > 255:
            end = 255

        count = sum(np.count_nonzero(img == i) for i in range(start, end + 1))
        return count

    def change_pixel_to_cartesian(self, y, x):
        half = self.size / 2
        cx = x - half
        cy = -(y - half)
        cx += self.center.x
        cy += self.center.y
        return cx, cy


class HeightfieldTiles:

    def __init__(self):
        self.creator = HeightfieldCreator()

        self._tiles = [
            Tile(self.creator.top_left, Point2(-1, 1), self.creator.size),
            Tile(self.creator.top_right, Point2(1, 1), self.creator.size),
            Tile(self.creator.bottom_left, Point2(-1, -1), self.creator.size),
            Tile(self.creator.bottom_right, Point2(1, -1), self.creator.size)
        ]

    def __iter__(self):
        yield from self._tiles


class TileSizeError(Exception):
    """Raised when tile size is not (256, 256)
    """


class HeightfieldCreator:

    def __init__(self):
        self.size = 256
        self.top_left = f'{TERRAIN_DIR}/top_left.png'
        self.top_right = f'{TERRAIN_DIR}/top_right.png'
        self.bottom_left = f'{TERRAIN_DIR}/bottom_left.png'
        self.bottom_right = f'{TERRAIN_DIR}/bottom_right.png'

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

        cv2.imwrite(self.top_left, top_l)
        cv2.imwrite(self.top_right, top_r)
        cv2.imwrite(self.bottom_left, bottom_l)
        cv2.imwrite(self.bottom_right, bottom_r)

    def get_array(self, path):
        df = pd.read_csv(path, header=None).replace('e', 0)
        if df.shape != (256, 256):
            raise TileSizeError('Tile size is not (256, 256)')

        return df.values

    def make_heightfield_images(self, arr):
        arr = np.interp(arr, (arr.min(), arr.max()), (0, 256 * 256))
        arr = self.enlarge(arr)
        img = arr.astype(np.uint16)

        cv2.imwrite(f'{TERRAIN_DIR}/heightfield.png', img)
        self.crop(img)

    def concat_from_files(self, folder_name):
        path = f'{TERRAIN_DIR}/{folder_name}'
        x, y = [int(s) for s in folder_name.split('_')]
        li = [
            [[x, y], [x + 1, y]],
            [[x, y + 1], [x + 1, y + 1]]
        ]
        arr = np.concatenate(
            [np.concatenate([self.get_array(f'{path}/{x}_{y}.txt') for x, y in sub], 1) for sub in li], 0
        )

        arr = arr.astype(np.float64)
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

        arr = arr.astype(np.float64)
        self.make_heightfield_images(arr)

    def mirror(self, path):
        top_l = self.get_array(path)
        top_r = np.fliplr(top_l)
        top = np.concatenate([top_l, top_r], 1)
        bottom = np.flipud(top)
        arr = np.concatenate([top, bottom], 0)
        self.make_heightfield_images(arr)


if __name__ == '__main__':

    li = [
        ['14517_6447.txt', '14518_6447.txt'],
        ['14517_6448.txt', '14518_6448.txt'],
    ]

    HeightfieldCreator().concat_from_files('14404_6459')
    # Heightfield().mirror_image('14515_6445.txt')

    # HeightfieldCreator().concat_from_url(14, 14072, 6861)