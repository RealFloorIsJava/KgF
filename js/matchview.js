var sel = [];
var partResolver = {};
var chatId = 0;
var chatLock = false;
var countDown = 0;
var ending = false;
var intervalParticipants;
var intervalStatus;
var handResolver = {
  OBJECT: {},
  VERB: {}
};

function pickTab(tab) {
  $(".hand-tab-header").removeClass("active-tab-header");
  $(".hand-area-set-row").css("display", "none");
  $("." + tab).css("display", "inherit");
  $("#" + tab).addClass("active-tab-header");
}

function sendChat() {
  var text = $("#chatinput").val();
  $("#chatinput").val("");
  if (text.length > 0) {
    $.ajax({
      method: "POST",
      url: "/global.php?page=match&action=chatsend",
      data: {
        message: text
      }
    });
  }
}

function loadStatus() {
  $.ajax({
    method: "POST",
    url: "/global.php?page=match&action=status",
    data: {}
  }).done(function(msg) {
    var jdata = JSON.parse(msg);
    countDown = jdata["timer"];
    $("#matchstatus").html(jdata["status"]);
    ending = jdata["ending"];
    if (ending) {
      clearInterval(intervalParticipants);
      clearInterval(intervalStatus);
    }

    var elem = $("#match-statement");
    if (jdata["hasCard"]) {
      var format = getFormatted(jdata["cardText"]);
      elem.html(format);
      if (elem.hasClass("system-card")) {
        $("#match-statement").addClass("statement-card");
        $("#match-statement").removeClass("system-card");
      }
    } else {
      elem.html("Waiting...");
      if (elem.hasClass("statement-card")) {
        $("#match-statement").removeClass("statement-card");
        $("#match-statement").addClass("system-card");
      }
    }

    updateHand(jdata["hand"]["OBJECT"], "OBJECT");
    updateHand(jdata["hand"]["VERB"], "VERB");
  });
}

function updateHand(hand, type) {
  var lowerType = type.toLowerCase();
  var container = $("#" + lowerType + "-hand");

  var marks = {};
  for (var handId in handResolver[type]) {
    marks[handId] = true;
  }

  for (var handId in hand) {
    if (!marks.hasOwnProperty(handId)) {
      var elem = $("<div></div>");
      elem.addClass("card-base").addClass(lowerType + "-card");
      (function(){
        var htmlElem = elem[0];
        elem.click(function(){
          toggleSelect(htmlElem);
        });
      })();
      elem.html(getFormatted(hand[handId]));
      container.append(elem);
      handResolver[type][handId] = elem;
    }
    if (marks.hasOwnProperty(handId)) {
      delete marks[handId];
    }
  }

  for (var handId in marks) {
    handResolver[type][handId].remove();
  }

  var needsSystemCard = true;
  for (var handId in handResolver[type]) {
    needsSystemCard = false;
    container.children(".system-card").remove();
    break;
  }
  if (needsSystemCard) {
    var sysCard = $("<div></div>");
    sysCard.addClass("card-base").addClass("system-card");
    sysCard.html("No cards on your hand.");
    container.append(sysCard);
  }
}

function loadChat() {
  if (chatLock) {
    return;
  }
  chatLock = true;
  $.ajax({
    method: "POST",
    url: "/global.php?page=match&action=chat",
    data: {
      offset: chatId
    }
  }).done(function(msg) {
    var list = $("#chatlist");
    var shouldScroll =
      list.scrollTop() + list.innerHeight() >= list.get(0).scrollHeight - 50;
    var jdata = JSON.parse(msg);
    for (var i = 0; i < jdata.length; i++) {
      var part = jdata[i];
      var elem = $("<div><img><span></span></div>");
      elem.children("img").attr("src",
        part["type"] == "SYSTEM" ? "/img/bang.svg" : "/img/message.svg");
      elem.children("img").addClass("chat-svg");
      elem.children("span").addClass("chat-msg").html(part["message"]);

      chatId = part["id"] + 1;
      jdata[i] = elem;
    }
    list.append(jdata);
    if (shouldScroll && jdata.length > 0) {
      list.scrollTop(list.get(0).scrollHeight + list.innerHeight());
    }
    chatLock = false;
  });
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
        var newElem =
          $("<div><div></div><div></div><div></div><div></div></div>");
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
      if (part["picking"]) {
        elem.children("div").eq(2).html("<i>Picking</i>");
      } else {
        elem.children("div").eq(2).html("<i>&nbsp;</i>");
      }
      elem.children("div").eq(3).html("<i>???</i>");
      jdata[i] = elem;
    }
    list.empty().append(jdata);
  });
}

function toggleSelect(o) {
  var remove = false;
  for (var i = 0; i < sel.length; i++) {
    if (sel[i] == o || remove) {
      // Need sync with server
      $(sel[i]).children(".card-select").eq(0).remove();
      $(sel[i]).removeClass("card-selected");
      sel.splice(i--, 1);
      remove = true;
    }
  }
  if (!remove) {
    if (sel.length < 3) { // TODO magic
      sel.push(o);
      $(o).addClass("card-selected");
      $(o).prepend($("<div class=\"card-select\">?</div>"));
    }
  }
  for (var i = 0; i < sel.length; i++) {
    $(sel[i]).children(".card-select").eq(0).html(i + 1);
  }
}

function updateCountdown() {
  var minutes = (Math.max(0, Math.floor(countDown / 60)) + "").padStart(2, "0");
  var seconds = (Math.max(0, countDown) % 60 + "").padStart(2, "0");
  $("#countdown").html(minutes + ":" + seconds);
}

$('#chatinput').keypress(function (e) {
  var key = e.which;
  if (key == 13) {
    sendChat();
  }
});

pickTab('tab-actions');
loadStatus();
loadParticipants();

intervalParticipants = setInterval(loadParticipants, 5000);
setInterval(loadChat, 500);
intervalStatus = setInterval(loadStatus, 2000);

setInterval(function() {
  countDown--;
  updateCountdown();
  if (countDown == 0 && ending) {
    window.location.assign("/global.php");
  }
}, 1000);
