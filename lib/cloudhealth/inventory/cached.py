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

	def instances(self, customer):
		query = {
			'assett_type': 'ec2_instance',
			'customer_id': customer.Id(),
		}
		return self.cloudhealth.inventory.find(query)

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
			'assett_type': 'ec2_instance',
			'customer_id': customer.Id(),
			'state': instance.state,
			'region': instance.region.name,
		}
		return inst_json

	def volumes(self, customer):
		query = {
			'assett_type': 'ec2_volume',
			'customer_id': customer.Id(),
		}
		return self.cloudhealth.inventory.find(query)

	def update_volume(self, customer, volume):
		volume_json = self.__volume_to_json(customer, volume)
		self.cloudhealth.inventory.update(
			{ '_id': volume.id },
			{ '$set': volume_json },
			upsert = True
		)

	def __volume_to_json(self, customer, volume):
		volume_json = {
			'last_update_ts': datetime.datetime.utcnow(),
			'assett_type': 'ec2_volume',
			'customer_id': customer.Id(),
			'status': volume.status,
			'region': volume.region.name,
			'attachment_state': volume.attachment_state(),
			'device': '',
			'instance_id': '',
		}

		if volume.attachment_state() == 'attached':
			volume_json['device'] = volume.attach_data.device
			volume_json['instance_id'] = volume.attach_data.instance_id

		return volume_json

	def snapshots(self, customer):
		query = {
			'assett_type': 'ec2_snapshot',
			'customer_id': customer.Id(),
		}
		return self.cloudhealth.inventory.find(query)

	def update_snapshot(self, customer, snapshot):
		snapshot_json = self.__snapshot_to_json(customer, snapshot)
		self.cloudhealth.inventory.update(
			{ '_id': snapshot.id },
			{ '$set': snapshot_json },
			upsert = True
		)

	def __snapshot_to_json(self, customer, snapshot):
		snapshot_json = {
			'last_update_ts': datetime.datetime.utcnow(),
			'assett_type': 'ec2_snapshot',
			'customer_id': customer.Id(),
			'volume_id': snapshot.volume_id,
			'volume_size': snapshot.volume_size,
			'status': snapshot.status,
			'region': snapshot.region.name,
		}
		return snapshot_json