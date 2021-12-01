'use strict';

ckan.module('bpatheme_footer_image', function ($) {
    return {
        initialize: function () {
            $.proxyAll(this, /_on/);
            if (this.options.alt === 'NCRIS') {
                this.sandbox.client.getTemplate('bpatheme_footer_image_ncris.html', this.options, this._onReceiveSnippet);
            } else {
                this.sandbox.client.getTemplate('bpatheme_footer_image_bpa.html', this.options, this._onReceiveSnippet);
            }

        },
        _onReceiveSnippet: function (html) {
            this.el[0].innerHTML = html;
        },
    }
});
