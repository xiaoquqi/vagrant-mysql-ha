#!/usr/bin/env python

# This script is used to repaire mysql cluster

import logging
import os
import re
import salt.client
import sys

HA_HOSTS = ["db1.mysql.com", "db2.mysql.com", "db3.mysql.com"]

MYSQL_HOST = "200.21.1.161"
MYSQL_USERNAME = "root"
MYSQL_PASSWORD = "sysadmin"


def current_dir():
    return os.path.normpath(os.path.join(
        os.path.abspath(sys.argv[0]), os.pardir))


def mkdir_p(path):
    """Create a mkdir -p method"""
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def setup_logging(log_path, debug=False, verbose=False,
                  log_name="mysql_recovery"):
    """Set up global logs

    By default, script will create a log directory in the same path
    with the script. Or you can specify the directory yourself.

    To use logging in this code in anywhere, just import logging.

    """

    if log_path is None:
        log_path = os.path.join(current_dir(), "log")

    if not os.path.exists(log_path):
        mkdir_p(log_path)

    # Default log settings
    log_format = "%(asctime)s %(process)s %(levelname)s [-] %(message)s"
    log_level = logging.INFO

    if debug:
        log_level = logging.DEBUG
        log_file = os.path.join(log_path, "%s.debug.log" % log_name)
    else:
        log_file = os.path.join(log_path, "%s.log" % log_name)

    # As conflict with logging, we should define a different handler
    logger = logging.getLogger(__name__)

    if verbose:
        st_handler = logging.StreamHandler()
        st_handler.setLevel(log_level)
        st_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(st_handler)
    else:
        fh_handler = logging.FileHandler(log_file)
        fh_handler.setLevel(log_level)
        fh_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(fh_handler)

    return logger


class SaltClient(object):
    """Salt client wrapper, all salt related methods"""

    def __init__(self):
        self._local_client = salt.client.LocalClient()

    def check_hosts_up(self, check_hosts):
        """Use salt test.ping to check all hosts is up"""

        cmd_ret = self._local_client.cmd(check_hosts,
                "test.ping", expr_form="list")
        logger.debug("Test.ping returns: %s", cmd_ret)

        if len(cmd_ret) < len(check_hosts):
            return False

        is_up = True
        for host in cmd_ret:
            status = cmd_ret[host]
            logger.info("Host %s status is %s" % (host, status))
            if not status:
                logger.warning("Host %s is not up" % (host, status))
                is_up = False

        return is_up

    def start_service(self, hosts, service_name):
        """Use service command to start specific service"""

        ret = self._local_client.cmd(hosts, "service.start",
                [service_name], expr_form="list")
        logger.debug("Service %s start returns: %s", service_name, ret)

        return ret

    def stop_service(self, hosts, service_name):
        """Use service command to stop specific service"""

        ret = self._local_client.cmd(hosts, "service.stop",
                [service_name], expr_form="list")
        logger.info("Service %s stop returns: %s", service_name, ret)

        return ret

    def find_service(self, hosts, service_name):
        """Use ps and grep to verify service is running"""

        ret = self._local_client.cmd(hosts, "ps.pgrep",
                [service_name], expr_form="list")
        logger.info("Find service %s returns: %s", service_name, ret)
        return ret

    def kill_service(self, hosts, service_name):
        """Run kill -9 to stop service"""

        ret = self._local_client.cmd(hosts, "ps.pkill",
                [service_name, "signal=9"], expr_form="list")
        logger.info("Try to kill %s returns: %s", service_name, ret)
        return ret

    def cmd_run(self, hosts, cmd_str):
        """Wrapper for salt cmd.run"""

        ret = self._local_client.cmd(hosts, "cmd.run",
                [cmd_str], expr_form="list")
        logger.info("Command %s run returns: %s", cmd_str, ret)
        return ret

    def file_sed(self, hostname, path, old_str, new_str):
        ret = self._local_client.cmd(hostname, "file.sed",
                [path, old_str, new_str])
        logger.info("File sed on host %s returns: %s", hostname, ret)

