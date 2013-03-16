(function($, document, undefined) {
    $(function() {
        var currently_moving = 'existing-chunks__item__moving';
        var currently_deleting = 'existing-chunks__item__deleting';
        var currently_editing = 'existing-chunks__item__editing';
        var moved = 'existing-chunks__item__justmoved';
        var all_classes = [
            currently_moving,
            currently_deleting,
            currently_editing,
            moved].join(' ');

        var $edit_links = $('.existing-chunks__item__name a');
        var $delete_links = $('.existing-chunks__item__delete .deletelink');
        var $move_links = $('.existing-chunks__item__move a');
        var $fancyiframe_links = $('.add-chunks__available a, .existing-chunks__item__name a, .existing-chunks__item__delete a');
        var $nominated_template = $('[rel="current_template"]').eq(0);
        var $tables = $('table.existing-chunks');
        var $doc = $(document);

        var toggle_row_for_deletion = function() {
            $(this).closest('tr').toggleClass(currently_deleting);
        };
        var toggle_row_for_moving = function() {
            $(this).closest('tr').toggleClass(currently_moving);
        };
        var toggle_row_for_editing = function() {
            $(this).closest('tr').toggleClass(currently_editing);
        };

        var move_row_up = function(evt) {
            return move_row.call(this, evt, 'prev', 'before');
        }
        var move_row_down = function(evt) {
            return move_row.call(this, evt, 'next', 'after');
        }

        var move_row = function(evt, next_prev, before_after) {
            evt.preventDefault();
            var row = $(this).closest("tr");
            row.siblings().removeClass(currently_moving);
            var other = row[next_prev]();
            if (other.is("tr")) {
                row.detach();
                other[before_after](row);
                row.addClass(currently_moving);
                return;
            }
            alert('Unable to move any further');
        }

        $nominated_template.bind('change', function(evt) {
            var $me = $(this);
            var qs = '?current_template=' + $me.val();
            var url = [location.protocol, '//', location.host, location.pathname].join('');
            window.location = url + qs;
            return;
        });

        $delete_links.bind('mouseover', toggle_row_for_deletion);
        $delete_links.bind('mouseout', toggle_row_for_deletion);

        $move_links.bind('mouseover', function(evt) {
            $(this).closest('tr').addClass(currently_moving);
        });
        $move_links.bind('mouseout', function(evt) {
             $(this).closest('tr').removeClass(currently_moving);
         });

        $edit_links.bind('mouseover', toggle_row_for_editing);
        $edit_links.bind('mouseout', toggle_row_for_editing);


        var on_popup_close = function(event, action, data) {
            console.log(arguments);
            if (action === 'delete') {
                $('#movable-item__' + data.primary_key).detach().remove();
            }
            if (action === 'add') {
                $tables
                    .filter('#container-' + data.parent_region)
                    .eq(0)
                    .find('tbody tr')
                    .eq(-1)
                    .after(data.html);
            }
            if (action === 'change') {
                $('#movable-item__' + data.primary_key).replaceWith(data.html);
            }
            // Some action was definitely called, but it may have been custom
            // so we still want to update the tables.
            if (typeof action !== "undefined") {
                $tables.tableDnDUpdate();
            }
        }
        $doc.bind('fancyiframe-close', on_popup_close);

        $fancyiframe_links.fancyiframe({
            callbacks: {
                href: function($el) {
                    var href = $el.attr('href');
                    var parts = href.split('?', 2);
                    var link = parts[0];
                    var qs = (parts[1] || '') + '&_popup=1&_frontend_editing=1';
                    return link + '?' + qs;
                }
            },
            elements: {
                prefix: 'django-adminlinks',
                classes: 'adminlinks'
            },
            fades: {
                opacity: 0.85,
                overlayIn: 100,
                overlayOut: 250,
                wrapperIn: 0,
                wrapperOut: 250
            }
        });

        var highlight_change = function($row, klass, duration) {
            $row
                .removeAttr('style') // needed to cancel previous animate calls.
                .removeClass(all_classes)
                .addClass(klass)
                .animate({backgroundColor: '#FFFFFF'}, duration)
                .removeClass(klass);
            return;
        }


/*
        $tables.tableDnD({
            dragHandle: '.existing-chunks__item__move a',
            onDragClass: 'existing-chunks__item__moving',
            onDrop: function(table, dropped_row) {
                var $row = $(dropped_row);
                $row.addClass(currently_moving);
                var $act = $(table).parent().parent().find('.activity-occuring').eq(0);
                var $chunks = $(table).parent().parent().find('.grouped-chunks').eq(0);
                $chunks.hide();
                $act.show();
                $.ajax({
                    url: 'reorder/',
                    cache: false,
                    type: 'GET',
                    async: false,
                    data: $.tableDnD.serialize(),
                    success: function(data) {
                        highlight_change($row, moved, 1500);
                        $act.hide();
                        $chunks.show();
                    },
                    error: function(data) {
                        alert('An error occured. Need to implement reverting the table.');
                        $act.hide();
                        $chunks.show();
                    }
                });
            }
        });
*/
    });

})(typeof django !== 'undefined' && django.jQuery || window.jQuery, document);
