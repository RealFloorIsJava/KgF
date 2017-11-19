var matchResolver = {};

function loadMatches() {
    $.ajax({
        method: "POST",
        url: "/global.php?page=ajax&action=matchlist",
        data: {}
    }).done(function(msg) {
        var list = $("#matchlist");
        var jdata = JSON.parse(msg);
        for (var i = 0; i < jdata.length; i++) {
            var match = jdata[i];
            if (!matchResolver.hasOwnProperty(match["id"])) {
                var newElem = $("<div><div></div><div></div></div>");
                matchResolver[match["id"]] = newElem;
                
                var btn = $("<button onclick=\"joinMatch(" + match["id"] + ")\"></button>").html("Join match");
                newElem.addClass("match-box");
                newElem.children("div").eq(0).append($("<b></b>'s match &mdash; <b></b> participants &mdash; Starting in <b></b> seconds...<span></span>"));
                newElem.children("div").eq(0).append($("<div></div>").css("float", "right").append(btn)).append($("<div></div>").css("clear", "both"));
                newElem.children("div").eq(1).append($("<b></b>'s match &mdash; <b></b> participants<span></span>"));
                newElem.children("div").eq(1).append($("<div></div>").css("float", "right").append($("<button></button>").prop("disabled", true).html("Match in progress"))).append($("<div></div>").css("clear", "both"));
            }
            var elem = $(matchResolver[match["id"]]);
            elem.children("div").eq(0).find("b").eq(0).html(match["owner"]);
            elem.children("div").eq(1).find("b").eq(0).html(match["owner"]);
            elem.children("div").eq(0).find("b").eq(1).html(match["participants"]);
            elem.children("div").eq(1).find("b").eq(1).html(match["participants"]);
            elem.children("div").eq(0).find("b").eq(2).html(match["seconds"]);
            elem.children("div").eq(0).css("display", match["started"] ? "none" : "inline");
            elem.children("div").eq(1).css("display", match["started"] ? "inline" : "none");
            jdata[i] = elem;
        }
        list.empty().append(jdata);
    });
}

function joinMatch(id) {
    window.location.assign("/global.php?page=match&action=join&match=" + id);
}

function createMatch() {
    window.location.assign("/global.php?page=match&action=create");
}

setInterval(loadMatches, 900);
