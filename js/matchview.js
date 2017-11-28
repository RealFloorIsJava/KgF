var sel = [];
var partResolver = {};
var chatId = 0;
var chatLock = false;
var countDown = 0;

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
  });
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
  var minutes = (Math.abs(Math.floor(countDown / 60)) + "").padStart(2, "0");
  var seconds = (Math.abs(countDown) % 60 + "").padStart(2, "0");
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

setInterval(loadParticipants, 5000);
setInterval(loadChat, 500);
setInterval(loadStatus, 5000);

setInterval(updateCountdown, 1000);
setInterval(function() { countDown--; }, 1000);
