;(function($, undefined) {
    // for fancyiframe
    var fancyiframe_links = '.results.ui-sortable tbody a';
//    var $nominated_template = $('[rel="current_template"]').eq(0);

    var on_popup_close = function(event, data) {
            // no additional data was provided.
        if (arguments.length === 1) {
            return;
        }
        console.log(arguments);
    };

    // for dragging and dropping
    var handle = 'div.drag_handle';
    var sortable_targets = '.results';
    var all_inlines = 'div.region-inline-wrapper';
    var progress_wrapper = 'div.region-inline-progress-wrapper';
    var wait = 'div.region-inline-progress-wrapper div.waiting';
    var success = 'div.region-inline-progress-wrapper div.success';
    var start_region;
    var start_position;
    var target_region;
    var target_position;

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
        if (url !== void(0)) {
            var $wait = $(wait);
            var $old_progress = $(progress_wrapper);
            $wait.show();
            var data = {pk: id, position: position, region: region};
            $.get(url, data, function(resp, status) {
                $wait.fadeOut(750, function(evt) {
                    $old_progress.remove();
                });
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

    var ready_up = function() {
        $(sortable_targets).sortable(sortable_options).disableSelection();

        $(document).bind('fancyiframe-close', on_popup_close);

        if (window.location.search.indexOf('pop=') === -1 && window.location.search.indexOf('_popop=') === -1) {
            $(fancyiframe_links).fancyiframe({
                elements: {
                    prefix: 'django-adminlinks',
                    classes: 'adminlinks'
                },
                fades: {
                    opacity: 0.90,
                    overlayIn: 100,
                    overlayOut: 250,
                    wrapperIn: 0,
                    wrapperOut: 250
                }
            });
        }
    };

    $(document).ready(ready_up);
})(typeof django !== 'undefined' && django.jQuery || window.jQuery);
