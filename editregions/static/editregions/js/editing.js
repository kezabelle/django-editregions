(function($, document, undefined) {
    $(function() {
        var $fancyiframe_links = $('.results.ui-sortable tbody a');
        var $nominated_template = $('[rel="current_template"]').eq(0);
        var $tables = $('table.existing-chunks');
        var $doc = $(document);

        $nominated_template.bind('change', function(evt) {
            var $me = $(this);
            var qs = '?current_template=' + $me.val();
            var url = [location.protocol, '//', location.host, location.pathname].join('');
            window.location = url + qs;
            return;
        });

        var on_popup_close = function(event, data) {
            // no additional data was provided.
            if (arguments.length === 1) {
                return;
            }
            console.log(arguments);
        }
        $doc.bind('fancyiframe-close', on_popup_close);

        $fancyiframe_links.fancyiframe({
            callbacks: {
                href: function($el) {
                    var href = $el.attr('href');
                    var parts = href.split('?', 2);
                    var link = parts[0];
                    var qs = (parts[1] || '') + '&_popup=1&_backend_editing=1&_frontend_editing=1';
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
    });

})(typeof django !== 'undefined' && django.jQuery || window.jQuery, document);
