#!/usr/bin/env python

import sys
import os
import re
from time import time
import boto
from boto import ec2
from boto.ec2 import cloudwatch
from boto import rds
import ConfigParser
import datetime

try:
    import json
except ImportError:
    import simplejson as json


class Ec2Inventory(object):
    def __init__(self, ec2_access_key, ec2_secret_key, region = 'all'):
        ''' Main execution path '''

        self.selected_region = region

        self.ec2_access_key = ec2_access_key
        self.ec2_secret_key = ec2_secret_key

        # Inventory grouped by instance IDs, tags, security groups, regions,
        # and availability zones
        self.inventory = {}

        # Index of hostname (address) to instance ID
        self.index = {}

        self.region_connections = {}

        # Read settings and parse CLI arguments
        self.__read_settings()

    def instances(self):
        ''' Do API calls to each region '''

        for region in self.regions:
            for inst in self.__get_instances_by_region(region):
                yield inst

    def volumes(self):
        ''' Do API calls to each region '''

        for region in self.regions:
            for vol in self.__get_volumes_by_region(region):
                yield vol

    def snapshots(self):
        ''' Do API calls to each region '''

        for region in self.regions:
            for s in self.__get_snapshots_by_region(region):
                yield s

    def rds_instances(self):
        ''' Do API calls to each region '''

        for region in self.regions:
            for inst in self.__get_rds_instances_by_region(region):
                yield inst

    def __read_settings(self):
        ''' Reads the settings from the ec2.ini file '''

        self.regions = []

        self.config_file = os.path.dirname(os.path.realpath(__file__)) + '/ec2.ini'
        if (not os.path.exists(self.config_file)):
            configRegions = self.selected_region
            self.destination_variable = 'public_dns_name'
            self.vpc_destination_variable = 'ip_address'
        else:
            config = ConfigParser.SafeConfigParser()
            config.read(self.config_file)
            configRegions = config.get('ec2', 'regions')
            self.destination_variable = config.get('ec2', 'destination_variable')
            self.vpc_destination_variable = config.get('ec2', 'vpc_destination_variable')        

        # Regions
        if (configRegions == 'all'):
            for regionInfo in ec2.regions():
                self.regions.append(regionInfo.name)
        else:
            self.regions = configRegions.split(",")

    def __get_connection(self, region):
        ''' Creates EC2 connection to a region and caches it '''

        if not region in self.region_connections:
            self.region_connections[region] = ec2.connect_to_region(region, aws_access_key_id=self.ec2_access_key, aws_secret_access_key=self.ec2_secret_key)

        return self.region_connections[region]

    def __get_instances_by_region(self, region):
        ''' Makes an AWS EC2 API call to the list of instances in a particular
        region '''

        try:
            conn = self.__get_connection(region)
            
            if conn:
                reservations = conn.get_all_instances()
                for reservation in reservations:
                    for instance in reservation.instances:
                        yield instance

        except boto.exception.BotoServerError as e:
            print "BotoServerError: "
            print e
            sys.exit(1)

    def __get_volumes_by_region(self, region):
        ''' Makes an AWS EC2 API call to the list of volumes in a particular
        region '''

        try:
            conn = self.__get_connection(region)
            
            if conn:
                for vol in conn.get_all_volumes():
                    yield vol

        except boto.exception.BotoServerError as e:
            print "BotoServerError: "
            print e
            sys.exit(1)

    def __get_snapshots_by_region(self, region):
        ''' Makes an AWS EC2 API call to the list of volumes in a particular
        region '''

        try:
            conn = self.__get_connection(region)
            
            if conn:
                for s in conn.get_all_snapshots():
                    yield s

        except boto.exception.BotoServerError as e:
            print "BotoServerError: "
            print e
            sys.exit(1)

    def __get_rds_instances_by_region(self, region):
	''' Makes an AWS API call to the list of RDS instances in a particular
        region '''

        try:
            conn = rds.connect_to_region(region, aws_access_key_id=self.ec2_access_key, aws_secret_access_key=self.ec2_secret_key)
            if conn:
                instances = conn.get_all_dbinstances()
                for instance in instances:
                    yield instance

        except boto.exception.BotoServerError as e:
            print "RDS BotoServerError: "
            print e
            sys.exit(1)

    def get_instance(self, region, instance_id):
        ''' Gets details about a specific instance '''

        conn = ec2.get_connection(region)

        reservations = conn.get_all_instances([instance_id])
        for reservation in reservations:
            for instance in reservation.instances:
                return instance

    def __add_instance(self, instance, region):
        ''' Adds an instance to the inventory and index, as long as it is
        addressable '''

        # Only want running instances
        if instance.state != 'running':
            return

        # Select the best destination address
        if instance.subnet_id:
            dest = getattr(instance, self.vpc_destination_variable)
        else:
            dest =  getattr(instance, self.destination_variable)

        if not dest:
            # Skip instances we cannot address (e.g. private VPC subnet)
            return

        # Add to index
        self.index[dest] = [region, instance.id]

        # Inventory: Group by instance ID (always a group of 1)
        self.inventory[instance.id] = [dest]

        # Inventory: Group by region
        self.__push(self.inventory, region, dest)

        # Inventory: Group by availability zone
        self.__push(self.inventory, instance.placement, dest)
        
        # Inventory: Group by instance type
        self.__push(self.inventory, self.__to_safe('type_' + instance.instance_type), dest)
        
        # Inventory: Group by key pair
        if instance.key_name:
            self.__push(self.inventory, self.__to_safe('key_' + instance.key_name), dest)
        
        # Inventory: Group by security group
        try:
            for group in instance.groups:
                key = self.__to_safe("security_group_" + group.name)
                self.__push(self.inventory, key, dest)
        except AttributeError:
            print 'Package boto seems a bit older.'
            print 'Please upgrade boto >= 2.3.0.'
            sys.exit(1)

        # Inventory: Group by tag keys
        for k, v in instance.tags.iteritems():
            key = self.__to_safe("tag_" + k + "=" + v)
            self.__push(self.inventory, key, dest)

    def __add_rds_instance(self, instance, region):
        ''' Adds an RDS instance to the inventory and index, as long as it is
        addressable '''

        # Only want available instances
        if instance.status != 'available':
            return

        # Select the best destination address
        #if instance.subnet_id:
            #dest = getattr(instance, self.vpc_destination_variable)
        #else:
            #dest =  getattr(instance, self.destination_variable)
        dest = instance.endpoint[0]

        if not dest:
            # Skip instances we cannot address (e.g. private VPC subnet)
            return

        # Add to index
        self.index[dest] = [region, instance.id]

        # Inventory: Group by instance ID (always a group of 1)
        self.inventory[instance.id] = [dest]

        # Inventory: Group by region
        self.__push(self.inventory, region, dest)

        # Inventory: Group by availability zone
        self.__push(self.inventory, instance.availability_zone, dest)
        
        # Inventory: Group by instance type
        self.__push(self.inventory, self.__to_safe('type_' + instance.instance_class), dest)
        
        # Inventory: Group by security group
        try:
            key = self.__to_safe("security_group_" + instance.security_group.name)
            self.__push(self.inventory, key, dest)
        except AttributeError:
            print 'Package boto seems a bit older.'
            print 'Please upgrade boto >= 2.3.0.'
            sys.exit(1)

        # Inventory: Group by engine
        self.__push(self.inventory, self.__to_safe("rds_" + instance.engine), dest)

        # Inventory: Group by parameter group
        self.__push(self.inventory, self.__to_safe("rds_parameter_group_" + instance.parameter_group.name), dest)

    def __get_host_info(self):
        ''' Get variables about a specific host '''

        if len(self.index) == 0:
            # Need to load index from cache
            self.load_index_from_cache()

        if not self.args.host in self.index:
            # try updating the cache
            self.do_api_calls_update_cache()
            if not self.args.host in self.index:
                # host migh not exist anymore
                return self.json_format_dict({}, True)

        (region, instance_id) = self.index[self.args.host]

        instance = self.get_instance(region, instance_id)
        instance_vars = {}
        for key in vars(instance):
            value = getattr(instance, key)
            key = self.to_safe('ec2_' + key)

            # Handle complex types
            if type(value) in [int, bool]:
                instance_vars[key] = value
            elif type(value) in [str, unicode]:
                instance_vars[key] = value.strip()
            elif type(value) == type(None):
                instance_vars[key] = ''
            elif key == 'ec2_region':
                instance_vars[key] = value.name
            elif key == 'ec2_tags':
                for k, v in value.iteritems():
                    key = self.to_safe('ec2_tag_' + k)
                    instance_vars[key] = v
            elif key == 'ec2_groups':
                group_ids = []
                group_names = []
                for group in value:
                    group_ids.append(group.id)
                    group_names.append(group.name)
                instance_vars["ec2_security_group_ids"] = ','.join(group_ids)
                instance_vars["ec2_security_group_names"] = ','.join(group_names)
            else:
                pass
                # TODO Product codes if someone finds them useful
                #print key
                #print type(value)
                #print value

        return self.json_format_dict(instance_vars, True)

    def __push(self, my_dict, key, element):
        ''' Pushed an element onto an array that may not have been defined in
        the dict '''

        if key in my_dict:
            my_dict[key].append(element);
        else:
            my_dict[key] = [element]

    def __to_safe(self, word):
        ''' Converts 'bad' characters in a string to underscores so they can be
        used as Ansible groups '''

        return re.sub("[^A-Za-z0-9\-]", "_", word)

    def __json_format_dict(self, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted
        string '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

class Ec2Metrics(object):
    def __init__(self, ec2_access_key, ec2_secret_key):
        self.ec2_access_key = ec2_access_key
        self.ec2_secret_key = ec2_secret_key
        self.cwc = cloudwatch.CloudWatchConnection(aws_access_key_id=self.ec2_access_key, aws_secret_access_key=self.ec2_secret_key)

    def instance_cpu(self, instance_id):
        #end = datetime.datetime.utcnow()
        end = datetime.datetime.utcnow() - datetime.timedelta(minutes=15)
        start = end - datetime.timedelta(minutes=15)
        statistics = ['Average', 'Sum', 'Maximum', 'Minimum']
        metric_name = 'CPUUtilization'
        namespace = 'AWS/EC2'
        unit = 'Percent'
        dimensions = {
            'InstanceId': [instance_id]
        }
        return self.cwc.get_metric_statistics(
            60,
            start,
            end,
            metric_name,
            namespace,
            statistics,
            dimensions,
            unit
        )