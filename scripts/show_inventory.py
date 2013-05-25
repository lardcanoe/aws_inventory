#!/usr/bin/env python

import sys
import os
import argparse

sys.path.append('../lib')
import cloudhealth
from cloudhealth import inventory
from cloudhealth.inventory import ec2

class ShowInventoryCli(object):

	def __init__(self):
		self.parse_cli_args()

	def parse_cli_args(self):
		''' Command line argument processing '''

		parser = argparse.ArgumentParser(description='Produce an Inventory file based on EC2')
		parser.add_argument('--list', action='store_true', default=True,
		help='List instances (default: True)')
		self.args = parser.parse_args()

	def go(self):

		if 'EC2_SECRET_KEY' not in os.environ:
			print 'Missing EC2_SECRET_KEY environ var'
			sys.exit(1)
		if 'EC2_ACCESS_KEY' not in os.environ:
			print 'Missing EC2_ACCESS_KEY environ var'
			sys.exit(1)

		ec2_access_key = os.environ['EC2_ACCESS_KEY']
		ec2_secret_key = os.environ['EC2_SECRET_KEY']

		inv = ec2.Ec2Inventory(ec2_access_key, ec2_secret_key)
		for inst in inv.instances():
			print inst.id, ':', inst.state
		#for inst in inv.rds_instances():
		#	print inst

if __name__ == '__main__':
	cli = ShowInventoryCli()
	cli.go()