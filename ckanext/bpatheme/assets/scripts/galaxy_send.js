'use strict';

/*
 * galaxy_send CKAN module
 *
 * Two-step modal:
 *   1. If no Galaxy API key is stored in the CKAN session, show a "Connect"
 *      step where the user pastes their key (User → Preferences → API Key in Galaxy).
 *   2. Once connected, show the user's histories and let them pick one.
 *      CKAN proxies all Galaxy API calls server-side using the stored key.
 *
 * Required data attributes on the trigger element:
 *   data-module-resource-id   – CKAN resource UUID
 *   data-module-package-id    – CKAN package name/id
 *   data-module-resource-name – Human-readable resource name
 *   data-module-galaxy-url    – Galaxy instance base URL (for links only)
 */

ckan.module('galaxy_send', function ($) {

    var MODAL_ID = 'galaxy-australia-modal';

    function _buildModal(galaxyUrl) {
        var safeUrl = _escAttr(galaxyUrl);
        var apiKeyHelpUrl = safeUrl + '/user/api_key';
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

            /* ── API key step ── */
            '        <div id="galaxy-modal-key-step" style="display:none">',
            '          <p>',
            '            Enter your <strong>Galaxy Australia API key</strong> to connect.',
            '            <a href="' + apiKeyHelpUrl + '" target="_blank">',
            '              Find it under User &rarr; Preferences &rarr; Manage API Key',
            '              <i class="fa fa-external-link"></i>',
            '            </a>.',
            '          </p>',
            '          <div class="input-group">',
            '            <input type="password" id="galaxy-api-key-input" class="form-control"',
            '                   placeholder="Paste your Galaxy API key here" autocomplete="off">',
            '            <span class="input-group-btn">',
            '              <button class="btn btn-primary" id="galaxy-connect-btn">',
            '                <i class="fa fa-plug"></i> Connect',
            '              </button>',
            '            </span>',
            '          </div>',
            '          <div id="galaxy-key-error" class="text-danger small" style="margin-top:6px;display:none"></div>',
            '        </div>',

            /* ── loading spinner ── */
            '        <div id="galaxy-modal-loading" class="text-center" style="padding:24px 0;display:none">',
            '          <i class="fa fa-spinner fa-spin fa-2x"></i>',
            '          <p style="margin-top:8px">Loading your Galaxy Australia histories&hellip;</p>',
            '        </div>',

            /* ── general error ── */
            '        <div id="galaxy-modal-error" class="alert alert-danger" style="display:none"></div>',

            /* ── history list ── */
            '        <div id="galaxy-modal-histories" style="display:none">',
            '          <p style="margin-bottom:6px"><strong>Select a history to send this file to:</strong></p>',
            '          <div id="galaxy-history-list" class="list-group"',
            '               style="max-height:320px;overflow-y:auto;border:1px solid #ddd;border-radius:4px">',
            '          </div>',
            '          <p class="text-right" style="margin-top:6px;margin-bottom:0">',
            '            <a href="#" id="galaxy-change-key-link" class="small text-muted">',
            '              <i class="fa fa-key"></i> Change API key',
            '            </a>',
            '          </p>',
            '        </div>',

            /* ── success ── */
            '        <div id="galaxy-modal-success" class="alert alert-success" style="display:none">',
            '          <i class="fa fa-check"></i>',
            '          Your file has been queued for upload in Galaxy Australia.',
            '          <br><a href="' + safeUrl + '" target="_blank" class="alert-link">',
            '            Open Galaxy Australia <i class="fa fa-external-link"></i>',
            '          </a>',
            '        </div>',
            '      </div>',

            '      <div class="modal-footer">',
            '        <a href="' + safeUrl + '" target="_blank"',
            '           class="btn btn-default pull-left"',
            '           title="Open Galaxy Australia in a new tab">',
            '          <i class="fa fa-external-link"></i> Galaxy Australia',
            '        </a>',
            '        <button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>',
            '        <button type="button" class="btn btn-primary" id="galaxy-modal-send-btn"',
            '                style="display:none" disabled>',
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
            galaxyUrl: 'https://usegalaxy.org.au',
        },

        initialize: function () {
            $.proxyAll(this, /_on/);
            this.el.on('click', this._onClick);
        },

        _getModal: function () {
            var existing = $('#' + MODAL_ID);
            return existing.length ? existing : _buildModal(this.options.galaxyUrl);
        },

        _onClick: function (e) {
            e.preventDefault();
            this._selectedHistoryId = null;
            var modal = this._getModal();

            modal.find('#galaxy-modal-resource-name').text(
                this.options.resourceName ? 'File: ' + this.options.resourceName : ''
            );
            // Wire up persistent buttons (they survive modal reuse)
            modal.find('#galaxy-connect-btn').off('click').on('click', this._onConnectClick);
            modal.find('#galaxy-change-key-link').off('click').on('click', this._onChangeKeyClick);
            modal.find('#galaxy-modal-send-btn')
                .off('click').on('click', this._onSendClick)
                .prop('disabled', true).show()
                .html('<i class="fa fa-rocket"></i> Send to Galaxy');

            this._resetModal(modal);
            modal.modal('show');
            this._loadHistories(modal);
        },

        _resetModal: function (modal) {
            modal.find('#galaxy-modal-key-step').hide();
            modal.find('#galaxy-modal-loading').hide();
            modal.find('#galaxy-modal-error').hide().text('');
            modal.find('#galaxy-modal-histories').hide();
            modal.find('#galaxy-modal-success').hide();
            modal.find('#galaxy-modal-send-btn').hide();
            modal.find('#galaxy-api-key-input').val('');
            modal.find('#galaxy-key-error').hide().text('');
            modal.find('#galaxy-history-list').empty();
        },

        _showKeyStep: function (modal, errorMsg) {
            modal.find('#galaxy-modal-loading').hide();
            modal.find('#galaxy-modal-histories').hide();
            modal.find('#galaxy-modal-send-btn').hide();
            modal.find('#galaxy-modal-key-step').show();
            if (errorMsg) {
                modal.find('#galaxy-key-error').text(errorMsg).show();
            }
        },

        _loadHistories: function (modal) {
            var self = this;
            modal.find('#galaxy-modal-loading').show();
            $.ajax({
                url: '/galaxy/histories',
                method: 'GET',
                success: function (data) { self._onHistoriesReceived(modal, data); },
                error: function (xhr) { self._onHistoriesFailed(modal, xhr); },
            });
        },

        _onHistoriesReceived: function (modal, data) {
            modal.find('#galaxy-modal-loading').hide();

            if (!Array.isArray(data) || !data.length) {
                modal.find('#galaxy-modal-error').html(
                    '<i class="fa fa-exclamation-triangle"></i> ' +
                    'No histories found in Galaxy Australia. ' +
                    'Please <a href="' + _escHtml(this.options.galaxyUrl) + '" target="_blank">open Galaxy Australia</a> ' +
                    'and create a history first.'
                ).show();
                modal.find('#galaxy-modal-histories').hide();
                modal.find('#galaxy-modal-send-btn').hide();
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
                    modal.find('#galaxy-history-list .list-group-item').removeClass('active');
                    $(this).addClass('active');
                    self._selectedHistoryId = history.id;
                    modal.find('#galaxy-modal-send-btn').prop('disabled', false);
                });
                listEl.append(item);
            });

            modal.find('#galaxy-modal-histories').show();
            modal.find('#galaxy-modal-send-btn').show().prop('disabled', true);
        },

        _onHistoriesFailed: function (modal, xhr) {
            modal.find('#galaxy-modal-loading').hide();
            // 401 with error=no_api_key means we need the user to enter their key
            if (xhr.status === 401) {
                try {
                    var body = JSON.parse(xhr.responseText);
                    if (body.error === 'no_api_key') {
                        this._showKeyStep(modal);
                        return;
                    }
                } catch (ignored) {}
            }
            // 401 with a different message means the stored key was rejected by Galaxy
            if (xhr.status === 401 || xhr.status === 403) {
                this._showKeyStep(modal, 'Your Galaxy API key was rejected. Please enter a valid key.');
                return;
            }
            var msg = 'Could not load Galaxy Australia histories.';
            try {
                var b = JSON.parse(xhr.responseText);
                if (b && b.error) { msg = b.error; }
            } catch (ignored) {}
            modal.find('#galaxy-modal-error').html(
                '<i class="fa fa-exclamation-triangle"></i> ' + _escHtml(msg)
            ).show();
        },

        _onConnectClick: function () {
            var modal = this._getModal();
            var apiKey = modal.find('#galaxy-api-key-input').val().trim();
            if (!apiKey) {
                modal.find('#galaxy-key-error').text('Please enter an API key.').show();
                return;
            }
            var connectBtn = modal.find('#galaxy-connect-btn');
            connectBtn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i>');
            modal.find('#galaxy-key-error').hide();
            var self = this;

            $.ajax({
                url: '/galaxy/set-api-key',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ api_key: apiKey }),
                success: function () {
                    connectBtn.prop('disabled', false).html('<i class="fa fa-plug"></i> Connect');
                    modal.find('#galaxy-modal-key-step').hide();
                    self._loadHistories(modal);
                },
                error: function () {
                    connectBtn.prop('disabled', false).html('<i class="fa fa-plug"></i> Connect');
                    modal.find('#galaxy-key-error').text('Could not save API key. Please try again.').show();
                },
            });
        },

        _onChangeKeyClick: function (e) {
            e.preventDefault();
            var modal = this._getModal();
            modal.find('#galaxy-modal-histories').hide();
            modal.find('#galaxy-modal-send-btn').hide();
            modal.find('#galaxy-api-key-input').val('');
            modal.find('#galaxy-key-error').hide().text('');
            modal.find('#galaxy-modal-key-step').show();
        },

        _onSendClick: function () {
            var modal = this._getModal();
            if (!this._selectedHistoryId) { return; }
            var sendBtn = modal.find('#galaxy-modal-send-btn');
            sendBtn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i> Sending&hellip;');
            var self = this;

            $.ajax({
                url: '/galaxy/send',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    history_id: self._selectedHistoryId,
                    package_id: self.options.packageId,
                    resource_id: self.options.resourceId,
                }),
                success: function (data) {
                    if (data && data.err_msg) {
                        sendBtn.prop('disabled', false).html('<i class="fa fa-rocket"></i> Send to Galaxy');
                        modal.find('#galaxy-modal-error').html(
                            '<i class="fa fa-exclamation-triangle"></i> ' + _escHtml(data.err_msg)
                        ).show();
                        return;
                    }
                    modal.find('#galaxy-modal-histories').hide();
                    modal.find('#galaxy-modal-error').hide();
                    modal.find('#galaxy-modal-send-btn').hide();
                    modal.find('#galaxy-modal-success').show();
                },
                error: function (xhr) {
                    sendBtn.prop('disabled', false).html('<i class="fa fa-rocket"></i> Send to Galaxy');
                    var msg = 'Failed to send to Galaxy Australia.';
                    try { var b = JSON.parse(xhr.responseText); if (b && b.error) { msg = b.error; } } catch (ignored) {}
                    modal.find('#galaxy-modal-error').html(
                        '<i class="fa fa-exclamation-triangle"></i> ' + _escHtml(msg)
                    ).show();
                },
            });
        },
    };
});

function _escHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function _escAttr(str) {
    return String(str).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
