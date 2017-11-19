function heartbeat() {
    $.ajax({
        method: "POST",
        url: "/global.php?page=match&action=heartbeat",
        data: {}
    });
}

setInterval(heartbeat, 2000);
