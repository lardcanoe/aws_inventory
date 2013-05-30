Meteor.subscribe('customers');
Meteor.subscribe('inventory');

Template.customers.customers = function () {
  return Customers.find({});
};

Template.inventory.instances = function (customer_id) {
  return Inventory.find({assett_type: 'ec2_instance', customer_id: customer_id});
};

Template.inventory.instance_volumes = function (instance_id) {
  return Inventory.find({assett_type: 'ec2_volume', instance_id: instance_id});
};

Template.inventory.volumes = function (customer_id) {
  return Inventory.find({assett_type: 'ec2_volume', customer_id: customer_id});
};

Template.inventory.snapshot_count = function (volume_id) {
  return Inventory.find({assett_type: 'ec2_snapshot', volume_id: volume_id}).count();
};
