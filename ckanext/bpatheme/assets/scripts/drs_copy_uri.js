'use strict';

ckan.module('drs_copy_uri', function ($) {
    return {
        initialize: function () {
            $.proxyAll(this, /_on/);
            this.el.on('click', this._onClick);
        },
        _onClick: function (event) {
            event.preventDefault();
            var uri = this.options.uri;
            if (!uri) {
                this._toggleFeedback('No DRS URI available');
                return;
            }
            var self = this;
            navigator.clipboard.writeText(uri).then(
                function () { self._toggleFeedback(uri); },
                function (err) { self._toggleFeedback('ERROR: ' + err); }
            );
        },
        _toggleFeedback: function (message) {
            var element = $(this.el[0]).closest('div');
            $(element).on('shown.bs.popover', function () {
                $('.popover').one('click', function () {
                    $(this).closest('div').popover('destroy');
                });
                setTimeout(function () {
                    element.popover('destroy');
                }, 6000);
            });
            element.popover('destroy');
            element.popover({
                title: 'Copied to clipboard!',
                html: true,
                content: message,
                placement: 'left'
            });
            element.popover('show');
        }
    };
});
