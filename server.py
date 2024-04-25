#! /usr/bin/env python3
import time
import configparser, argparse
import logging
import sys
from os import makedirs, getcwd
from os.path import join
from pathlib import Path

import numpy as np
import json

from flask import Flask, request, redirect, send_file
from concurrent.futures import ThreadPoolExecutor
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler


from fractal import FractalManager
from statsManager import StatsManager 

app = Flask(__name__)
logger = logging.getLogger("__name__")

def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="description")
    parser.add_argument(
        "--debug",
        help="set the log level to DEBUG",
        action="store_true",
    )
    return parser.parse_args()

def configure_logger(debug, dryrun=False, log_prefix=None):
    """Configure the logger."""
    log_dir = Path.home() / f"{Path(__file__).stem}_LOG"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{time.strftime('%Y%m%d')}.log"
    log_format = ( 
        f"%(asctime)s{' - DRYRUN' if dryrun else ''} - %(levelname)s - {log_prefix if log_prefix else ''}%(message)s"
    )   
    logging.basicConfig(
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
        handlers=[logging.StreamHandler(), logging.FileHandler(log_file)],
        force=True,
    )   
    if debug:
        logger.setLevel(logging.DEBUG)
    logging.getLogger("sh").setLevel(logging.WARNING)

def parse_configuration(data_model):
    """Check and parse config file."""
    cfg_file = 'configs/server.conf'
    raw_config = configparser.ConfigParser()
    raw_config.read(cfg_file)
    config = {section: dict.fromkeys(data_model[section]) for section in data_model}
    try:
        for section in config:
            for item in config[section]:
                config[section][item] = raw_config.get(section, item)
    except (configparser.NoSectionError, configparser.NoOptionError) as err:
        logger.error(f"Invalid configuration: {err}")
        sys.exit(1)
    return config

@app.route('/status', methods=['GET'])
def check_app_status():
    return "App server running"

@app.route('/checkpoint', methods=['POST'])
def upload_checkpoint():
    """API endpoint to upload computed checkpoint by screensaver clients"""
    logger.debug(f'Request : {request.form}')
    if 'uuid' not in request.json: #TODO: validate json against a format
        logger.debug(f'invalid request : No uuid !')
        return redirect('/', code=303)

    if 'version' in request.json and request.json['version'] != "1.0a": #TODO: validate json against a format
        logger.debug(f'invalid request : wrong version!')
        return redirect('/', code=303)


    #TODO: Change filename + create a saving method in case we need some processing e.g. quarantines
    if request.json['nickname'] is not None:
        username = request.json['nickname']
    else:
        username = request.json['uuid'] 

    filename = f"{username}_{str(time.time())}.json"
    with open(join(fractal_mgr.input_dir, filename), 'w+') as f:
        json.dump(request.json, f)
    logger.debug(f"Saving histogram @ {join(fractal_mgr.input_dir, filename)}")
    return {"message": f"Thanks ! {username} "}

if __name__ == '__main__':
    args = get_args()
    print(f'Debug : {args.debug}')
    configure_logger(args.debug)
    config_data_model = {
        "server" : ['loglevel', 'worker'],
        "subdirs" : ['checkpointdir', 'fractal_outputdir', 'checkpoint_outputdir']
    }
    config = parse_configuration(config_data_model)
    logger.debug(f'{config}')

    logger.debug(f'Creating subdirs')
    for subdir in config['subdirs']:
        try:
            makedirs(config['subdirs'][subdir], exist_ok = True)
            logger.debug(f'''subdir { subdir }: { config['subdirs'][subdir] } created''')
        except FileExistsError as e:
            logger.debug(f'''subdir { subdir }: { config['subdirs'][subdir] } already exists''')
            pass
        

    executor = ThreadPoolExecutor(
        int(config['server']['worker'])
    )
    stats_mgr = StatsManager(
        db_path = 'db.json',
        output_dir = config['subdirs']['fractal_outputdir'],
        fractal_checkpoint_dir = config['subdirs']['checkpoint_outputdir']
    )
    fractal_mgr = FractalManager(
        stats_mgr = stats_mgr,
        input_dir = config['subdirs']['checkpointdir'], 
        fractal_output_dir = config['subdirs']['fractal_outputdir'], 
        checkpoint_output_dir = config['subdirs']['checkpoint_outputdir'], 
        checkpoint_size = (4, 7106, 4960)
    )
    last_compute_time = time.time()

    scheduler = BackgroundScheduler({'apscheduler.timezone': 'Europe/Paris'})
    scheduler.add_job(func=fractal_mgr.compute_histograms, trigger="interval", seconds=60 * 1)
    scheduler.add_job(func=fractal_mgr.save_checkpoint, trigger="interval", seconds=60 * 10)
    scheduler.add_job(func=fractal_mgr.save_image, trigger="cron", hour = 0)
    scheduler.add_job(func=fractal_mgr.save_checkpoint,  args = ['old.npy'], trigger="cron", hour = 0)

    scheduler.add_job(func=stats_mgr.compute_graphs, trigger="cron", hour = 1)
    scheduler.add_job(func=stats_mgr.increment, args = ['days_uptime'], trigger="cron", hour = 0)
    scheduler.add_job(func=stats_mgr.save, trigger="interval", seconds=60 * 60)

    scheduler.start()

    app.run(debug=args.debug, port=8000, use_reloader = False, threaded = False, processes = 1)