class MySQLCluster(object):
    """Handle MySQL Cluster operations"""

    def __init__(self, hosts):
        self._salt_client = SaltClient()
        self._hosts = hosts
        self._service_name = "mysql"

    def is_cluster_hosts_up(self):
        return self._salt_client.check_hosts_up(self._hosts)

    def stop_cluster(self):
        """Stop mysql cluster"""

        # NOTE(Ray): Sometimes systemctl stop command runs very slow, so
        # we just kill mysql service directly. Remove this part.
        # Gracefully shutdown mysql service
        #stop_ret = self._salt_client.stop_service(
        #        self._hosts, self._service_name)
        #for host in stop_ret:
        #    status = stop_ret[host]
        #    logger.info("Current host %s service %s status is %s",
        #            host, self._service_name, status)

        # Verify if mysql stopped
        stop_succ = True
        find_ret = self._salt_client.find_service(
                self._hosts, self._service_name)
        for host in find_ret:
            pids = find_ret[host]
            if pids is not None:
                logger.warning("Host %s service %s pids: %s",
                        host, self._service_name, pids)
                stop_succ = False
                break

        # Force shutdown mysql service
        if not stop_succ:
            self._salt_client.kill_service(
                    self._hosts, self._service_name)

    def start_cluster(self):
        """Start mysql cluster"""

        bootstrap_hostname = self._get_bootstrap_node_by_wsrep()
        logger.info("Current bootstrap host is %s", bootstrap_hostname)

        if bootstrap_hostname:
            slave_hosts = HA_HOSTS[:]
            slave_hosts.remove(bootstrap_hostname)
            logger.info("Slave hosts are %s", slave_hosts)

            self._update_bootstrap_sign(bootstrap_hostname)
            self._salt_client.start_service([bootstrap_hostname],
                                            "mysql@bootstrap")
            for host in slave_hosts:
                self._salt_client.start_service(host, "mysql")

    def _get_bootstrap_node_by_wsrep(self):
        """Run wsrep-recover command to find bootstrap node

        Recommendation method according to offical document
        """
        cmd_str = "mysqld_safe --wsrep-recover"
        cmd_ret = self._salt_client.cmd_run(self._hosts, cmd_str)

        max_recovered_pos = -1
        max_hostname = None
        for host in cmd_ret:
            content = cmd_ret[host]
            recovered_pos = int(self._get_recovered_pos(content))
            logger.info("Host %s recovered position is %s",
                    host, recovered_pos)
            if recovered_pos > max_recovered_pos:
                max_recovered_pos = recovered_pos
                max_hostname = host

        return max_hostname

    def _get_seqno(self, content):
        # seqno:   -1
        m = re.search("seqno\:\s*(.+)", content)
        return m.group(1)

    def _get_recovered_pos(self, content):
        """Parser mysqld_safe --wsrep-recover"""
        # For mysqld started
        # mysqld_safe A mysqld process already exists
        m = re.search("mysqld_safe A mysqld process already exists", content)
        if m is not None:
            return -1

        # For mysql already started
        # Assigning 63120109-2a96-11e7-af57-f2c70dc56080:2264 to wsrep_start_position
        m = re.search("Assigning.*\:(\d+)", content)
        if m is not None:
            return m.group(1)

        # For mysql is not started
        # Recovered position 63120109-2a96-11e7-af57-f2c70dc56080:2277
        m = re.search("WSREP: Recovered position.*\:(\d+)", content)
        if m is not None:
            return m.group(1)

    def _get_bootstrap_node_by_grastate():
        """Get bootstrap node by parsing grastate.data

        NOTE(Ray): This is not correct during force shutdown instance,
        DO NOT use for forcing poweroff case, just keep this method for
        future function.
        """

        cmd_str = "cat /var/lib/mysql/grastate.dat"
        cmd_ret = self._salt_client.cmd_run(self._hosts, cmd_str)

        max_seqno = -1
        max_hostname = None
        for host in cmd_ret:
           content = cmd_ret[host]
           seqno = int(self._get_seqno(content))
           logger.info("Host %s seqno is %s", host, seqno)
           if seqno > max_seqno:
               max_seqno = seqno
               max_hostname = host

        if max_seqno == -1:
            logger.warning("MySQL is running normally, exiting...")
            sys.exit(0)
        else:
            return max_hostname

    def _update_bootstrap_sign(self, hostname):
        """Set bootstrap to 1 in /var/lib/mysql/grastate.dat

        safe_to_bootstrap: 0
        """

        path = "/var/lib/mysql/grastate.dat"
        old_str = "safe_to_bootstrap: 0"
        new_str = "safe_to_bootstrap: 1"
        cmd_ret = self._salt_client.file_sed(hostname, path,
                old_str, new_str)
        logger.debug("Run file.sed returns: %s", cmd_ret)

if __name__ == "__main__":
    logger = setup_logging(None, True, True)
    mysql_cluster = MySQLCluster(HA_HOSTS)
    is_up = mysql_cluster.is_cluster_hosts_up()

    if is_up:
        logger.info("Host is all up, starting to recover cluster...")

        logger.info("Stopping all mysql services...")
        mysql_cluster.stop_cluster()

        logger.info("Starting mysql cluster...")
        mysql_cluster.start_cluster()
    else:
        logger.error("Host is not all up, exiting...")
        sys.exit(1)
