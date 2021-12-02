#!/usr/bin/env python3

import os
import threading
import re
import yaml
import argparse
import requests
from requests.auth import HTTPBasicAuth
import json

class Starter:

  VERSION = '1.0'
  CL_HEADER = '\033[95m'
  CL_OKBLUE = '\033[94m'
  CL_OKCYAN = '\033[96m'
  CL_OKGREEN = '\033[92m'
  CL_WARNING = '\033[93m'
  CL_FAIL = '\033[91m'
  CL_END = '\033[0m'
  CL_BOLD = '\033[1m'
  CL_UNDERLINE = '\033[4m'
  CONF_FILE = os.getenv("CONF_FILE", "/opt/apps/conf/apps.yml")
  APP_NAME = ""

  def __init__(self):
    print(f"{self.CL_HEADER}JAVA APPLICATION LOADER ver {self.VERSION}{self.CL_END}")

  def run(self):
    print(f"Using config file: {self.CL_BOLD}{self.CONF_FILE}{self.CL_END}")
    print(f"Application for starting up: {self.CL_BOLD}{self.APP_NAME}{self.CL_END}")
    self.load_config()
    if self.APP_NAME not in self.CONFIG['applications']:
      print(f"{self.CL_FAIL}Application {self.APP_NAME} not found in config file{self.CL_END}")
      exit(1)
    self.load_common_variables()
    self.load_specific_variables()
    if self.CONFIG['common_vars']['hdfs_address'] == "auto":
      self.detect_hdfs_master()
    self.start_app()

  def load_config(self):
    with open(self.CONF_FILE, 'r') as stream:
      self.CONFIG = yaml.safe_load(stream)

  def start_app(self):
    jar_file = self.CONFIG['applications'][self.APP_NAME]['starter']['location']
    print(f"{self.CL_HEADER}=== STARTING APPLICATION {jar_file} ==={self.CL_END}")
    self.BASE_DIR = os.path.dirname(jar_file)
    self.BASE_NAME = os.path.basename(jar_file)
    os.chdir(self.BASE_DIR)
    #instance_count = 1
    for instance in self.CONFIG['applications'][self.APP_NAME]['starter']['instances']:
      print(instance)
      heap_size = self.CONFIG['applications'][self.APP_NAME]['starter']['heap_size']
      print(f"Starting instance %s of %s" % (instance['name'], self.APP_NAME))
      x = threading.Thread(target=self.thread_function, args=(instance['name'], str(instance['port']), str(heap_size), ))
      x.start()

  def thread_function(self, instance_name, instance_port, instance_heap):
    print("Starting thread %s" % instance_name)
    os.system(f"java -Xmx{instance_heap} -jar -Dserver.port={instance_port} -Dinstance.name={instance_name} {self.BASE_NAME}")

  def load_specific_variables(self):
    print(f"{self.CL_HEADER}=== LOAD SPECIFIC VARIABLES ==={self.CL_END}")
    base_cnf = self.CONFIG['applications'][self.APP_NAME]
    if 'variables' not in base_cnf:
      print("Specific variables are absent\n")
      return
    for vr in dict.keys(base_cnf['variables']):
      val = ""
      if str(base_cnf['variables'][vr]) != "None":
        val = str(base_cnf['variables'][vr])
      os.environ[vr] = val
      print(f"Load {self.CL_OKGREEN}%s = %s{self.CL_END}" % (str(vr), str(val)))
    print("")

  def load_common_variables(self):
    print(f"{self.CL_HEADER}=== LOAD COMMON VARIABLES ==={self.CL_END}")
    for vr in dict.keys(self.CONFIG['common_vars']):
      val = ""
      if str(self.CONFIG['common_vars'][vr]) != "None":
        val = str(self.CONFIG['common_vars'][vr])
      os.environ[vr] = val
      print(f"Load {self.CL_OKGREEN}%s = %s{self.CL_END}" % (str(vr), str(val)))
    print("")

  def detect_hdfs_master(self):
    print(f"{self.CL_HEADER}=== DETECT HDFS MASTER ==={self.CL_END}")
    if 'starter_ambari_url' not in self.CONFIG['common_vars']:
      print("Does not exists variable starter_ambari_url when hdfs master autodetect is enabled")
      exit(1)
    uri = f"{self.CONFIG['common_vars']['starter_ambari_url']}/host_components?HostRoles/component_name=NAMENODE&metrics/dfs/FSNamesystem/HAState=active"
    r = requests.get(uri, auth=HTTPBasicAuth(self.CONFIG['common_vars']['starter_ambari_user'], self.CONFIG['common_vars']['starter_ambari_password']))
    out = json.loads(r.text)
    if 'status' in out:
      print(f"Status of your request is {out['status']}: {out['message']}")
      exit(1)
    self.HDFS_MASTER_NODE=f"hdfs://{out['items'][0]['HostRoles']['host_name']}:8020"
    os.environ['hdfs_address'] = self.HDFS_MASTER_NODE
    print(f"{self.CL_OKGREEN}HDFS master node variable set: {self.HDFS_MASTER_NODE}{self.CL_END}")
    print("")

if __name__ == '__main__':
  st = Starter()
  argp = argparse.ArgumentParser(description = 'Luxoft application starter')
  argp.add_argument("--configfile", "-c", default = st.CONF_FILE, help="custom path to config file, default " + st.CONF_FILE)
  argp.add_argument("--application", "-a", required = True, help="Application name from config file")
  args = argp.parse_args()
  st.APP_NAME = args.application
  st.CONF_FILE = args.configfile
  st.run()
