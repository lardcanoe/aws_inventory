#!/usr/bin/env python

import sys
import os
import argparse
#from threading import Thread
import multiprocessing
import signal
import time

#print os.path.abspath(os.path.dirname(sys.argv[0]))
#print os.path.abspath(__path__)

sys.path.append(os.path.abspath(os.path.dirname(sys.argv[0])) + '/../lib')
import cloudhealth
from cloudhealth import accounts
from cloudhealth import providers
from cloudhealth import inventory
from cloudhealth import metrics

def run_worker(id):
	try:
		print 'Spawning Worker: ', id, os.getpid()
		w = metrics.MetricQueueWorker(id)
		w.go();
		print 'Exitting Worker: ', id, os.getpid()
	except:
		print "[run_worker] Unexpected error:", sys.exc_info()[0]

class StoreMetricCli(object):

	def __init__(self):
		self.parse_cli_args()

	def parse_cli_args(self):
		''' Command line argument processing '''
		parser = argparse.ArgumentParser(prog='Update Metrics')
		parser.add_argument('--version', action='version', version='%(prog)s 2.0')

		#Display Options
		parser.add_argument('--verbose', '-v', action='count')

		#Options
		parser.add_argument('--worker-count', '-w', type=int, choices=range(1, 5), default=1)

		self.args = parser.parse_args()

	def go(self):

		pool = multiprocessing.Pool(self.args.worker_count, self.init_worker)
		for i in range(self.args.worker_count):
			pool.apply_async(run_worker, args=(i+1,))

		try:
			pool.close()

			self.add_assetts_to_queue()

			pool.join()
		except KeyboardInterrupt:
			print "Caught KeyboardInterrupt, terminating workers"
			pool.terminate()

	def init_worker(self):
		signal.signal(signal.SIGINT, signal.SIG_IGN)

	def add_assetts_to_queue(self):
		customers = accounts.Customers()
		for customer in customers.find():
			for cp in customer.cloud_providers().find():
				if cp.provider_type == 'ec2':
					self.add_ec2_to_queue(customer)
				else:
					print 'Unimplemented Cloud Provider: ', cp.provider_type

	def add_ec2_to_queue(self, customer):
		qc = metrics.MetricQueueClient()
		inv_cache = inventory.CachedInventory()
		for inst in inv_cache.instances(customer):
			qc.insert(customer, inst['_id'])
			qc.insert(customer, inst['_id'])
			qc.insert(customer, inst['_id'])
			qc.insert(customer, inst['_id'])
			qc.insert(customer, inst['_id'])

if __name__ == '__main__':
	cli = StoreMetricCli()
	cli.go()