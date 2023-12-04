import pandas as pd
import numpy as np
import cv2


class Heightfield:

    def __init__(self):
        self.tile_size = 256
        self.dir = 'terrains'
        # self.file = altitude_file_path

    def mirror_image(self, file):
        arr = self.get_array(file)

        top_l = np.interp(arr, (arr.min(), arr.max()), (0, 256 * 256))
        top_r = np.fliplr(top_l)
        top = np.concatenate([top_l, top_r], 1)
        bottom = np.flipud(top)
        mirror_arr = np.concatenate([top, bottom], 0)
        mirror_arr = mirror_arr.astype(np.uint16)

        mirror_arr = self.enlarge(mirror_arr)
        img = mirror_arr.astype(np.uint16)
        self.crop(img)

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

    def get_array(self, file):
        df = pd.read_csv(f'terrains/heightfield_texts/{file}', header=None)
        return df.values

    def concat_images(self, file_list):
        arr = np.concatenate(
            [np.concatenate([self.get_array(file) for file in files], 1) for files in file_list], 0
        )
        arr = np.interp(arr, (arr.min(), arr.max()), (0, 256 * 256))
        arr = self.enlarge(arr)
        img = arr.astype(np.uint16)

        cv2.imwrite('terrains/heightfield.png', img)
        self.crop(img)


# def download_txt(urls):

#     for url in urls:
#         s = url[:-4]
#         li = s.split('/')
#         save_name = f'{li[-2]}_{li[-1]}.txt'
#         print(save_name)
#         urllib.request.urlretrieve(url, save_name)


if __name__ == '__main__':
    # Heightfield('terrains/heightfield_texts/14516_6445.txt').make_image()
    # Heightfield('terrains/heightfield_texts/14516_6445.txt').make_img2()

    li = [
        ['14517_6447.txt', '14518_6447.txt'],
        ['14517_6448.txt', '14518_6448.txt'],
    ]

    # Heightfield().concat_images(li)
    Heightfield().mirror_image('14516_6448.txt')

    # urls = [
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14515/6445.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14515/6446.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14515/6447.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14515/6448.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14516/6445.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14516/6446.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14516/6447.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14516/6448.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14517/6445.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14517/6446.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14517/6447.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14517/6448.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14518/6445.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14518/6446.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14518/6447.txt',
    #     'http://cyberjapandata.gsi.go.jp/xyz/dem/14/14518/6448.txt',
    # ]
    # for url in urls:
    #     s = url[:-4]
    #     li = s.split('/')
    #     file = f'terrains/heightfield_texts/{li[-2]}_{li[-1]}.txt'
    #     save_name = f'terrains/{li[-2]}_{li[-1]}.png'
    #     make_image(file, save_name)

    # file = 'terrains/14517_6446.txt'
    # dest = 'terrains/14517_6446.png'
    # make_image(file, dest)