#!/usr/bin/env python
#===============================================================================
#
#          FILE: get_redis_stats.py
# 
#         USAGE: ./get_redis_stats.py instance metric
# 
#   DESCRIPTION: 
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: Anton Soroko (anton.soroko@gmail.com) 
#  ORGANIZATION: 
#       CREATED: 09.09.2016 13:51:48 MSK
#      REVISION:  ---
#===============================================================================

import os
import glob
import json
import subprocess
import sys
import time


METRICS = {}
CACHE_TTL = 55

def execute(command, stdin=None):
    child = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    output = child.communicate(input=stdin)[0]
    return child.returncode, output

def discovery():
    output = {'data':[]}
    for file in glob.glob("/var/vcap/store/cf-redis-broker/redis-data/*/redis.conf"):
        name = os.path.basename(os.path.dirname(file))
        with open(file, "r") as fd:
            content = fd.readlines()
        for line in content:
            if line.startswith("port "):
                port = line.replace("port ", "").strip()
            #elif line.startswith("syslog-ident "):
            #    name = line.replace("syslog-ident redis-server-", "").strip()
        output['data'].append({ '{#REDISNAME}': name, '{#REDISPORT}': port })
    print json.dumps(output, indent=4)

def get_metric(metric_name):
    return METRICS[metric_name]

def get_info(redis_instance):
    directory="/var/vcap/data/sys/run/zabbix_agentd"
    if not os.path.exists(directory):
        os.makedirs(directory)
    cache_file = os.path.join(directory, "redis-status-{}".format(redis_instance))
    cache_expired = True
    if os.access(cache_file, os.R_OK + os.W_OK):
        cache_file_stat = os.stat(cache_file)
        if cache_file_stat.st_size != 0 and time.time() - cache_file_stat.st_mtime < CACHE_TTL:
            with open(cache_file, 'r') as fd:
                rc, output = 0, fd.read()
            cache_expired = False
    if cache_expired:
        redis_config = "/var/vcap/store/cf-redis-broker/redis-data/{}/redis.conf".format(redis_instance)
        with open(redis_config, 'r') as fd:
            content = fd.readlines()
        for line in content:
            if line.startswith("port "):
                port = line.replace("port ", "").strip()
            elif line.startswith("requirepass "):
                password = line.replace("requirepass ", "").strip()
        rc, output = execute("/var/vcap/packages/redis/bin/redis-cli -p {port} -a {password} INFO".format(port=port, password=password))
        with open(cache_file, 'w') as fd:
            fd.write(output)
    if rc == 0:
        for line in output.splitlines():
            if not line.startswith("#") and ':' in line:
                key, value = (val.strip() for val in line.split(':', 1))
                METRICS[key] = value
    else:
        sys.exit(1)

def main():
    command = sys.argv[1]
    if command == "discovery":
        discovery()
        sys.exit(0)
    elif command == "metric":
        redis_instance = sys.argv[2]
        metric_name = sys.argv[3]
        get_info(redis_instance)
        print get_metric(metric_name)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
