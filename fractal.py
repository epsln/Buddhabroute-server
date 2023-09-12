from os.path import join
from PIL import Image
import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError

import logging
from os import listdir, mkdir, getcwd, remove
from os.path import isfile, join
import time

logger = logging.getLogger("__name__")

class FractalManager():
    def __init__(self, input_dir, fractal_output_dir, checkpoint_output_dir, output_size, checkpoint_filename = 'last.npy'):
        self.input_dir = input_dir
        self.checkpoint_output_dir = checkpoint_output_dir
        self.fractal_output_dir = fractal_output_dir
        self.output_size = output_size
        self.checkpoint_filename = checkpoint_filename
        self.output_filename = "histogram.png"
        self.archive_filename = "histogram.png"
        if not isfile(join(self.checkpoint_output_dir, self.checkpoint_filename)):
            logger.info(f'Could not find last checkpoint {join(self.checkpoint_output_dir, self.checkpoint_filename)},'
                          'starting from scratch !')
            self.last_checkpoint = np.zeros(output_size)
        else:
            logger.info(f'Loading last checkpoint: {join(self.checkpoint_output_dir, self.checkpoint_filename)}')
            self.last_checkpoint = self._load(join(self.checkpoint_output_dir, self.checkpoint_filename))

    def _load(self, filename):
        return np.load(join(self.checkpoint_output_dir, filename))

    def save_checkpoint(self):
        logger.info(f'Saving last checkpoint: {join(self.fractal_output_dir, self.checkpoint_filename)}')
        return np.save(join(self.checkpoint_output_dir, self.checkpoint_filename), self.last_checkpoint)

        logger.info(f'Saving last checkpoint: {join(self.fractal_output_dir, self.checkpoint_filename)}')
        return np.save(join(self.checkpoint_output_dir, self.checkpoint_filename), self.last_checkpoint)

    def smoothing_func(self, val, max_val):
        return np.log(val + 1)/max_val * 255

    def _get_checkpoints_list(self):
        return [join(self.input_dir, f) for f in listdir(self.input_dir)
                if isfile(join(self.input_dir, f)) and f.endswith(".npy")]

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
                if histo.shape != self.output_size:
                    remove(input_file)
                    logger.info(f'file {input_file} was non compliant')
                    continue

                files.append(histo)
            except EmptyDataError:
                remove(input_file)
                logger.debug(f'{input_file} is empty !')
                remove(input_file)
                continue

            remove(input_file)

        for data in files:
           self._compute(data)

        self.save_image(self.output_filename)

    def _compute(self, histogram):
        self.last_checkpoint = np.add(self.last_checkpoint, histogram)

    def save_image(self, filename = None):
        if not filename:
            filename = f'{str(round(time.time()))}.png'
        logger.debug(f'Saving output image at {join(self.fractal_output_dir, filename)}')
        max_val = np.log(np.max(self.last_checkpoint) + 1)
        out_array = self.smoothing_func(self.last_checkpoint, max_val)
        output_img = Image.fromarray(out_array.astype(np.uint8))
        output_img.convert("L")
        output_img.save(join(self.fractal_output_dir, filename))
