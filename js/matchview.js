function heartbeat() {
    $.ajax({
        method: "POST",
        url: "/global.php?page=match&action=heartbeat",
        data: {}
    });
}

function pickTab(tab) {
    $(".hand-tab-header").removeClass("active-tab-header");
    $(".hand-area-set-row").css("display", "none");
    $("." + tab).css("display", "inherit");
    $("#" + tab).addClass("active-tab-header");
}

pickTab('tab-actions');

setInterval(heartbeat, 2000);
