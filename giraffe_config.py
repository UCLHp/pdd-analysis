import os
import sys
from configparser import ConfigParser


class GiraffeConfig:
    '''
    Acquire user inputs.
    '''

    def __init__(self):
        # Select Operator
        basedir = os.path.dirname(sys.argv[0])
        config_file = os.path.join(basedir, 'giraffe_config_file.cfg')
        config = ConfigParser()
        config.read(config_file)

        self.db_dirpath_fe = config['Database']['Location_FE']
        self.db_dirpath_be = config['Database']['Location_BE']
        self.db_password_fe = config['Database']['Password_FE']
        self.db_password_be = config['Database']['Password_BE']
