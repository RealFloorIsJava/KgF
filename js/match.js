matchjs = new (function() {
  /**
   * Maps match IDs to match box elements (jQuery)
   */
  this.matchResolver = {};

  /**
   * Displays the fetched match list
   */
  this.displayMatches = function(msg) {
    var list = $("#matchlist");
    var jdata = JSON.parse(msg);
    for (var i = 0; i < jdata.length; i++) {
      var match = jdata[i];
      if (!this.matchResolver.hasOwnProperty(match["id"])) {
        var newElem = $("<div><div></div><div></div></div>");
        this.matchResolver[match["id"]] = newElem;

        var btn = $("<button onclick=\"joinMatch(" + match["id"]
          + ")\"></button>").html("Join match");
        newElem.addClass("match-box");
        newElem.children("div").eq(0).append(
          $("<b></b>'s match &mdash; <b></b> participants &mdash; "
            + "Starting in <b></b> seconds...<span></span>"));
        newElem.children("div").eq(0)
          .append($("<div></div>").css("float", "right").append(btn))
          .append($("<div></div>").css("clear", "both"));
        newElem.children("div").eq(1).append(
          $("<b></b>'s match &mdash; <b></b> participants<span></span>"));
        newElem.children("div").eq(1).append(
          $("<div></div>").css("float", "right").append(
            $("<button></button>").prop("disabled", true)
              .html("Match in progress")))
          .append($("<div></div>").css("clear", "both"));
      }
      var elem = $(this.matchResolver[match["id"]]);
      elem.children("div").eq(0).find("b").eq(0).html(match["owner"]);
      elem.children("div").eq(1).find("b").eq(0).html(match["owner"]);
      elem.children("div").eq(0).find("b").eq(1).html(match["participants"]);
      elem.children("div").eq(1).find("b").eq(1).html(match["participants"]);
      elem.children("div").eq(0).find("b").eq(2).html(match["seconds"]);
      elem.children("div").eq(0).css(
        "display", match["started"] ? "none" : "inline");
      elem.children("div").eq(1).css(
        "display", match["started"] ? "inline" : "none");
      jdata[i] = elem;
    }
    list.empty().append(jdata);
  };

  /**
   * Loads the match list
   */
  this.loadMatches = function() {
    $.ajax({
      method: "POST",
      url: "/global.php?page=dashboard&action=matchlist",
      data: {}
    }).done(function(msg) {
      this.displayMatches(msg);
    }.bind(this));
  };

  /**
   * Joins the match with the given ID
   */
  this.joinMatch = function(id) {
    window.location.assign("/global.php?page=match&action=join&match=" + id);
  };

  /**
   * Opens the deck editor
   */
  this.deckEditor = function() {
    window.location.assign("/global.php?page=deckedit");
  }
})();

setInterval(function() {
  matchjs.loadMatches();
}, 900);
