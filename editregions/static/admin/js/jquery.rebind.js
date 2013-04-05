;(function(undefined) {
    if (typeof django !== 'undefined' && django.jQuery) {
        var did_modify = false;

        // standard access via $
        if (typeof window.$ === 'undefined') {
            window.$ = django.jQuery;
            did_modify = true
        };

        // in case something is explicitly asking for jQuery.
        if (typeof window.jQuery === 'undefined') {
            window.jQuery = django.jQuery;
            did_modify = true
        };

        // can we log the information?
        if (typeof console !== 'undefined' && typeof console.log === 'function') {
            var version = $.fn.jquery.toString();
            if (did_modify === true) {
                console.log('version ' + version + ' of jQuery applied to window[$|jQuery]');
            } else {
                console.log('jQuery version ' + version + ' already applied to window[$|jQuery]');
            }
        };

    }
})();
