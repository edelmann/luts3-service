"""
Configuration utils.

Author: Henrik Thostrup Jensen <htj@ndgf.org>
Copyright: Nordic Data Grid Facility (2009)
"""

import ConfigParser


# log isn't loaded yet, so make a fake log
class FakeLog:
    def msg(self, *args):
        print ','.join(args)
log = FakeLog()



# configuration constants
DEFAULT_HOSTKEY         = '/etc/grid-security/hostkey.pem'
DEFAULT_HOSTCERT        = '/etc/grid-security/hostcert.pem'
DEFAULT_CERTDIR         = '/etc/grid-security/certificates'
DEFAULT_AUTHZ_FILE      = '/etc/sgas.authz'
DEFAULT_WEB_FILES       = '/usr/local/share/sgas/webfiles'
DEFAULT_COREINFO_DESIGN = ''
DEFAULT_COREINFO_VIEW   = ''

# server options
SERVER_BLOCK     = 'server'
HOSTKEY          = 'hostkey'
HOSTCERT         = 'hostcert'
CERTDIR          = 'certdir'
DB               = 'db'
AUTHZ_FILE       = 'authzfile'
WEB_FILES        = 'webfiles'

COREINFO_DESIGN  = 'coredesign'
COREINFO_VIEW    = 'coreview'

# view options
VIEW_PREFIX      = 'view:'
VIEW_DESIGN      = 'design'
VIEW_NAME        = 'view'
VIEW_DESCRIPTION = 'description'
VIEW_FILTER      = 'filter'
VIEW_POSTPROCESS = 'postprocess'



class ConfigurationError(Exception):
    pass



def readConfig(filename):

    cfg = ConfigParser.SafeConfigParser()

    # add defaults
    cfg.add_section(SERVER_BLOCK)
    cfg.set(SERVER_BLOCK, HOSTKEY,  DEFAULT_HOSTKEY)
    cfg.set(SERVER_BLOCK, HOSTCERT, DEFAULT_HOSTCERT)
    cfg.set(SERVER_BLOCK, CERTDIR,  DEFAULT_CERTDIR)
    cfg.set(SERVER_BLOCK, AUTHZ_FILE, DEFAULT_AUTHZ_FILE)
    cfg.set(SERVER_BLOCK, WEB_FILES,  DEFAULT_WEB_FILES)
    cfg.set(SERVER_BLOCK, COREINFO_DESIGN, DEFAULT_COREINFO_DESIGN)
    cfg.set(SERVER_BLOCK, COREINFO_VIEW,   DEFAULT_COREINFO_VIEW)

    # read cfg file
    cfg.readfp(open(filename))

    return cfg

