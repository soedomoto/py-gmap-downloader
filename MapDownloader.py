import math
import os
from urllib import request
from PIL import Image


class MapDownloader(object):
    def __init__(self, lat_start, lng_start, lat_end, lng_end, zoom=12, tile_size=256):
        self.lat_start = lat_start
        self.lng_start = lng_start
        self.lat_end = lat_end
        self.lng_end = lng_end
        self.zoom = zoom
        self.tile_size = tile_size

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

    def generate_image(self, filename):
        width, height = 256 * (self._x_end + 1 - self._x_start), 256 * (self._y_end + 1 - self._y_start)
        map_img = Image.new('RGB', (width, height))

        p_curr, p_target = 1, (self._x_end + 1 - self._x_start) * (self._y_end + 1 - self._y_start)

        for x in range(0, self._x_end + 1 - self._x_start):
            for y in range(0, self._y_end + 1 - self._y_start):
                print('Processing tile #{} of {}'.format(p_curr, p_target))

                url = 'https://mts1.google.com/vt/lyrs=y&x=' + str(self._x_start + x) + '&y=' + str(self._y_start + y) + '&z=' + str(self.zoom)

                current_tile = 'tile-' + str(x) + '_' + str(y) + '_' + str(self.zoom) + '.png'
                request.urlretrieve(url, current_tile)

                # im = Image.open(current_tile)
                # map_img.paste(im, (x * 256, y * 256))
                # map_img.save(filename)

                # os.remove(current_tile)

                p_curr += 1


def main():
    try:
        md = MapDownloader(-6.159281, 106.842750, -6.161547, 106.847020, 20)
        md.generate_image('2.png')

        print("The map has successfully been created")
    except Exception as e:
        print("Could not generate the image - try adjusting the zoom level and checking your coordinates. Cause: {}".format(e))


if __name__ == '__main__':
    main()