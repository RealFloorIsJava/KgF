var sel = [];

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

function toggleSelect(o) {
    var remove = false;
    for (var i = 0; i < sel.length; i++) {
        if (sel[i] == o) {
            // Need sync with server
            $(o).children(".card-select").eq(0).remove();
            $(o).removeClass("card-selected");
            sel.splice(i, 1);
            remove = true;
        }
    }
    if (!remove) {        
        if (sel.length < 3) { // todo magic
            sel.push(o);
            $(o).addClass("card-selected");
            $(o).prepend($("<div class=\"card-select\">?</div>"));
        }
    }
    for (var i = 0; i < sel.length; i++) {
        $(sel[i]).children(".card-select").eq(0).html(i + 1);
    }
}

pickTab('tab-actions');

setInterval(heartbeat, 2000);
