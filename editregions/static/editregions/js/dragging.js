;(function($, undefined) {
    // for fancyiframe
    var fancyiframe_links = '.results.ui-sortable tbody a, .changelist-filter .add-chunks__available a';
//    var $nominated_template = $('[rel="current_template"]').eq(0);

    var on_popup_close = function(event, data) {
            // no additional data was provided.
        if (arguments.length === 1) {
            return;
        }

        if (data.html !== void(0) && data.html !== '') {
            $(all_inlines).replaceWith(data.html);
            ready_up();
        }
    };

    // for dragging and dropping
    var handle = 'div.drag_handle';
    var sortable_targets = '.results-list';
    var all_inlines = 'div.region-inline-wrapper';
    var progress_wrapper = 'div.region-inline-progress-wrapper';
    var wait = 'div.region-inline-progress-wrapper div.waiting';
    var success = 'div.region-inline-progress-wrapper div.success';


    var update_remote_object = function(sortable, event, ui, id, position, region) {
        var url = ui.item.find(handle).eq(0).attr('data-href');
        // url should be the URL to the movement form.
        if (url !== void(0)) {
            var $wait = $(wait);
            var $old_progress = $(progress_wrapper);
            $wait.show();
            var data = {
                pk: id,
                position: position,
                region: region
            };
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
                $(sortable_targets).sortable('enable');
                $(sortable_targets).sortable('refresh');

                // refresh the view itself with updated data.
                $(all_inlines).replaceWith(resp['html']);
                ready_up();
            });
        }
    };

    var finish_changelist_changes = function(e, ui) {
        // this fires for both sides of a drag-between-tables ...

        var tbody = ui.item.parent();
        var rows = tbody.find('tr');
        rows.each(function (i) {
            var target_class = (i % 2) + 1;
            $(this).removeClass('row1 row2').addClass('row'+ target_class);
            $('td:nth-child(1)', this).html(i+1);
        });

        var obj_id = ui.item.find(handle).eq(0).attr('data-pk');

        var target_region = $(this).attr('data-region');
        var target_position = ui.item.index()+1;

        var exists = $(this).find(ui.item).length === 1;
        if (exists === true) {
            console.log(target_position);
            // something has changed, either DOM index or region, or both.
            update_remote_object(this, e, ui, obj_id, target_position, target_region);
        } else {
            // nothing has changed ...
        }
    };

    var get_subclass_type = function(element) {
        /*
        Takes `element`, (typically a `tr`) and finds all links within it,
        reducing the css classes to those which are related to chunk variants.

        If more than one unique chunktype value is found, that's an error.
         */
        var my_type = element.find('a').map(function() {
            var _class = $(this).attr('class').split(' ');
            for (var i = 0; i < _class.length; i++) {
                var _just_this_class = _class[i];
                if (_just_this_class.indexOf('chunktype-') === 0) {
                    return _just_this_class;
                }
            }
        });
        var unique_type_classes = $.unique(my_type);
        if (unique_type_classes.length !== 1) {
            return false;
        }
        return unique_type_classes[0];
    };
    var start_changelist_changes = function(e, ui) {
        var selected_subclass = get_subclass_type(ui.item);
        var all_sortables = $(sortable_targets);
        all_sortables.sortable('disable');
        var to_enable = all_sortables.filter('.' + selected_subclass);
        to_enable.sortable('enable');
        all_sortables.sortable('refresh');
        // set placeholder contents ...
        var html = ui.item.html();
        ui.placeholder.html(html);
    };

    var restore_changelists = function(e, ui) {
        var all_sortables = $(sortable_targets);
        all_sortables.sortable('enable');
        all_sortables.sortable('refresh');
    };

    var sortable_options = {
        axis: 'y',
        stop: restore_changelists,
        start: start_changelist_changes,
        update: finish_changelist_changes,
        forcePlaceholderSize: true,
        containment: '.region-inline-wrapper, #changelist-form',
        items: 'li',
        connectWith: sortable_targets,
        dropOnEmpty: true,
        handle: handle,
        tolerance: 'pointer',
        cursor: 'move'
    };

    // this exists as a non-anonymous function so that once we've updated an
    // object we can dynamically re-bind everything we need to.
    var ready_up = function() {
        var jqSortables = $(sortable_targets);
        jqSortables.sortable(sortable_options);
        jqSortables.sortable("option", "disabled", false);
        jqSortables.disableSelection();

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
        } else {
            $(fancyiframe_links).each(function() {
                var $t = $(this);
                var href = $t.attr('href');
                var redirect = encodeURIComponent(window.location.pathname + window.location.search);
                if (href.indexOf('?') === -1) {
                    href += '?next=' + redirect;
                } else {
                    href += '&next=' + redirect;
                }
                $t.attr('href', href);
            });
        }
    };

    $(document).ready(ready_up);
})(django.jQuery);
