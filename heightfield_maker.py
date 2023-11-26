import pandas as pd
import numpy as np
import cv2


class Heightfield:

    def __init__(self, altitude_file_path):
        self.dir = 'terrains'
        self.file = altitude_file_path

    def make_image(self):
        df = pd.read_csv(self.file, header=None)
        arr = df.values

        top_l_256 = np.interp(arr, (arr.min(), arr.max()), (0, 65536))
        top_r_256 = np.fliplr(top_l_256)
        bottom_l_256 = np.flipud(top_l_256)
        bottom_r_256 = np.fliplr(bottom_l_256)

        top_h = np.concatenate([top_l_256, top_r_256], 1)
        bottom_h = np.concatenate([bottom_l_256, bottom_r_256], 1)
        square_512 = np.concatenate([top_h, bottom_h], 0)
        square_512 = square_512.astype(np.uint16)

        top_l_257 = square_512[:257, :257]
        top_r_257 = square_512[:257, 255:]
        bottom_l_257 = square_512[255:, :257]
        bottom_r_257 = square_512[255:, 255:]

        cv2.imwrite(f'{self.dir}/top_left.png', top_l_257)
        cv2.imwrite(f'{self.dir}/top_right.png', top_r_257)
        cv2.imwrite(f'{self.dir}/bottom_left.png', bottom_l_257)
        cv2.imwrite(f'{self.dir}/bottom_right.png', bottom_r_257)

    def find_size(self, current, size=1):
        size *= 2
        if size >= current:
            return size + 1
        return self.find_size(current, size)


# def make_image(file_path, output_path):
#     df = pd.read_csv(file_path, header=None)
#     size = len(df)
#     arr = df.values

#     if (found := find_size(size)) != size:
#         size = found
#         arr = cv2.resize(arr, (size, size))

#     arr = np.interp(arr, (arr.min(), arr.max()), (0, size ** 2))
#     arr = arr.astype(np.uint16)
#     cv2.imwrite(output_path, arr)


# >>> arr1_interp = np.interp(arr1, (arr1.min(), arr1.max()), (0, 256 ** 2))
# >>> arr1_interp2 = np.flipud(arr1_interp)
# >>> arr1_interp3 = np.flipud(arr1_interp2)
# >>> arr1_interp3 = np.fliplr(arr1_interp2)
# >>> arr1_interp4 = np.fliplr(arr1_interp)
# >>> h1 = np.concatenate([arr1_interp, arr1_interp4], 1)
# >>> h2 = np.concatenate([arr1_interp2, arr1_interp3], 1)
# >>> v_arr = np.concatenate([h1, h2], 0)
# >>> v_arr = v_arr.astype(np.uint16)
# >>> v_arr.shape
# (512, 512)
# >>> cv2.imwrite('test.png', v_arr)
# True
# >>> top_left = v_arr[:257, :257]
# >>> top_left.shape
# (257, 257)
# >>> top_right = v_arr[:257, 255:]
# >>> top_right.shape
# (257, 257)
# >>> bottom_left = v_arr[255:, :257]
# >>> bottom_left.shape
# (257, 257)
# >>> bottom_right = v_arr[255:, 255:]
# >>> bottom_right.shape
# (257, 257)
# >>> cv2.imwrite('top_left', top_left)
# Traceback (most recent call last):
#   File "<stdin>", line 1, in <module>
# cv2.error: OpenCV(4.8.0) D:\a\opencv-python\opencv-python\opencv\modules\imgcodecs\src\loadsave.cpp:696: error: (-2:Unspecified error) could not find a writer for the specified extension in function 'cv::imwrite_'

# >>> cv2.imwrite('top_left.png', top_left)
# True
# >>> cv2.imwrite('top_right.png', top_right)
# True
# >>> cv2.imwrite('bottom_right.png', bottom_right)
# True
# >>> cv2.imwrite('bottom_left.png', bottom_left)
# True





def download_txt(urls):

    for url in urls:
        s = url[:-4]
        li = s.split('/')
        save_name = f'{li[-2]}_{li[-1]}.txt'
        print(save_name)
        urllib.request.urlretrieve(url, save_name)


if __name__ == '__main__':
    Heightfield('terrains/heightfield_texts/14518_6445.txt').make_image()

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