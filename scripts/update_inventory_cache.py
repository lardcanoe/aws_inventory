#!/usr/bin/env python

import sys
import os
import argparse

sys.path.append(os.path.abspath(os.path.dirname(sys.argv[0])) + '/../lib')
import cloudhealth
from cloudhealth import accounts
from cloudhealth import providers
from cloudhealth import inventory

class StoreInventoryCli(object):

	def __init__(self):
		self.parse_cli_args()

	def parse_cli_args(self):
		''' Command line argument processing '''

		parser = argparse.ArgumentParser(description='Produce an Inventory file based on EC2')
		parser.add_argument('--list', action='store_true', default=True,
			help='List instances (default: True)')
		self.args = parser.parse_args()

	def go(self):

		if 'AWS_SECRET_KEY' not in os.environ:
			print 'Missing AWS_SECRET_KEY environ var'
			sys.exit(1)
		if 'AWS_ACCESS_KEY' not in os.environ:
			print 'Missing AWS_ACCESS_KEY environ var'
			sys.exit(1)

		ec2_access_key = os.environ['AWS_ACCESS_KEY']
		ec2_secret_key = os.environ['AWS_SECRET_KEY']

		cache = inventory.CachedInventory()

		customers = accounts.Customers()
		for customer in customers.find():
			for cp in customer.cloud_providers().find():
				if cp.provider_type == 'ec2':
					#customer.add_cloud_provider('ec2')
					inv = providers.Ec2Inventory(ec2_access_key, ec2_secret_key)
					for inst in inv.instances():
						cache.update_instance(customer, inst)
						print customer.name, ':Instance:', inst.id, ':', inst.state
					for vol in inv.volumes():
						cache.update_volume(customer, vol)
						print customer.name, ':Volume:', vol.id, ':', vol.status
					snap_count = 0
					for snap in inv.snapshots():
						cache.update_snapshot(customer, snap)
						snap_count += 1
						#print customer.name, ':Snapshot:', snap.id, ':', snap.status, ':', snap.volume_id
					print customer.name, ':Snapshots:', snap_count
				else:
					print 'Unimplemented Cloud Provider: ', cp.provider_type

		#TODO: Mark all cached instances that are not in EC2 as terminated
		#for inst in inv.rds_instances():
		#	print inst

if __name__ == '__main__':
	cli = StoreInventoryCli()
	cli.go()