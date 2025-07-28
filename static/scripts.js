$('#chat-form').submit(function(e) {
    e.preventDefault();
    const msg = $('#message').val();
    const lang = $('#lang').val();
    $('#chat-box').append(`<p><b>You:</b> ${msg}</p>`);
    $('#message').val('');
    $.post('/ask', { message: msg, lang: lang }, function(data) {
        $('#chat-box').append(`<p><b>Bot:</b> ${data.answer}</p>`);
        $('#chat-box').scrollTop($('#chat-box')[0].scrollHeight);
    });
});

function downloadChat() {
    window.location.href = '/download';
}
