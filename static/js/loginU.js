$("form").submit(function () {
    resetForm();
    if (validateFieldAt(0, /^.+$/, "Username must be non-empty.") &&
        validateFieldAt(1, /^.+$/, "Password must be non-empty.")
    ) {
        hashFieldAt(1);
        return true;
    } else {
        return false;
    }
});
