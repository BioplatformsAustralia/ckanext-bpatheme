ckan.module('fetch-async-page', function($, _) {
  'use strict';

  return {
    initialize: function() {
      $.proxyAll(this, /_on/);
      this.sandbox.client.getTemplate('test_async.html');
    },
  };
});
