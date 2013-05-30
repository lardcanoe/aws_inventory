Customers = new Meteor.Collection("customers");

Customers.allow({
  insert: function (userId, duel) {
    return true;
  },
  update: function (userId, duels, fields, modifier) {
    return true;
  },
  remove: function (userId, duels) {
    return true;
  }
});

Inventory = new Meteor.Collection("inventory");

Inventory.allow({
  insert: function (userId, duel) {
    return true;
  },
  update: function (userId, duels, fields, modifier) {
    return true;
  },
  remove: function (userId, duels) {
    return true;
  }
});