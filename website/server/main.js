Meteor.startup(function () {
// code to run on server at startup
});

Meteor.publish("customers", function () {
	return Customers.find({});
});

Meteor.publish("inventory", function () {
	return Inventory.find({});
});