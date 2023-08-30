from os.path import join
from PIL import Image
import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError

import logging
from os import listdir, mkdir, getcwd, remove
from os.path import isfile, join

logger = logging.getLogger("__name__")

class FractalManager():
    def __init__(self, input_dir, fractal_output_dir, checkpoint_output_dir, output_size, checkpoint_filename = 'last.npy'):
        self.input_dir = input_dir
        self.checkpoint_output_dir = checkpoint_output_dir
        self.fractal_output_dir = fractal_output_dir
        self.output_size = output_size
        self.checkpoint_filename = checkpoint_filename
        self.output_filename = "histogram.png"
        self.max_val = 0
        if not os.path.isfile(join(self.fractal_output_dir, self.checkpoint_filename)):
            logger.info(f'Could not find last checkpoint {join(self.fractal_output_dir, self.checkpoint_filename)},'
                          'starting from scratch !')
            self.last_checkpoint = np.zeros(output_size)
        else:
            logger.info(f'Loading last checkpoint: {join(self.fractal_output_dir, self.checkpoint_filename)}')
            self.last_checkpoint = self._load(join(self.fractal_output_dir, self.checkpoint_filename))

    def _load(self, filename):
        np.load(join(self.fractal_output_dir, filename))

    def _save(self, filename):
        logger.info(f'Saving last checkpoint: {join(self.fractal_output_dir, self.checkpoint_filename)}')
        np.save(join(self.checkpoint_output_dir, self.checkpoint_filename), self.last_checkpoint)

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

                files.append(histo_df)
            except EmptyDataError:
                logger.debug(f'{input_file} is empty !')
                continue

        for data in files: 
           self._compute(data)

        self._output_image()


    def _compute(self, histogram):
        self.last_checkpoint = np.add(self.last_checkpoint, histogram.values)
        self.max_val = np.log(np.max(self.last_checkpoint) + 1)
        logger.debug(f'{self.max_val}')
        self.last_checkpoint = self.smoothing_func(self.last_checkpoint, self.max_val)

    def _output_image(self):
        output_img = Image.fromarray(self.last_checkpoint.astype(np.uint8))
        output_img.convert("L")
        output_img.save(join(self.fractal_output_dir, self.output_filename))

#    def compute_histograms(self):
#        filename_list = self._get_checkpoints_list()
#        logger.debug(f'compute histogram on files : { filename_list }')
#        if type(filename_list) is list and len(filename_list) == 0:
#            logger.debug(f'no files to compute')
#            return
#
#        max_val = 0
#        for input_file in filename_list:
#            try:
#                logger.debug(f'opening {input_file}')
#                histo_df = pd.read_csv(input_file)
#            except EmptyDataError:
#                logger.debug(f'{input_file} is empty !')
#                continue
#
#            if histo_df.shape != self.output_size:
#                remove(input_file)
#                logger.info(f'file {input_file} was non compliant and removed')
#                continue
#
#            self.last_checkpoint = np.add(self.last_checkpoint, histo_df.values)
#            max_val = np.log(np.max(self.last_checkpoint) + 1)
#            logger.debug(f'{max_val}')
#
#            remove(input_file)
#        
#        self.last_checkpoint = self.smoothing_func(self.last_checkpoint, max_val)
#
#        output_img = Image.fromarray(self.last_checkpoint.astype(np.uint8))
#        output_img.convert("L")
#        output_img.save(join(self.fractal_output_dir, self.output_filename))
