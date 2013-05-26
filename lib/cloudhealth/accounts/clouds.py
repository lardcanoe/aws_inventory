#!/usr/bin/env python

import sys
import os
import argparse
import pymongo
from pymongo import MongoClient
import datetime

#from customer import Customer

class CloudProvider(object):
	def __init__(self, dictFromDb):
		self.my_dict = dictFromDb;

	def __getattr__(self, name):
		if name == 'id':
			name = '_id'
		return self.my_dict[name]

	def Id(self):
		return self.my_dict['_id']

class CloudProviders(object):
	def __init__(self, customer):
		self.customer = customer
		self.__setup_db()

	def __setup_db(self):
		self.mongo = MongoClient('localhost', 27017)
		self.cloudhealth = self.mongo['cloudhealth']
		if 'providers' not in self.cloudhealth.collection_names():
			self.cloudhealth.create_collection('providers')

	def find(self):
		query = {
			'customer_id': self.customer.id
		}
		for p in self.cloudhealth.providers.find(query):
			yield CloudProvider(p)
