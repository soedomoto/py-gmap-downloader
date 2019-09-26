import math
import multiprocessing

import os
import queue
import shutil
import threading
from PIL import Image
from datetime import datetime
from urllib import request


class MapDownloader(object):
    def __init__(self, lat_start, lng_start, lat_end, lng_end, zoom=12, tile_size=256):
        self.tile_server = 'https://mts1.google.com/vt/lyrs=y&x={}&y={}&z={}'

        self.lat_start = lat_start
        self.lng_start = lng_start
        self.lat_end = lat_end
        self.lng_end = lng_end
        self.zoom = zoom
        self.tile_size = tile_size
        self.q = queue.Queue()

        self._generate_xy_point()

    def _generate_xy_point(self):
        self._x_start, self._y_start = self._convert_latlon_to_xy(self.lat_start, self.lng_start)
        self._x_end, self._y_end = self._convert_latlon_to_xy(self.lat_end, self.lng_end)

    def _convert_latlon_to_xy(self, lat, lng):
        tiles_count = 1 << self.zoom

        point_x = (self.tile_size / 2 + lng * self.tile_size / 360.0) * tiles_count // self.tile_size
        sin_y = math.sin(lat * (math.pi / 180.0))
        point_y = ((self.tile_size / 2) + 0.5 * math.log((1 + sin_y) / (1 - sin_y)) *
                   -(self.tile_size / (2 * math.pi))) * tiles_count // self.tile_size

        return int(point_x), int(point_y)

    def _fetch_worker(self):
        while True:
            item = self.q.get()
            if item is None:
                break

            idx, url, current_tile = item
            print('Fetching #{} of {}: {}'.format(idx, self.q_size, url))
            request.urlretrieve(url, current_tile)

            self.q.task_done()

    def write_into(self, filename):
        # create temp dir
        directory = os.path.abspath('./{}'.format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
        if not os.path.exists(directory):
            os.makedirs(directory)

        # generate source list
        idx = 1
        for x in range(0, self._x_end + 1 - self._x_start):
            for y in range(0, self._y_end + 1 - self._y_start):
                url = self.tile_server.format(
                    str(self._x_start + x), str(self._y_start + y), str(self.zoom))
                current_tile = os.path.join(directory, 'tile-{}_{}_{}.png'.format(
                    str(self._x_start + x), str(self._y_start + y), str(self.zoom)))
                self.q.put((idx, url, current_tile))
                idx += 1

        # stop workers
        for i in range(multiprocessing.cpu_count()):
            self.q.put(None)

        # start fetching tile using multithread to speed up process
        self.q_size = self.q.qsize()

        threads = []
        for i in range(multiprocessing.cpu_count()):
            t = threading.Thread(target=self._fetch_worker)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        # combine image into single
        width, height = 256 * (self._x_end + 1 - self._x_start), 256 * (self._y_end + 1 - self._y_start)
        map_img = Image.new('RGB', (width, height))

        for x in range(0, self._x_end + 1 - self._x_start):
            for y in range(0, self._y_end + 1 - self._y_start):
                current_tile = os.path.join(directory, 'tile-{}_{}_{}.png'.format(
                    str(self._x_start + x), str(self._y_start + y), str(self.zoom)))
                im = Image.open(current_tile)
                map_img.paste(im, (x * 256, y * 256))

        map_img.save(filename)

        # remove temp dir
        shutil.rmtree(directory)


def main():
    try:
        md = MapDownloader(-6.256524, 107.170208, -6.292112, 107.242934, 20)
        md.write_into('lemanabang.png')

        print("The map has successfully been created")
    except Exception as e:
        print(
            "Could not generate the image - try adjusting the zoom level and checking your coordinates. Cause: {}".format(
                e))


if __name__ == '__main__':
    main()
