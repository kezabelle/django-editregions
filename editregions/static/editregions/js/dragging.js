;(function($, undefined) {
    // for fancyiframe
    var fancyiframe_links = '.results.ui-sortable tbody a, .changelist-filter .add-chunks__available a';
//    var $nominated_template = $('[rel="current_template"]').eq(0);

    var on_popup_close = function(event, data) {
            // no additional data was provided.
        if (arguments.length === 1) {
            return;
        };

        if (data.html !== void(0) && data.html !== '') {
            $(all_inlines).replaceWith(data.html);
            ready_up();
        };
    };

    // for dragging and dropping
    var handle = 'div.drag_handle';
    var sortable_targets = '.results';
    var all_inlines = 'div.region-inline-wrapper';
    var progress_wrapper = 'div.region-inline-progress-wrapper';
    var wait = 'div.region-inline-progress-wrapper div.waiting';
    var success = 'div.region-inline-progress-wrapper div.success';

    // variables hoisted up here for tracking whether things got changed.
    var start_region;
    var start_position;
    var target_region;
    var target_position;

    // just sets some variables into the parent scope when they might've changed,
    // so that `finish_changelist_changes` can decide whether or not
    // to bother calling `update_remote_object`
    var maybe_move_region = function(e, ui){
        $(this).find("tbody").append(ui.item);
        // rebinds the region to the parent scope
        target_region = $(this).parent().attr('data-region');
        target_position = ui.item.index();
    };

    var table_helper = function(e, tr) {
        var $originals = tr.children();
        var $helper = tr.clone();
        $helper.children().each(function(index) {
            $(this).width($originals.eq(index).width())
        });
        return $helper;
    };

    var update_remote_object = function(sortable, event, ui, id, position, region) {
        var url = ui.item.find(handle).eq(0).attr('data-href');
        // url should be the URL to the movement form.
        if (url !== void(0)) {
            var $wait = $(wait);
            var $old_progress = $(progress_wrapper);
            $wait.show();
            var data = {pk: id, position: position, region: region};
            $.get(url, data, function(resp, status) {
                // frameElement indicates we're in the popup iframe, so we want
                // to traverse back to the parent window and set a shared
                // variable to indicate to the parent window that once we've
                // closed this window, we need to refresh.
                window.__data_changed__ = true;
                if (window.frameElement !== void(0) && window.frameElement !== null) {
                    parent.window.__data_changed__ = true;
                }
                // wait a bit then remove the progress element from the DOM
                $wait.fadeOut(750, function(evt) {
                    $old_progress.remove();
                });

                // refresh the view itself with updated data.
                $(all_inlines).replaceWith(resp['html']);
                ready_up();
            });
        }
    };

    var finish_changelist_changes = function(e, ui) {
        var tbody = ui.item.parent();
        var rows = tbody.find('tr');
        rows.each(function (i) {
            var target_class = (i % 2) + 1;
            $(this).removeClass('row1 row2').addClass('row'+ target_class);
            $('td:nth-child(1)', this).html(i+1);
        });

        var obj_id = ui.item.find(handle).eq(0).attr('data-pk');
        // in case of undefined after `maybe_move_region`, test again here.
        target_region = target_region || $(this).parent().attr('data-region');
        target_position = target_position || ui.item.index();

        if (target_position !== start_position || target_region !== start_region) {
            update_remote_object(this, e, ui, obj_id, target_position+1, target_region);
        }
    };

    var start_changelist_changes = function(e, ui) {
        // into parent scope.
        start_position = ui.item.index();
        start_region = $(this).parent().attr('data-region');

        var html = ui.item.html();
        ui.placeholder.html(html);
    };

    var sortable_options = {
        axis: 'y',
        helper: table_helper,
        stop: finish_changelist_changes,
        start: start_changelist_changes,
        receive: maybe_move_region,
        forcePlaceholderSize: true,
        containment: '.region-inline-wrapper, #changelist-form',
        items: 'tbody > tr',
        connectWith: sortable_targets,
        dropOnEmpty: true,
        handle: handle,
        tolerance: 'pointer',
        cursor: 'move'
    };

    // this exists as a non-anonymous function so that once we've updated an
    // object we can dynamically re-bind everything we need to.
    var ready_up = function() {
        $(sortable_targets).sortable(sortable_options).disableSelection();

        $(document).bind('fancyiframe-close', on_popup_close);

        if (window.frameElement === null) {
            $(fancyiframe_links).fancyiframe({
                debug: true,
                elements: {
                    prefix: 'django-adminlinks',
                    classes: 'adminlinks'
                },
                fades: {
                    opacity: 0.93,
                    overlayIn: 0,
                    overlayOut: 0
                },
                callbacks: {
                    href: function($element) {
                        // we're not in a frame (so we're viewing the admin
                        // directly;
                        var new_href = $.fn.fancyiframe.defaults.callbacks.href($element);
                        return new_href.toString() + '&amp;_popup=1'
                    }
                }
            });
        }
    };

    $(document).ready(ready_up);
})(django.jQuery);
