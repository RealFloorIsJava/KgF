function enterACP(skip) {
    if (!skip) {
        var pw = prompt("Enter Admin CP password.");
        if (pw != null) {
            $.ajax({
                method: "POST",
                url: "/ajax.php?action=escalate",
                data: {
                    token: pw
                }
            }).done(function(msg) {
                window.location.assign("/admin.php");
            });
        }
    } else {
        window.location.assign("/admin.php");
    }
}

function changeName() {
    var newName = prompt("What name would you like to have?");
    if (newName != null && newName != "") {
        $.ajax({
            method: "POST",
            url: "/ajax.php?action=rename",
            data: {
                name: newName
            }
        }).done(function(msg) {
            document.getElementById("username").innerHTML = newName;
        });
    }
}
