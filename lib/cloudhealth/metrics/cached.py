#!/usr/bin/env python

import sys
import os
import argparse
import pymongo
from pymongo import MongoClient
#from bson.objectid import ObjectId
import datetime

class CachedMetrics(object):
	def __init__(self):
		self.__setup_db()

	def __setup_db(self):
		self.mongo = MongoClient('localhost', 27017)
		self.cloudhealth = self.mongo['cloudhealth']
		if 'metrics' not in self.cloudhealth.collection_names():
			self.cloudhealth.create_collection('metrics')

	def instance_cpu(self, instance_id):
		query = {
			'assett_type': 'ec2_instance_cpu',
			'instance_id': instance_id,
		}
		return self.cloudhealth.metrics.find(query).sort([('Timestamp', pymongo.ASCENDING)])

	def insert_instance_cpu(self, customer_id, instance_id, metrics):
		x = 0
		for m in metrics:
			m['instance_id'] = instance_id
			m['customer_id'] = customer_id
			self.cloudhealth.metrics.insert(
				m
			)
			x += 1
		return x

