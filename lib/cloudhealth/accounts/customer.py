#!/usr/bin/env python

import sys
import os
import argparse
import pymongo
from pymongo import MongoClient
import datetime

class Customer(object):
	def __init__(self, dictFromDb):
		self.my_dict = dictFromDb;

	def __getattr__(self, name):
		return self.my_dict[name]

	def Id(self):
		return self.my_dict['_id']