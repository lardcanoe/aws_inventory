#!/usr/bin/env python

import sys
import os
import argparse
import pymongo
from pymongo import MongoClient
import datetime

class CachedInventory(object):
	def __init__(self):
		self.__setup_db()

	def __setup_db(self):
		self.mongo = MongoClient('localhost', 27017)
		self.cloudhealth = self.mongo['cloudhealth']
		if 'inventory' not in self.cloudhealth.collection_names():
			self.cloudhealth.create_collection('inventory')

	def update_instance(self, customer, instance):
		inst_json = self.__inst_to_json(customer, instance)
		self.cloudhealth.inventory.insert(inst_json)

	def __inst_to_json(self, customer, instance):
		inst_json = {
			'customer_id': customer.Id(),
			'_id': instance.id,
			'state': instance.state
		}
		return inst_json