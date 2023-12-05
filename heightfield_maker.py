import pandas as pd
import numpy as np
import cv2


DIR = 'terrains/heightfield_texts'


class Heightfield:

    def __init__(self):
        self.tile_size = 256
        self.dir = 'terrains'
        # self.file = altitude_file_path

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

        cv2.imwrite(f'{self.dir}/top_left.png', top_l)
        cv2.imwrite(f'{self.dir}/top_right.png', top_r)
        cv2.imwrite(f'{self.dir}/bottom_left.png', bottom_l)
        cv2.imwrite(f'{self.dir}/bottom_right.png', bottom_r)

    def get_array(self, path):
        df = pd.read_csv(path, header=None).replace('e', 0)
        return df.values

    def make_heightfield_images(self, arr):
        arr = np.interp(arr, (arr.min(), arr.max()), (0, 256 * 256))
        arr = self.enlarge(arr)
        img = arr.astype(np.uint16)

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


if __name__ == '__main__':
    # Heightfield('terrains/heightfield_texts/14516_6445.txt').make_image()
    # Heightfield('terrains/heightfield_texts/14516_6445.txt').make_img2()

    li = [
        ['14517_6447.txt', '14518_6447.txt'],
        ['14517_6448.txt', '14518_6448.txt'],
    ]

    # Heightfield().concat_from_files(li)
    Heightfield().mirror_image('14515_6445.txt')

    # Heightfield().concat_from_url(14, 14525, 6396)