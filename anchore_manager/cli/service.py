import os
import re
import sys
import json
import time
import click
import importlib
import traceback
import threading
import subprocess
import watchdog
import anchore_engine.configuration.localconfig
#import anchore_engine.db.entities.upgrade

from watchdog.observers import Observer
from watchdog.events import RegexMatchingEventHandler

from anchore_engine.subsys import logger
import anchore_engine.db.entities.common
from anchore_engine.db.entities.exceptions import TableNotFoundError
from anchore_engine.db.entities.exceptions import is_table_not_found

import anchore_manager.cli.utils

class AnchoreLogWatcher(RegexMatchingEventHandler):
    regexes = [re.compile(".*/anchore-.*\.log$")]
    files = {}

    def do_close(self, event):
        if event.src_path in self.files and self.files[event.src_path]['filehandle']:
            self.files[event.src_path]['filehandle'].close()
        self.files[event.src_path] = {'filehandle': None, 'filetell': 0}

    def on_deleted(self, event):
        if event.src_path not in self.files:
            self.files[event.src_path] = {'filehandle': None, 'filetell': 0}

        self.do_close(event)

    def on_modified(self, event):
        if event.src_path not in self.files:
            self.files[event.src_path] = {'filehandle': None, 'filetell': 0}

        if not self.files[event.src_path]['filehandle']:
            if os.path.exists(event.src_path):
                self.files[event.src_path]['filehandle'] = open(event.src_path)

        if self.files[event.src_path]['filehandle']:
            patt = re.match(".*anchore-(.*)\.log$", event.src_path)
            if patt:
                logname = patt.group(1)
            else:
                logname = event.src_path

            for line in self.files[event.src_path]['filehandle'].readlines():
                sys.stdout.write("[service:" + str(logname) + "] " + line)

            self.files[event.src_path]['filetell'] = self.files[event.src_path]['filehandle'].tell()

    def on_created(self, event):
        if event.src_path not in self.files:
            self.files[event.src_path] = {'filehandle': None, 'filetell': 0}

        if self.files[event.src_path]['filehandle']:
            self.do_close(event)

        if os.path.exists(event.src_path):
            self.files[event.src_path]['filehandle'] = open(event.src_path)
            self.files[event.src_path]['filetell'] = 0

    def on_moved(self, event):
        if event.src_path not in self.files:
            self.files[event.src_path] = {'filehandle': None, 'filetell': 0}
        self.on_created(event)

    def on_any_event(self, event):
        if event.src_path not in self.files:
            self.files[event.src_path] = {'filehandle': None, 'filetell': 0}


class ServiceThread():

    def __init__(self, thread_target, thread_args):
        self.thread_target = thread_target
        self.thread_args = thread_args
        self.start()

    def start(self):
        self.thread = threading.Thread(target=self.thread_target, args=self.thread_args)
        self.thread.name = self.thread_args[0]
        self.thread.start()


def terminate_service(service, flush_pidfile=False):
    pidfile = "/var/run/" + service + ".pid"
    try:
        thepid = None
        if os.path.exists(pidfile):
            with open(pidfile, 'r') as FH:
                thepid = int(FH.read())

        if thepid:
            print "Found old pid for service: {}. Terminating it".format(service)
            try:
                os.kill(thepid, 0)
            except OSError:
                pass
            else:
                print "killing old twistd pid: " + str(thepid)
                os.kill(thepid, 9)
            if flush_pidfile:
                os.remove(pidfile)
    except Exception as err:
        print "could not shut down running twistd - exception: " + str(err)


def startup_service(service, configdir):
    pidfile = "/var/run/" + service + ".pid"
    logfile = "/var/log/anchore/" + service + ".log"
    # os.environ['ANCHORE_LOGFILE'] = logfile

    print "cleaning up service: " + str(service)
    terminate_service(service, flush_pidfile=True)

    twistd_cmd = '/bin/twistd'
    for f in ['/bin/twistd', '/usr/local/bin/twistd']:
        if os.path.exists(f):
            twistd_cmd = f

    cmd = [twistd_cmd, '--logger=anchore_engine.subsys.twistd_logger.logger', '--pidfile', pidfile, "-n", service, '--config', configdir]
    print "starting service: " + str(service)
    print "\t " + ' '.join(cmd)

    try:
        newenv = os.environ.copy()
        newenv['ANCHORE_LOGFILE'] = logfile
        pipes = subprocess.Popen(cmd, env=newenv)
        sout, serr = pipes.communicate()
        rc = pipes.returncode
        raise Exception("process exited: " + str(rc))
    except Exception as err:
        traceback.print_exc()
        print "service process exited at (" + str(time.ctime()) + "): " + str(err)

    print "exiting service thread"
    return (False)

