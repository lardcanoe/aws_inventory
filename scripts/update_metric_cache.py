#!/usr/bin/env python

import sys
import os
import argparse

sys.path.append('../lib')
import cloudhealth
from cloudhealth import accounts
from cloudhealth import providers
from cloudhealth import inventory
from cloudhealth import metrics

class StoreMetricCli(object):

	def __init__(self):
		self.parse_cli_args()

	def parse_cli_args(self):
		''' Command line argument processing '''

	def go(self):

		if 'EC2_SECRET_KEY' not in os.environ:
			print 'Missing EC2_SECRET_KEY environ var'
			sys.exit(1)
		if 'EC2_ACCESS_KEY' not in os.environ:
			print 'Missing EC2_ACCESS_KEY environ var'
			sys.exit(1)

		self.ec2_access_key = os.environ['EC2_ACCESS_KEY']
		self.ec2_secret_key = os.environ['EC2_SECRET_KEY']

		cache = inventory.CachedInventory()

		customers = accounts.Customers()
		for customer in customers.find():
			for cp in customer.cloud_providers().find():
				if cp.provider_type == 'ec2':
					self.update_ec2(customer, cp)
				else:
					print 'Unimplemented Cloud Provider: ', cp.provider_type

	def update_ec2(self, customer, cp):
		inv_cache = inventory.CachedInventory()
		metric_cache = metrics.CachedMetrics()
		ec2_prov = providers.Ec2Metrics(self.ec2_access_key, self.ec2_secret_key)
		for inst in inv_cache.instances(customer):
			dps = ec2_prov.instance_cpu(inst['_id'])
			metric_cache.insert_instance_cpu(customer, inst['_id'], dps)

if __name__ == '__main__':
	cli = StoreMetricCli()
	cli.go()