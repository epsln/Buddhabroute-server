from os.path import join
from PIL import Image
import numpy as np
import pandas as pd
from pandas.errors import ParserError, EmptyDataError

from os import listdir, mkdir, getcwd, remove
from os.path import isfile, join, expanduser

class FractalManager():
    def __init__(self, input_dir, output_dir, output_size):
        self.input_dir = expanduser(input_dir)
        self.output_dir = expanduser(output_dir)
        self.output_size = output_size
        self.output_filename = "histogram.png"

        try:
            mkdir(self.input_dir)
        except FileExistsError:
            pass

        try:
            mkdir(self.output_dir)
        except FileExistsError:
            pass

    def smoothing_func(self, val, max_val):
        return np.log(val + 1)/max_val * 255

    def _get_checkpoints_list(self):
        return [join(self.input_dir, f) for f in listdir(self.input_dir)
                if isfile(join(self.input_dir, f)) and f.endswith(".npy")]

    def compute_histograms(self):
        filename_list = self._get_checkpoints_list()
        try:
            output_arr = np.load(join(self.output_dir, "last_checkpoint.npy"))
        except FileNotFoundError:
            output_arr = np.zeros(self.output_size)

        max_val = 0
        for input_file in filename_list:
            histo = np.load(input_file)
            if histo.shape != self.output_size:
                remove(input_file)
                continue

            output_arr = np.add(output_arr, histo)
            remove(input_file)
        max_val = np.log(np.max(output_arr) + 1)
        np.save(join(self.output_dir, "last_checkpoint.npy"), output_arr)
        output_arr = self.smoothing_func(output_arr, max_val)

        output_img = Image.fromarray(output_arr.astype(np.uint8))
        output_img.convert("L")
        output_img.save(join(self.output_dir, self.output_filename))
