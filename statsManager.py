import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from os.path import isfile, join
from os import listdir
import json
import logging

logger = logging.getLogger("__name__")

class StatsManager():
    def __init__(self, db_path, output_dir, fractal_checkpoint_dir):
        self.db_path = db_path 
        self.output_dir = output_dir
        self.fractal_checkpoint_dir = fractal_checkpoint_dir 
        self.stats_dict = {}

        if isfile(db_path) is False:
            logger.info(f'Could not find stats db ! Path {db_path}. Starting from scratch.')
            self.stats_dict['mse'] = []
        else:
            logger.info(f'Loading stats db @ {db_path},')
            self.load()

    def load(self):
        with open(self.db_path) as fi:
            self.stats_dict = json.load(fi)

    def save(self):
        with open(self.db_path, 'w+') as fi:
             fi.write(json.dumps(self.stats_dict))

    def set_user_stats(self, uuid, stats):
        for stat_name in stats.keys():
            self.stats_dict[uuid][stat_name] = stats[stat_name]

    def set_gen_stats(self, stats):
        for stat_name in stats.keys():
            self.stats_dict[stat_name] = stats[stat_name]

    def increment(self, key, amount = 1):
        logger.debug(f'Increasing {key} by {amount}')
        if key in self.stats_dict:
            self.stats_dict[key] += amount
        else:
            self.stats_dict[key] = amount

    def decrement(self, key, amount = 1):
        logger.debug(f'Decreasing {key} by {amount}')
        if key in self.stats_dict:
            self.stats_dict[key] -= amount
        else:
            self.stats_dict[key] = amount

    def compute_graphs(self):
        paths = [join(self.fractal_checkpoint_dir, f) for f in listdir(self.fractal_checkpoint_dir)]
        if len(paths) < 2:
            logger.info(f'Not enough checkpoints to compute a convergence graph.')
            return 

        old_check = np.load(paths[1])
        new_check = np.load(paths[0])

        mse = ((old_check - new_check)**2).mean()

        self.stats_dict['mse'].append(mse)
        plt.plot(self.stats_dict['mse'])
        plt.ylabel('Mean Squared Error')
        plt.xlabel('Days')
        plt.savefig(join(self.output_dir, 'mse.jpg'))
