;(function($, undefined) {

    var sortable_targets = '.results';

    var maybe_move_region = function(e, ui){
        $(this).find("tbody").append(ui.item);
    };

    var table_helper = function(e, tr) {
        var $originals = tr.children();
        var $helper = tr.clone();
        $helper.children().each(function(index) {
            $(this).width($originals.eq(index).width())
        });
        return $helper;
    };

    var update_remote_object = function(obj, requested_position) {
        alert('making ' + obj + ' be at position ' + requested_position);
    };

    var finish_changelist_changes = function(e, ui) {
        var tbody = ui.item.parent();
        var rows = tbody.find('tr');
        rows.each(function (i) {
            var target_class = (i % 2) + 1;
            $(this).removeClass('row1 row2').addClass('row'+ target_class);
            $('td:nth-child(1)', this).html(i+1);
        });
        var new_position = Math.min(1, ui.item.prevUntil().length + 1);
        var handle = $(e.srcElement).attr('data-pk');
        update_remote_object(handle, new_position);
    };

    var start_changelist_changes = function(e, ui) {
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
        handle: 'div.drag_handle',
        tolerance: 'pointer',
        cursor: 'move'
    };

    var ready_up = function() {
        $(sortable_targets).sortable(sortable_options);
    };

    $(document).ready(ready_up);
})(jQuery);
