function resetForm() {
    $('.message.error').addClass('hidden');
    $(".field").removeClass("error");
    $('.message.error ul')[0].innerHTML = "";
}

function validateFieldAt(id, regex, message) {
    if ($(`.field:eq(${id.toString()}) input`)[0].value.match(regex) == null) {
        $('.message.error').removeClass('hidden');
        $(`.field:eq(${id.toString()})`).addClass('error');
        var li = document.createElement("li");
        li.innerText = message;
        $(".message.error ul")[0].appendChild(li);
        return false;
    } else {
        return true;
    }
}

function validatePasswordFieldAt(id, message) {
    if ($(`.field:eq(${id.toString()}) input`)[0].value != $(`.field:eq(${id.toString()}) input`)[1].value) {
        $('.message.error').removeClass('hidden');
        $(`.field:eq(${id.toString()})`).addClass('error');
        var li = document.createElement("li");
        li.innerText = message;
        $(".message.error ul")[0].appendChild(li);
        return false;
    } else {
        return true;
    }
}

function hashFieldAt(id) {
    $(`.field:eq(${id.toString()}) input`)[0].value = CryptoJS.SHA1($(`.field:eq(${id.toString()}) input`)[0].value).toString();
}