Meteor.subscribe('customers');
Meteor.subscribe('inventory');

Template.customers.customers = function () {
  return Customers.find({});
};

Template.inventory.instances = function () {
  return Inventory.find({assett_type: 'ec2_instance'});
};

Template.inventory.instance_volumes = function (instance_id) {
  return Inventory.find({assett_type: 'ec2_volume', instance_id: instance_id});
};

Template.inventory.volumes = function () {
  return Inventory.find({assett_type: 'ec2_volume'});
};

Template.inventory.snapshot_count = function (volume_id) {
  return Inventory.find({assett_type: 'ec2_snapshot', volume_id: volume_id}).count();
};
