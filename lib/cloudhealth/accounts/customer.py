#!/usr/bin/env python

import sys
import os
import argparse
import pymongo
from pymongo import MongoClient
import datetime

from clouds import CloudProviders

class Customer(object):
	def __init__(self, dictFromDb):
		self.my_dict = dictFromDb;

	def __getattr__(self, name):
		if name == 'id':
			name = '_id'
		return self.my_dict[name]

	def Id(self):
		return self.my_dict['_id']

	def add_cloud_provider(self, provider_type):
		mongo = MongoClient('localhost', 27017)
		cloudhealth = mongo['cloudhealth']		
		cloudhealth.providers.insert(
			{
				'customer_id': self.id,
				'provider_type': provider_type,
				'created_ts': datetime.datetime.utcnow()
			}
		)

	def cloud_providers(self):
		return CloudProviders(self)
