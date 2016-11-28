$(function() {
    $('[data-toggle="tooltip"]').tooltip()
})

// https://docs.djangoproject.com/en/1.10/ref/csrf/#ajax
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
var csrftoken = getCookie('csrftoken');
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
})

function apiRequest(apiPath, method, data, blocking, blockingMessage) {
    if (blocking) {
        $.blockUI({ message: (blockingMessage || "Please Wait…") })
    }
    return $.ajax({
        url: window.apiUrlPrefix + '/api/' + apiPath,
        type: method,
        contentType: 'application/json',
        data: JSON.stringify(data),
    })
        .always(function() {
            $.unblockUI()
        })

    // TODO: Show error messages.
}
