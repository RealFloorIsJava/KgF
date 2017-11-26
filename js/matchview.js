var sel = [];
var partResolver = {};

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

function loadParticipants() {
    $.ajax({
        method: "POST",
        url: "/global.php?page=match&action=participants",
        data: {}
    }).done(function(msg) {
        var list = $("#partlist");
        var jdata = JSON.parse(msg);
        for (var i = 0; i < jdata.length; i++) {
            var part = jdata[i];
            if (!partResolver.hasOwnProperty(part["id"])) {
                var newElem = $("<div><div></div><div></div><div></div><div></div></div>");
                partResolver[part["id"]] = newElem;
                newElem.addClass("part");
                newElem.children("div").eq(0).addClass("part-name");
                newElem.children("div").eq(1).addClass("part-score");
                newElem.children("div").eq(2).addClass("part-type");
                newElem.children("div").eq(3).addClass("part-status");
            }
            var elem = $(partResolver[part["id"]]);
            elem.children("div").eq(0).html(part["name"]);
            elem.children("div").eq(1).html("<b>" + part["score"] + "pts</b>");
            elem.children("div").eq(2).html("<i>???</i>");
            elem.children("div").eq(3).html("<i>???</i>");
            jdata[i] = elem;
        }
        list.empty().append(jdata);
    });
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
loadParticipants();

setInterval(heartbeat, 2000);
setInterval(loadParticipants, 1900);
