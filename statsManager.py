import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

class StatsManager():
    def __init__(self, db_path, output_dir, fractal_checkpoint_dir):
        self.output_dir = output_dir
        self.fractal_checkpoint_dir = fractal_checkpoint_dir 
        self.stats_dict = {}

        if isfile(db_path) is False:
            logger.info(f'Could not find stats db ! Path: {db_path},')
            stats_dict['mse'] = []
        else:
            logger.info(f'Loading stats db @ {db_path},')
            stats_dict = self.load(db_path)

    def load(self, db_path):
        with open(db_path) as fi:
            self.stats_dict = json.loads(fi)

    def save(self, db_path):
        with open(db_path, 'w+') as fi:
             fi.write(json.dumps(self.stats_dict))

    def set_user_stats(self, uuid, stats):
        for stat_name in stats.keys():
            self.stats_dict[uuid][stat_name] = stats[stat_name]

    def set_gen_stats(self, stats):
        for stat_name in stats.keys():
            self.stats_dict[stat_name] = stats[stat_name]

    def increment(self, key, amount = 1):
        self.stats_dict[stat_name] += amount

    def decrement(self, key, amount = 1):
        self.stats_dict[stat_name] -= amount

    def compute_convergence_graph(self):
        path = [join(self.fractal_checkpoint_dir, f) for f in listdir(self.fractal_checkpoint_dir)]
        if len(paths) < 2:
            logger.info(f'Not enough checkpoints to compute a convergence graph.')

        old_check = np.load(paths[1])
        new_check = np.load(paths[0])

        mse = ((old_check - new_check)**2).mean()

        self.stats_dict['mse'].append(mse)
        plt.plot(self.stats_dict['mse'])
        plt.ylabel('Mean Squared Error')
        plt.xlabel('Days')
        plt.savefig(join(self.output_dir, 'mse.jpg'))
