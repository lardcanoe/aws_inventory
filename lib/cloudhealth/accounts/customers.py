#!/usr/bin/env python

import sys
import os
import argparse
import pymongo
from pymongo import MongoClient
import datetime

from customer import Customer

class Customers(object):
	def __init__(self):
		self.__setup_db();

	def __setup_db(self):
		self.mongo = MongoClient('localhost', 27017)
		self.cloudhealth = self.mongo['cloudhealth']
		if 'customers' not in self.cloudhealth.collection_names():
			self.cloudhealth.create_collection('customers')

	def find(self):
		for c in self.cloudhealth.customers.find():
			yield Customer(c)
