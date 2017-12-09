(function(){
  var mMatchResolver = {};

  function createMatchDIV(id) {
    var elem = $("<div></div>").addClass("match-box");

    var matchFloatClear = $("<div></div>").addClass("clearAfterFloat");
    var startingMatchButton = $("<div></div>")
      .addClass("rightFloat")
      .append($("<button></button>")
        .text("Join match")
        .click(function() {
          window.location.assign("/global.php?page=match&action=join&match="
            + id);
        })
      );

    var runningMatchButton = $("<div></div>")
      .addClass("rightFloat")
      .append($("<button></button>")
        .text("Match in progress")
        .prop("disabled", true)
      );

    var matchElem = $("<div></div>")
      .append($("<b></b>"))
      .append("'s match &mdash; ")
      .append($("<b></b>"))
      .append(" participants");

    elem.append(matchElem.clone()
      .append(" &mdash; Starting in ").append($("<b></b>")).append(" seconds...")
      .append(startingMatchButton)
      .append(matchFloatClear)
    );
    elem.append(matchElem
      .append(runningMatchButton)
      .append(matchFloatClear.clone())
    );
    return elem;
  }

  function displayMatches(json) {
    var matchList = $("#matchlist");
    for (var i = 0; i < json.length; i++) {
      var match = json[i];
      if (!mMatchResolver.hasOwnProperty(match["id"])) {
        mMatchResolver[match["id"]] = createMatchDIV(match["id"]);
      }
      var elem = mMatchResolver[match["id"]];

      var startingDIV = elem.children("div").eq(0);
      startingDIV.find("b").eq(0).html(match["owner"]);
      startingDIV.find("b").eq(1).html(match["participants"]);
      startingDIV.find("b").eq(2).html(match["seconds"]);
      startingDIV.addClass(match["started"] ? "invisible" : "inlineVisible");
      startingDIV.removeClass(match["started"] ? "inlineVisible" : "invisible");

      var runningDIV = elem.children("div").eq(1);
      runningDIV.find("b").eq(0).html(match["owner"]);
      runningDIV.find("b").eq(1).html(match["participants"]);
      runningDIV.addClass(match["started"] ? "inlineVisible" : "invisible");
      runningDIV.removeClass(match["started"] ? "invisible" : "inlineVisible");

      json[i] = elem;
    }
    matchList.empty().append(json);
  }

  function loadMatches() {
    $.ajax({
      method: "POST",
      url: "/global.php?page=dashboard&action=matchlist",
      dataType: "json",
      success: displayMatches
    });
  }

  $("#deckEditButton").click(function() {
    window.location.assign("/global.php?page=deckedit");
  });

  $("#nameChangeLabel").click(function() {
    var newName = prompt("What name would you like to have?");
    if (newName != null && newName != "" && newName.length < 32) {
      $("#username").text(newName);
      $.ajax({
        method: "POST",
        url: "/global.php?page=ajax&action=rename",
        data: {
          name: newName
        }
      });
    } else {
      alert("Invalid name!");
    }
  });

  setInterval(loadMatches, 900);
})();
