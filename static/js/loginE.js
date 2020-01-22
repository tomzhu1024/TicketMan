$("form").submit(function () {
    resetForm();
    if (validateFieldAt(0, /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/, "Email must be in the format of someone@example.com.") &&
        validateFieldAt(1, /^.+$/, "Password must be non-empty.")
    ) {
        hashFieldAt(1);
        return true;
    } else {
        return false;
    }
});
