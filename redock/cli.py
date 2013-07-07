# Command line interface for the redock program.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: July 7, 2013
# URL: https://github.com/xolox/python-redock

# Standard library modules.
import getopt
import logging
import os
import subprocess
import sys
import textwrap

# External dependencies.
from humanfriendly import Timer

# Modules included in our package.
from redock.api import Container, Image, DEFAULT_BASE_IMAGE
from redock.logger import logger

def main():
    """
    Command line interface for the ``redock`` program.
    """
    # Parse and validate the command line arguments.
    try:
        # Command line option defaults.
        base = DEFAULT_BASE_IMAGE
        hostname = None
        message = None
        # Parse the command line options.
        options, arguments = getopt.getopt(sys.argv[1:], 'b:n:m:vh',
                                          ['base=', 'hostname=', 'message=', 'verbose', 'help'])
        for option, value in options:
            if option in ('-b', '--base'):
                base = value
            elif option in ('-n', '--hostname'):
                hostname = value
            elif option in ('-m', '--message'):
                message = value
            elif option in ('-v', '--verbose'):
                if logger.getEffectiveLevel() == logging.INFO:
                    logger.setLevel(logging.VERBOSE)
                elif logger.getEffectiveLevel() == logging.VERBOSE:
                    logger.setLevel(logging.DEBUG)
            elif option in ('-h', '--help'):
                usage()
                return
            else:
                # Programming error...
                assert False, "Unhandled option!"
        # Handle the positional arguments.
        if len(arguments) < 2:
            usage()
            return
        supported_actions = ('start', 'stop', 'save')
        action = arguments.pop(0)
        if action not in supported_actions:
            msg = "Action not supported: %r (supported actions are: %s)"
            raise Exception, msg % (action, ', '.join(supported_actions))
    except Exception, e:
        logger.error("Failed to parse command line arguments!")
        logger.exception(e)
        usage()
        sys.exit(1)
    # Start the container and connect to it over SSH.
    try:
        for image_name in arguments:
            container = Container(image=Image.coerce(image_name),
                                  base=Image.coerce(base),
                                  hostname=hostname)
            if action == 'start':
                container.initialize()
                if len(arguments) == 1 and all(os.isatty(n) for n in range(3)):
                    ssh_timer = Timer()
                    logger.info("Detected interactive terminal, connecting to container ..")
                    ssh_client = subprocess.Popen(['ssh', container.ssh_alias])
                    ssh_client.wait()
                    if ssh_client.returncode == 0:
                        logger.info("SSH client exited with status %i after %s.",
                                    ssh_client.returncode, ssh_timer)
                    else:
                        logger.warn("SSH client exited with status %i after %s.",
                                    ssh_client.returncode, ssh_timer)
                container.detach()
            elif action == 'stop':
                container.stop()
            elif action == 'save':
                container.commit_changes(message=message)
            else:
                # Programming error...
                assert False, "Unhandled action!"
    except Exception, e:
        logger.exception(e)
        sys.exit(1)

def usage():
    """
    Print a usage message to the console.
    """
    usage = textwrap.dedent("""
        Usage: redock [OPTIONS] ACTION CONTAINER..

        Create and manage Docker containers and images. Supported actions are
        `start', `ssh' and `stop'.

        Supported options:

          -b, --base=IMAGE     override the base image (defaults to {base})
          -n, --hostname=NAME  set container host name (defaults to image tag)
          -m, --message=TEXT   message for image created with `save' action
          -v, --verbose        make more noise (can be repeated)
          -h, --help           show this message and exit
    """).strip()
    print usage.format(base=DEFAULT_BASE_IMAGE)

# vim: ts=4 sw=4 et