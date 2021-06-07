'use strict';

ckan.module('bpatheme_fetchasync', function ($) {
    return {
        initialize: function () {
            $.proxyAll(this, /_on/);
            for (const key of Object.keys(this.options.project)) {
                this.options[key] = this.options.project[key]
            }
            delete this.options.project
            this.sandbox.client.getTemplate('bpatheme_fetchasync.html', this.options, this._onReceiveSnippet);
        },
        _onReceiveSnippet: function (html) {
            this.el[0].innerHTML = html;
        },
    }
});
