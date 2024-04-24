from os.path import join
from PIL import Image
import numpy as np
import pandas as pd
import json
from pandas.errors import EmptyDataError
import base64
import zlib
from matplotlib.colors import hsv_to_rgb


import logging
from os import listdir, mkdir, getcwd, remove, rename
from os.path import isfile, join
import time

logger = logging.getLogger("__name__")

class FractalManager():
    def __init__(self, stats_mgr, input_dir, fractal_output_dir, checkpoint_output_dir, checkpoint_size, checkpoint_filename = 'last.npy'):
        #TODO: init from config instead
        self.stats_mgr = stats_mgr
        self.input_dir = input_dir
        self.checkpoint_output_dir = checkpoint_output_dir
        self.fractal_output_dir = fractal_output_dir
        self.checkpoint_size = checkpoint_size 
        self.image_size = (checkpoint_size[1], checkpoint_size[2], 3)
        self.checkpoint_filename = checkpoint_filename
        self.output_filename = "histogram.png"
        self.archive_filename = "histogram.png"
        if not isfile(join(self.checkpoint_output_dir, self.checkpoint_filename)):
            logger.info(f'Could not find last checkpoint {join(self.checkpoint_output_dir, self.checkpoint_filename)},'
                          'starting from stratch !')
            self.last_checkpoint = np.zeros(checkpoint_size)
        else:
            logger.info(f'Loading last checkpoint: {self.checkpoint_output_dir} {self.checkpoint_filename}')
            self.last_checkpoint = self._load_checkpoint(join(self.checkpoint_output_dir, self.checkpoint_filename))

    def _load(self, filename):
        with open(join(self.checkpoint_output_dir, filename)) as f:
            js = json.load(f)
            histoVal = np.frombuffer(
                zlib.decompress(
                    base64.b64decode(
                        js['histogram']
                    )
                ),
                dtype=np.float64
            )
            red = np.frombuffer(
                zlib.decompress(
                    base64.b64decode(
                        js['red']
                    )
                ),
                dtype=np.float64
            )
            green = np.frombuffer(
                zlib.decompress(
                    base64.b64decode(
                        js['green']
                    )
                ),
                dtype=np.float64
                )
            blue = np.frombuffer(
                zlib.decompress(
                    base64.b64decode(
                        js['blue']
                    )
                ),
                dtype=np.float64
            )
            size = (int(js['shape'][0]), int(js['shape'][1]))
            histogram = np.zeros((4, int(js['shape'][0]), int(js['shape'][1])))
            histogram[0, :, :] = np.reshape(histoVal, size)
            histogram[1, :, :] = np.reshape(red, size)
            histogram[2, :, :] = np.reshape(green, size)
            histogram[3, :, :] = np.reshape(blue, size)
        return histogram

    def _load_checkpoint(self, filename):
        self.last_checkpoint = np.load(filename)


    def save_checkpoint(self, filename = None):
        if not filename:
            filename = self.checkpoint_filename
        logger.info(f'Saving last checkpoint: {self.checkpoint_output_dir}, {filename}')
        return np.save(join(self.checkpoint_output_dir, filename), self.last_checkpoint)

    def smoothing_func(self):
        histo = np.log(self.last_checkpoint[0, :, :] + 1)/np.log(np.max(self.last_checkpoint[0, :, :]) + 1)

        image = np.zeros(self.image_size)
        image[:, :, 0] = histo * self.last_checkpoint[1, :, :]
        image[:, :, 1] = histo * self.last_checkpoint[2, :, :] 
        image[:, :, 2] = histo * self.last_checkpoint[3, :, :]
        
        return image

    def _get_checkpoints_list(self):
        return [join(self.input_dir, f) for f in listdir(self.input_dir)
                if isfile(join(self.input_dir, f)) and f.endswith(".json")]

    def compute_histograms(self):
        filename_list = self._get_checkpoints_list()
        logger.debug(f'compute histogram on files : { filename_list }')
        if type(filename_list) is list and len(filename_list) == 0:
            logger.debug(f'no files to compute')
            return

        files = []
        for input_file in filename_list:
            try:
                logger.debug(f'opening {input_file}')
                histo = self._load(input_file)
                if histo.shape != self.checkpoint_size:
                    remove(input_file)
                    logger.info(f'File {input_file} wrong shape: Expected {checkpoint_size}, got {histo.shape}')
                    continue
            except Exception as e:
                remove(input_file)
                logger.debug(f'Error reading {input_file}: {e}')
                continue

            self._compute(histo)
            remove(input_file)

            self.stats_mgr.increment('tot_checkpoints', 1)            
        self.save_image(self.output_filename)

    def _compute(self, histogram):
        self.stats_mgr.increment('tot_num_pts', histogram[0, :, :] .sum())
        self.last_checkpoint[0, :, :] = np.add(self.last_checkpoint[0, :, :], histogram[0, :, :])
        #Need to replace in case of zero, and mean elsewise
        #Change value of incoming histogram to values of last checkpoint in case of 0, then do a mean on all values
        histogram[1] = np.where(histogram[1] < 1e-6, self.last_checkpoint[1], histogram[1])
        histogram[2] = np.where(histogram[2] < 1e-6, self.last_checkpoint[2], histogram[2])
        histogram[3] = np.where(histogram[3] < 1e-6, self.last_checkpoint[3], histogram[3])
        self.last_checkpoint[1] = np.where(self.last_checkpoint[1] < 1e-6, histogram[1], (self.last_checkpoint[1] + histogram[1]) / 2.0)
        self.last_checkpoint[2] = np.where(self.last_checkpoint[2] < 1e-6, histogram[2], (self.last_checkpoint[2] + histogram[2]) / 2.0)
        self.last_checkpoint[3] = np.where(self.last_checkpoint[3] < 1e-6, histogram[3], (self.last_checkpoint[3] + histogram[3]) / 2.0)

    def save_image(self, filename = None):
        if not filename:
            filename = f'{str(round(time.time()))}.png'
        logger.debug(f'Saving output image at {join(self.fractal_output_dir, filename)}')

        out_array = self.smoothing_func() * 255
        logger.debug(f'out_img min: {np.min(out_array[:, :, 0])}' )
        logger.debug(f'out_img min: {np.min(out_array[:, :, 1])}' )
        logger.debug(f'out_img min: {np.min(out_array[:, :, 2])}' )
        logger.debug(f'out_img max: {np.max(out_array[:, :, 0])}' )
        logger.debug(f'out_img max: {np.max(out_array[:, :, 1])}' )
        logger.debug(f'out_img max: {np.max(out_array[:, :, 2])}' )

        output_img = Image.fromarray(out_array.astype(np.uint8), 'RGB')
        output_img.save(join(self.fractal_output_dir, filename))
