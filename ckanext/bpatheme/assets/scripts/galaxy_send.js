'use strict';

/*
 * galaxy_send CKAN module
 *
 * Wires up the "Send to Galaxy Australia" dropdown item on resource pages and
 * resource list cards.  Opens a Bootstrap modal, fetches the user's Galaxy
 * histories via a CKAN server-side proxy, lets them pick one, then submits
 * an upload job to Galaxy.
 *
 * Required data attributes on the trigger element:
 *   data-module-resource-id   – CKAN resource UUID
 *   data-module-package-id    – CKAN package name/id
 *   data-module-resource-name – Human-readable resource name (shown in modal)
 */

ckan.module('galaxy_send', function ($) {

    var MODAL_ID = 'galaxy-australia-modal';

    // Build the modal DOM once and reuse it across all buttons on the page.
    function _buildModal() {
        var html = [
            '<div class="modal fade" id="' + MODAL_ID + '" tabindex="-1" role="dialog"',
            '     aria-labelledby="galaxy-modal-label">',
            '  <div class="modal-dialog" role="document" style="max-width:600px">',
            '    <div class="modal-content">',
            '      <div class="modal-header">',
            '        <button type="button" class="close" data-dismiss="modal" aria-label="Close">',
            '          <span aria-hidden="true">&times;</span>',
            '        </button>',
            '        <h4 class="modal-title" id="galaxy-modal-label">',
            '          <i class="fa fa-rocket"></i> Send to Galaxy Australia',
            '        </h4>',
            '      </div>',
            '      <div class="modal-body">',
            '        <p id="galaxy-modal-resource-name" class="text-muted small" style="margin-bottom:12px"></p>',
            '        <div id="galaxy-modal-loading" class="text-center" style="padding:24px 0">',
            '          <i class="fa fa-spinner fa-spin fa-2x"></i>',
            '          <p style="margin-top:8px">Loading your Galaxy Australia histories&hellip;</p>',
            '        </div>',
            '        <div id="galaxy-modal-error" class="alert alert-danger" style="display:none"></div>',
            '        <div id="galaxy-modal-histories" style="display:none">',
            '          <p style="margin-bottom:6px"><strong>Select a history to send this file to:</strong></p>',
            '          <div id="galaxy-history-list" class="list-group"',
            '               style="max-height:320px;overflow-y:auto;border:1px solid #ddd;border-radius:4px">',
            '          </div>',
            '        </div>',
            '        <div id="galaxy-modal-success" class="alert alert-success" style="display:none">',
            '          <i class="fa fa-check"></i>',
            '          Your file has been queued for upload in Galaxy Australia.',
            '          <br><a href="https://usegalaxy.org.au" target="_blank" class="alert-link">',
            '            Open Galaxy Australia <i class="fa fa-external-link"></i>',
            '          </a>',
            '        </div>',
            '      </div>',
            '      <div class="modal-footer">',
            '        <a href="https://usegalaxy.org.au" target="_blank"',
            '           class="btn btn-default pull-left"',
            '           title="Open Galaxy Australia in a new tab">',
            '          <i class="fa fa-external-link"></i> Galaxy Australia',
            '        </a>',
            '        <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>',
            '        <button type="button" class="btn btn-primary" id="galaxy-modal-send-btn" disabled>',
            '          <i class="fa fa-rocket"></i> Send to Galaxy',
            '        </button>',
            '      </div>',
            '    </div>',
            '  </div>',
            '</div>',
        ].join('\n');

        $('body').append(html);
        return $('#' + MODAL_ID);
    }

    return {
        options: {
            resourceId: null,
            packageId: null,
            resourceName: null,
        },

        initialize: function () {
            $.proxyAll(this, /_on/);
            this.el.on('click', this._onClick);
        },

        _getModal: function () {
            var existing = $('#' + MODAL_ID);
            return existing.length ? existing : _buildModal();
        },

        _onClick: function (e) {
            e.preventDefault();
            this._selectedHistoryId = null;
            var modal = this._getModal();

            // Reset state
            modal.find('#galaxy-modal-resource-name').text(
                this.options.resourceName ? 'File: ' + this.options.resourceName : ''
            );
            modal.find('#galaxy-modal-loading').show();
            modal.find('#galaxy-modal-histories').hide();
            modal.find('#galaxy-modal-error').hide().text('');
            modal.find('#galaxy-modal-success').hide();
            modal.find('#galaxy-history-list').empty();
            modal.find('#galaxy-modal-send-btn')
                .prop('disabled', true)
                .off('click')
                .on('click', this._onSendClick);

            modal.modal('show');
            this._fetchHistories(modal);
        },

        _fetchHistories: function (modal) {
            var self = this;
            $.ajax({
                url: '/api/galaxy/histories',
                method: 'GET',
                success: function (data) { self._onHistoriesReceived(modal, data); },
                error: function (xhr) { self._onHistoriesFailed(modal, xhr); },
            });
        },

        _onHistoriesReceived: function (modal, data) {
            modal.find('#galaxy-modal-loading').hide();

            if (!data || data.error) {
                var msg = (data && data.error) || 'Unknown error fetching histories.';
                this._showError(modal, msg);
                return;
            }

            if (!data.length) {
                this._showError(
                    modal,
                    'No Galaxy Australia histories found. ' +
                    'Please <a href="https://usegalaxy.org.au" target="_blank">open Galaxy Australia</a> ' +
                    'and create a history, then try again.'
                );
                return;
            }

            var listEl = modal.find('#galaxy-history-list').empty();
            var self = this;

            data.forEach(function (history) {
                var dateStr = (history.update_time || '').split('T')[0];
                var sizeStr = history.nice_size ? ' &mdash; ' + history.nice_size : '';
                var label = '<strong>' + _escHtml(history.name) + '</strong>' +
                            (dateStr ? '<span class="text-muted"> &nbsp;' + dateStr + '</span>' : '') +
                            sizeStr;

                var item = $('<a class="list-group-item" href="#" role="button"></a>')
                    .attr('data-history-id', history.id)
                    .html('<i class="fa fa-history text-muted" style="margin-right:6px"></i>' + label);

                item.on('click', function (e) {
                    e.preventDefault();
                    self._onHistorySelect(modal, history.id, $(this));
                });

                listEl.append(item);
            });

            modal.find('#galaxy-modal-histories').show();
        },

        _onHistoriesFailed: function (modal, xhr) {
            modal.find('#galaxy-modal-loading').hide();
            var msg = 'Could not load Galaxy Australia histories.';
            try {
                var body = JSON.parse(xhr.responseText);
                if (body && body.error) { msg = body.error; }
            } catch (ignored) {}
            this._showError(modal, msg);
        },

        _onHistorySelect: function (modal, historyId, itemEl) {
            modal.find('#galaxy-history-list .list-group-item').removeClass('active');
            itemEl.addClass('active');
            this._selectedHistoryId = historyId;
            modal.find('#galaxy-modal-send-btn').prop('disabled', false);
        },

        _onSendClick: function () {
            var modal = this._getModal();
            if (!this._selectedHistoryId) { return; }

            var sendBtn = modal.find('#galaxy-modal-send-btn');
            sendBtn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Sending&hellip;');

            var self = this;
            $.ajax({
                url: '/api/galaxy/send',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    history_id: self._selectedHistoryId,
                    package_id: self.options.packageId,
                    resource_id: self.options.resourceId,
                }),
                success: function (data) { self._onSendSuccess(modal, data); },
                error: function (xhr) { self._onSendFailed(modal, xhr, sendBtn); },
            });
        },

        _onSendSuccess: function (modal, data) {
            // Galaxy returns 200 even for queued jobs; check for error key
            if (data && data.err_msg) {
                this._onSendFailed(modal, { responseText: JSON.stringify({ error: data.err_msg }) },
                    modal.find('#galaxy-modal-send-btn'));
                return;
            }
            modal.find('#galaxy-modal-histories').hide();
            modal.find('#galaxy-modal-error').hide();
            modal.find('#galaxy-modal-send-btn').hide();
            modal.find('#galaxy-modal-success').show();
        },

        _onSendFailed: function (modal, xhr, sendBtn) {
            var msg = 'Failed to send file to Galaxy Australia.';
            try {
                var body = JSON.parse(xhr.responseText);
                if (body && body.error) { msg = body.error; }
            } catch (ignored) {}
            sendBtn.prop('disabled', false)
                   .html('<i class="fa fa-rocket"></i> Send to Galaxy');
            this._showError(modal, msg);
        },

        _showError: function (modal, message) {
            modal.find('#galaxy-modal-error').html(
                '<i class="fa fa-exclamation-triangle"></i> ' + message
            ).show();
        },
    };
});

function _escHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
