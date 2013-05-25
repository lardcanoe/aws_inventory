#!/usr/bin/env python

import sys
import os
import argparse
import pymongo
from pymongo import MongoClient
#from bson.objectid import ObjectId
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
		self.cloudhealth.inventory.update(
			{ '_id': instance.id },
			{ '$set': inst_json },
			upsert = True
		)

	def __inst_to_json(self, customer, instance):
		inst_json = {
			'last_update_ts': datetime.datetime.utcnow(),
			'customer_id': customer.Id(),
			'state': instance.state
		}
		return inst_json