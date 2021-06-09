'use strict';

ckan.module('bpatheme_header_image', function ($) {
    return {
        initialize: function () {
            $.proxyAll(this, /_on/);
            this.sandbox.client.getTemplate('bpatheme_header_image.html', this.options, this._onReceiveSnippet);
        },
        _onReceiveSnippet: function (html) {
            this.el[0].innerHTML = html;
        },
    }
});