config = {}
module = None

@click.group(name='service', short_help='Service operations')
@click.pass_obj
def service(ctx_config):
    global config, module
    config = ctx_config

    try:
        # do some DB connection/pre-checks here
        try:

            log_level = 'INFO'
            if config['debug']:
                log_level = 'DEBUG'
            logger.set_log_level(log_level, log_to_stdout=True)

        except Exception as err:
            raise err

    except Exception as err:
        print anchore_manager.cli.utils.format_error_output(config, 'service', {}, err)
        sys.exit(2)

@service.command(name='start', short_help="Start anchore-engine")
@click.option("--auto-upgrade", is_flag=True, help="Perform automatic upgrade on startup")
@click.option("--anchore-module", nargs=1, help="Name of anchore module to call DB routines from (default=anchore_engine)")
@click.option("--skip-config-validate", nargs=1, help="Comma-separated list of configuration file sections to skip specific validation processing (e.g. services,credentials,webhooks)")
def start(auto_upgrade, anchore_module, skip_config_validate):
    global config
    """
    """
    ecode = 0

    auto_upgrade = True

    if not anchore_module:
        module_name = "anchore_engine"
    else:
        module_name = str(anchore_module)

    try:
        service_map = {
            'analyzer': 'anchore-worker',
            'simplequeue': 'anchore-simplequeue',
            'apiext': 'anchore-api',
            'catalog': 'anchore-catalog',
            'kubernetes_webhook': 'anchore-kubernetes-webhook',
            'policy_engine': 'anchore-policy-engine',
            'feeds': 'anchore-feeds'
        }

        validate_params = {
            'services': True,
            'webhooks': True,
            'credentials': True
        }
        if skip_config_validate:
            try:
                items = skip_config_validate.split(',')
                for item in items:
                    validate_params[item] = False
            except Exception as err:
                raise Exception(err)

        # find/set up configuration        
        configdir = config['configdir']
        configfile = os.path.join(configdir, "config.yaml")

        localconfig = None
        if os.path.exists(configfile):
            try:
                localconfig = anchore_engine.configuration.localconfig.load_config(configdir=configdir, configfile=configfile, validate_params=validate_params)
            except Exception as err:
                raise Exception("cannot load local configuration: " + str(err))
        else:
            raise Exception("cannot locate configuration file ({})".format(configfile))

        # load the appropriate DB module
        try:
            print "Loading DB routines from module ({})".format(module_name)
            module = importlib.import_module(module_name + ".db.entities.upgrade")
        except TableNotFoundError as ex:
            print "Initialized DB not found."
        except Exception as err:
            raise Exception("Input anchore-module (" + str(module_name) + ") cannot be found/imported - exception: " + str(err))

        # preflight - db checks
        try:
            db_params = anchore_engine.db.entities.common.get_params(localconfig)
            db_params = anchore_manager.cli.utils.connect_database(config, db_params['db_connect'], db_params['db_connect_args']['ssl'], db_retries=300)

            code_versions, db_versions = anchore_manager.cli.utils.init_database(upgrade_module=module, localconfig=localconfig)

            in_sync = False
            timed_out = False
            max_timeout = 3600

            timer = time.time()
            while not in_sync and not timed_out:
                code_versions, db_versions = module.get_versions()

                if code_versions and db_versions:
                    if code_versions['db_version'] != db_versions['db_version']:
                        if auto_upgrade:
                            print "Auto-upgrade is set - performing upgrade."
                            try:
                                # perform the upgrade logic here
                                rc = module.run_upgrade()
                                if rc:
                                    print "Upgrade completed"
                                else:
                                    print "No upgrade necessary. Completed."
                            except Exception as err:
                                raise err

                            in_sync = True
                        else:
                            print "this version of anchore-engine requires the anchore DB version ("+str(code_versions['db_version'])+") but we discovered anchore DB version ("+str(db_versions['db_version'])+") in the running DB - it is safe to run the upgrade while seeing this message - will retry for "+str(max_timeout - int(time.time() - timer))+" more seconds."
                            time.sleep(5)
                    else:
                        print "DB version and code version in sync."
                        in_sync = True
                else:
                    print('Warn: no existing anchore DB data can be discovered, assuming bootstrap')
                    in_sync = True

                if (max_timeout - int(time.time() - timer)) < 0:
                    timed_out = True

            if not in_sync:
                raise Exception("this version of anchore-engine requires the anchore DB version ("+str(code_versions['db_version'])+") but we discovered anchore DB version ("+str(db_versions['db_version'])+") in the running DB - please perform the DB upgrade process and retry")

        except Exception as err:
            raise err

        finally:
            rc = anchore_engine.db.entities.common.do_disconnect()

        # start up the services
        startFailed = False
        if 'ANCHORE_ENGINE_SERVICES' in os.environ:
            input_services = os.environ['ANCHORE_ENGINE_SERVICES'].split()
        else:
            config_services = localconfig.get('services', {})
            if not config_services:
                print('Warn: Did not find any services to execute in the config file')
                sys.exit(1)

            input_services = [ name for name, srv_conf in config_services.items() if srv_conf.get('enabled')]

        services = []
        for service_conf_name in input_services:
            if service_conf_name in service_map.values():
                service = service_conf_name
            else:
                service = service_map.get(service_conf_name)

            if service:
                services.append(service)
            else:
                print('Warn: specified service {} not found in list of available services {} - removing from list of services to start'.format(service_conf_name, service_map.keys()))

        if 'anchore-catalog' in services:
            services.remove('anchore-catalog')
            services.insert(0, 'anchore-catalog')

        if not services:
            print "No services found in ANCHORE_ENGINE_SERVICES or as enabled in config.yaml to start - exiting"
            sys.exit(1)

        print('Starting services: {}'.format(services))
        #services = ['anchore-catalog', 'anchore-api', 'anchore-simplequeue', 'anchore-worker', 'anchore-kubernetes-webhook', 'anchore-policy-engine']

        try:
            if not os.path.exists("/var/log/anchore"):
                os.makedirs("/var/log/anchore/", 0755)
        except Exception as err:
            print "cannot create log directory /var/log/anchore - exception: " + str(err)
            raise err

        pids = []
        keepalive_threads = []
        for service in services:
            pidfile = "/var/run/" + service + ".pid"
            try:
                service_thread = ServiceThread(startup_service, (service, configdir))
                keepalive_threads.append(service_thread)
                max_tries = 30
                tries = 0
                while not os.path.exists(pidfile) and tries < max_tries:
                    time.sleep(1)
                    tries = tries + 1

                time.sleep(2)
            except Exception as err:
                startFailed = True
                print "service start failed - exception: " + str(err)

        if startFailed:
            print "one or more services failed to start. cleanly terminating the others"
            for service in services:
                terminate_service(service, flush_pidfile=True)

            sys.exit(1)
        else:
            # start up the log watchers
            try:
                observer = Observer()
                observer.schedule(AnchoreLogWatcher(), path="/var/log/anchore/")
                observer.start()

                try:
                    while True:
                        time.sleep(1)
                        if 'auto_restart_services' in localconfig and localconfig['auto_restart_services']:
                            for service_thread in keepalive_threads:
                                if not service_thread.thread.is_alive():
                                    print "restarting service " + service_thread.thread.name
                                    service_thread.start()

                except KeyboardInterrupt:
                    observer.stop()
                observer.join()

            except Exception as err:
                print "failed to startup log watchers - exception: " + str(err)
                raise err

    except Exception as err:
        print anchore_manager.cli.utils.format_error_output(config, 'servicestart', {}, err)
        if not ecode:
            ecode = 2
            
    anchore_manager.cli.utils.doexit(ecode)