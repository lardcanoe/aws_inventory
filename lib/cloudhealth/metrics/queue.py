import os
import sys, traceback
import pika
from bson.objectid import ObjectId

from cached import CachedMetrics
import cloudhealth
from cloudhealth import accounts
from cloudhealth import providers
from cloudhealth import inventory

class MetricQueueClient(object):

	def __init__(self):
		self.connection = pika.BlockingConnection(
			pika.ConnectionParameters(
				host='localhost'
			))
		self.channel = self.connection.channel()

		self.channel.queue_declare(
			queue='metrics', 
			durable=True,
			exclusive=False, 
			auto_delete=False
		)

	def insert(self, customer, instance_id, provider_objid):
		self.channel.basic_publish(
			exchange='',
			routing_key='metrics',
			body='',
			properties=pika.BasicProperties(
				delivery_mode = 1, # make message non-persistent,
				headers = {
					'instance_id': instance_id,
					'customer_id': str(customer.Id()),
					'provider_id': str(provider_objid),
				}
			))

		print "Added %s to queue..." % (instance_id,)

	def close(self):
		self.connection.close()

class MetricQueueWorker(object):

	def __init__(self, id):
		self.id = id

	def go(self):
		self.messages = 0

		self.channel = None

		# Step #1: Connect to RabbitMQ using the default parameters
		parameters = pika.ConnectionParameters()
		self.connection = pika.SelectConnection(parameters, self.on_connected)

		try:
			# Loop so we can communicate with RabbitMQ
			self.connection.ioloop.start()
		except KeyboardInterrupt:
			print 'KeyboardInterrupt'
			# Gracefully close the connection
			self.connection.close()
			# Loop until we're fully closed, will stop on its own
			self.connection.ioloop.start()

	def stop(self):
		self.channel.basic_cancel(self.on_cancelok, self.consumer_tag)

	# Step #2
	def on_connected(self, connection):
		"""Called when we are fully connected to RabbitMQ"""
		# Open a channel
		connection.channel(self.on_channel_open)

	# Step #3
	def on_channel_open(self, new_channel):
		"""Called when our channel has opened"""
		self.channel = new_channel
		self.declare_queue(self.on_queue_declared)

	def declare_queue(self, cb):
		return self.channel.queue_declare(
			queue="metrics", 
			durable=True, 
			exclusive=False, 
			auto_delete=False, 
			callback=cb
		)

	# Step #4
	def on_queue_declared(self, frame):
		"""Called when RabbitMQ has told us our Queue has been declared, frame is the response from RabbitMQ"""
		self.channel.basic_qos(prefetch_count=1)
		self.channel.add_on_cancel_callback(self.on_consumer_cancelled)
		self.consumer_tag = self.channel.basic_consume(
			self.handle_delivery, 
			frame.method.queue
		)

	def on_consumer_cancelled(self, method_frame):
		self.channel.close()

	def check_queue_empty(self):
		self.declare_queue(self.is_queue_empty_on_queue_declared)

	def is_queue_empty_on_queue_declared(self, frame):
		if frame.method.message_count == 0:
			self.channel.basic_cancel(self.on_cancelok, self.consumer_tag)

	# Step #5
	def handle_delivery(self, channel, method, properties, body):
		"""Called when we receive a message from RabbitMQ"""

		#<Basic.Deliver(['consumer_tag=ctag1.0', 'redelivered=True', 'routing_key=test', 'delivery_tag=3', 'exchange='])>
		#print method

		#<BasicProperties(['delivery_mode=1', "headers={'Client': 'Browser'}"])>
		if 'instance_id' in properties.headers and 'provider_id' in properties.headers:
			try:
				instance_id = str(properties.headers['instance_id'])
				provider_id = str(properties.headers['provider_id'])
				print "Processing: instance_id -", instance_id, " provider_id -", provider_id 

				provider = providers.Ec2Inventory(provider_id)

				metric_cache = CachedMetrics()
				ec2_prov = providers.Ec2Metrics(provider)
				dps = ec2_prov.instance_cpu(properties.headers['instance_id'])
				x = metric_cache.insert_instance_cpu(
					ObjectId(properties.headers['customer_id']), 
					properties.headers['instance_id'], 
					dps)

				print self.id, '- insert', x, 'metrics!'

				channel.basic_ack(method.delivery_tag, False)

				self.check_queue_empty()

			except Exception, ex:
				print "[handle_delivery] Unexpected error: %s" % ex 
				tb = traceback.format_exc()
				print tb
				#print "[handle_delivery] Unexpected error:", sys.exc_info()[0]
				#traceback.print_stack()

	def on_cancelok(self, unused_frame):
		self.channel.close()
		self.connection.ioloop.stop()
