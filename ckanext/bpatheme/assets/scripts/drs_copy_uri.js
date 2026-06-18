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
                this._toggleFeedback('No DRS URI available.');
                return;
            }
            navigator.clipboard.writeText(uri).then(
                this._onCopySuccess,
                this._onCopyError
            );
        },
        _onCopySuccess: function () {
            this._toggleFeedback('DRS URI copied to clipboard.');
        },
        _onCopyError: function () {
            this._toggleFeedback('Could not copy to clipboard.');
        },
        _toggleFeedback: function (message) {
            var element = this.el.closest('div, li');
            element.popover('destroy');
            element.popover({
                title: 'Copied!',
                html: true,
                content: message,
                placement: 'left',
            });
            element.popover('show');
            setTimeout(function () { element.popover('destroy'); }, 6000);
        },
    };
});
