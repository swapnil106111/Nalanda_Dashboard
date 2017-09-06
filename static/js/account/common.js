if (typeof toastr !== 'undefined') {
    toastr.options = {
        "closeButton": true,
        "debug": false,
        "positionClass": "toast-top-right",
        "onclick": null,
        "showDuration": "1000",
        "hideDuration": "1000",
        "timeOut": "100000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    };
}

$(document).ready(function() {
    var maxVal = function(a, b) {
        return a > b ? a : b;
    };
    var resizeSiteContent = function() {
        $('.site-content')[0].style.minHeight = maxVal($('.site-sidebar').height(), $(window).height()) + 'px';
    };
    resizeSiteContent();
    $(window).on('resize', resizeSiteContent);
});