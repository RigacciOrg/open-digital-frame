import logging
import os
import subprocess

class addon():

    def __init__(self, app):

        # Where to find the resources images.
        res_lib = os.path.realpath(os.path.dirname(__file__))
        res_img = os.path.join(os.path.dirname(res_lib), 'img')

        self.item = {
            'dir': 'addon:poweroff',
            'title': 'Poweroff',
            'path': 'addon:poweroff',
            'sorttitle': None,
            'date': None,
            'tags': None,
            'thumbnail': os.path.join(res_img, 'power-button-icon.png'),
            'playlist': None,
            'slides': None
        }

    def run(self):
        cmd = ['/usr/local/bin/odf-poweroff']
        try:
            retcode = subprocess.call(cmd)
        except Exception as ex:
            logging.error('Error executing add-on: %s' % (str(ex),))
