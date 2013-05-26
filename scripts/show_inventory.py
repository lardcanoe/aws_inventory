#!/usr/bin/env python

import sys
import os
import argparse
import string
import itertools

sys.path.append('../lib')
import cloudhealth
from cloudhealth import providers
from cloudhealth import accounts
from cloudhealth import inventory

class ShowInventoryCli(object):

	def __init__(self):
		self.parse_cli_args()

	def parse_cli_args(self):
		''' Command line argument processing '''

		parser = argparse.ArgumentParser(
			description='Produce an inventory list based on cached EC2 data',
			prog='Cached Inventory')
		parser.add_argument('--verbose', '-v', action='count')
		parser.add_argument('--version', action='version', version='%(prog)s 2.0')
		parser.add_argument('--customer', '-c', required = True)
		parser.add_argument('--hide-header', action = 'store_true', default = False)
		parser.add_argument('--type', choices=['instances', 'volumes', 'snapshots'], required=True)
		parser.add_argument('--source', '-s', choices=['cache', 'provider'], default = 'cache')
		self.args = parser.parse_args()

	def go(self):

		self.customer = self.find_customer();
		if self.customer == None:
			print 'Customer not found'
			sys.exit(1)

		self.display_header()

		if self.args.source == 'cache':
			self.show_from_cache()
		elif self.args.source == 'provider':
			self.show_from_provider()

	def display_header(self):
		if self.args.hide_header:
			return

		if self.args.type == 'instances':
			print 'Instance', '   Region', '      State'
		elif self.args.type == 'volumes':
			print 'Volume      ', 'Instance  ', ' Region', '    State', '     Device'
		elif self.args.type == 'snapshots':
			print 'Volume       ', 'Instance   ', ' Region    ', '    State', '    Size(GB)'

	def show_from_cache(self):
		cache = inventory.CachedInventory()

		if self.args.type == 'instances':
			for inst in cache.instances(self.customer):
				print inst['_id'], string.rjust(inst['region'], 10), string.rjust(inst['state'], 10)
		elif self.args.type == 'volumes':
			for vol in cache.volumes(self.customer):
				print vol['_id'], vol['instance_id'], string.rjust(vol['region'], 10), string.rjust(vol['status'], 10), string.rjust(vol['device'], 10)
		elif self.args.type == 'snapshots':
			for snap in cache.snapshots(self.customer).limit(10):
				print "%s %s %s %s %s" % (
					snap['_id'],
					snap['volume_id'],
					snap['region'],
					snap['status'],
					snap['volume_size'],
				) 
				#snap['_id'], string.rjust(snap['region'], 10), string.rjust(snap['state'], 10)

	def show_from_provider(self):
		if 'EC2_SECRET_KEY' not in os.environ:
			print 'Missing EC2_SECRET_KEY environ var'
			sys.exit(1)
		if 'EC2_ACCESS_KEY' not in os.environ:
			print 'Missing EC2_ACCESS_KEY environ var'
			sys.exit(1)

		ec2_access_key = os.environ['EC2_ACCESS_KEY']
		ec2_secret_key = os.environ['EC2_SECRET_KEY']

		for cp in self.customer.cloud_providers().find():
			if cp.provider_type == 'ec2':
				inv = providers.Ec2Inventory(ec2_access_key, ec2_secret_key)
				if self.args.type == 'instances':
					for inst in inv.instances():
						print inst.id, string.rjust(inst.region.name, 10), string.rjust(inst.state, 10)
				elif self.args.type == 'volumes':
					for vol in inv.volumes():
						if vol.attachment_state() == 'attached':
							instance_id = vol.attach_data.instance_id
							device = vol.attach_data.device
						else:
							instance_id = '          '
							device = ''
						print "%s %s %s %s %s" % (
							vol.id, 
							instance_id, 
							string.rjust(vol.region.name, 10), 
							string.rjust(vol.status, 10), 
							string.rjust(device, 10)
						)
				elif self.args.type == 'snapshots':
					#for snap in itertools.islice(inv.snapshots(), 0, 15):
					for snap in inv.snapshots():
						print "%s %s %s %s %s" % (
							snap.id,
							snap.volume_id,
							snap.region.name,
							snap.status,
							snap.volume_size,
						)
	def find_customer(self):
		customers = accounts.Customers();
		for c in customers.find():
			if c.name.lower() == self.args.customer.lower():
				return c
		return None

if __name__ == '__main__':
	cli = ShowInventoryCli()
	cli.go()