## This is a project with JAVA application starter  

Usage:  
```
starter.py -a appname 
```

By default starter try to open config file from /opt/apps/conf/apps.yml  
You can define path to config file by environment variable:  
CONFIG_FILE=/path/to/config.yml  

Example of configuration file you can see in apps-example.yml file  

If your application needs hdfs access, starter can detect current master node in HA cluster  
and will set environment variable hdfs_address with active master address.  

Thats all.  
Good luck ) 