;(function($, $p, pdoc, undefined) {
    var callable = function(evt) {
        $p(pdoc).trigger('fancyiframe-resize');
    };
    // Django 1.6+ (jQuery 1.9+)
    if ($.fn.on !== void(0)) {
        $("html").on('hide.fieldset', callable);
        $("html").on('show.fieldset', callable);
    }
})(django.jQuery, parent.window.jQuery, parent.document);
