(function(){
  var mSelectedCards = [];
  var mNumGaps = 0;
  var mHandResolver = {
    "OBJECT": {},
    "VERB": {}
  };
  var allowChoose = false;

  var mParticipantResolver = {};

  var mMinimumChatId = 0;
  var mChatLock = false;

  var mCountDown = 0;
  var mEnding = false;

  var mIntervalParticipants = 0;
  var mIntervalStatus = 0;
  var mIntervalFetchCards = 0;


  function startTasks() {
    mIntervalParticipants = setInterval(loadParticipants, 5000);
    mIntervalStatus = setInterval(loadStatus, 2000);
    mIntervalFetchCards = setInterval(fetchCards, 1750);
  }

  function fetchCards() {
    $.ajax({
      method: "POST",
      url: "/global.php?page=match&action=fetchcards",
      dataType: "json",
      success: function(data) {
        updateHand(data["hand"]["OBJECT"], "OBJECT");
        updateHand(data["hand"]["VERB"], "VERB");
        updatePlayed(data["played"]);
      }
    });
  }

  function loadStatus() {
    $.ajax({
      method: "POST",
      url: "/global.php?page=match&action=status",
      dataType: "json",
      success: function(data) {
        mCountDown = data["timer"];
        $("#matchstatus").html(data["status"]);
        mEnding = data["ending"];
        if (mEnding) {
          clearInterval(mIntervalParticipants);
          clearInterval(mIntervalStatus);
          clearInterval(mIntervalFetchCards);
        }

        var elem = $("#match-statement");
        if (data["hasCard"]) {
          var format = getFormatted(data["cardText"]);
          elem.html(format);
          if (elem.hasClass("system-card")) {
            $("#match-statement").addClass("statement-card")
              .removeClass("system-card");
          }
        } else {
          elem.text("Waiting...");
          if (elem.hasClass("statement-card")) {
            $("#match-statement").removeClass("statement-card")
              .addClass("system-card");
          }
        }

        mNumGaps = data["gaps"];
        allowChoose = data["allowChoose"];
      }
    });
  }

  function updatePlayed(played) {
    var area = $(".card-area-played");
    var sets = area.children(".card-area-set");
    if (sets.length == 0) {
      area.prepend($("<div></div>").addClass("card-area-set"));
      sets = area.children(".card-area-set");
    }
    for (var i = 0; i < played.length; i++) {
      if (i >= sets.length) {
        sets.last().after($("<div></div>").addClass("card-area-set"));
        sets = area.children(".card-area-set");
      }
      var set = sets.eq(i);
      set.empty();
      for (var j = 0; j < played[i].length; j++) {
        var card = $("<div></div>").addClass("card-base");
        if (played[i][j].hasOwnProperty("redacted")) {
          card.addClass("system-card");
          card.prepend($("<div></div>").addClass("card-label").text("?"));
        } else {
          card.addClass(played[i][j]["type"].toLowerCase() + "-card");
          card.html(getFormatted(played[i][j]["text"]));
        }
        set.append(card);
      }
    }
  }

  function updateHand(hand, type) {
    var lowerType = type.toLowerCase();
    var container = $("#" + lowerType + "-hand");
    var resolver = mHandResolver[type];
    var diff = symmetricKeyDifference(resolver, hand);

    for (var i = 0; i < diff.onlyB.length; i++) {
      var handId = diff.onlyB[i];

      var elem = $("<div></div>")
        .addClass("card-base")
        .addClass(lowerType + "-card")
        .attr("id", "hand-id-" + handId)
        .html(getFormatted(hand[handId]["text"]));

      if (hand[handId]["chosen"] != null) {
        var offset = hand[handId]["chosen"];
        while (mSelectedCards.length < offset + 1) {
          mSelectedCards.push(null);
        }
        mSelectedCards[offset] = elem;
        var select = $("<div></div>").addClass("card-label").text("?");
        elem.addClass("card-selected").prepend(select);
      }

      container.on("click", "#hand-id-" + handId, {
        "handId": handId
      }, function(event) {
        toggleSelect(event.data["handId"]);
      });

      container.append(elem);
      resolver[handId] = elem;
    }

    for (var i = 0; i < diff.onlyA.length; i++) {
      for (var j = 0; j < mSelectedCards.length; j++) {
        if (resolver[diff.onlyA[j]] == mSelectedCards[j]) {
          mSelectedCards.splice(j, 1);
          break;
        }
      }
      resolver[diff.onlyA[i]].remove();
    }

    updateSelectLabels();

    var needsSystemCard = true;
    for (var handId in resolver) {
      needsSystemCard = false;
      container.children(".system-card").remove();
      break;
    }
    if (needsSystemCard) {
      var sysCard = $("<div></div>")
        .addClass("card-base")
        .addClass("system-card")
        .text("No cards on your hand.");
      container.empty().append(sysCard);
    }
  }

  function loadChat() {
    if (mChatLock) {
      return;
    }
    mChatLock = true;
    $.ajax({
      method: "POST",
      url: "/global.php?page=match&action=chat",
      data: {
        offset: mMinimumChatId
      },
      dataType: "json",
      success: function(data) {
        var list = $("#chatlist");
        var shouldScroll = list.scrollTop()
          + list.innerHeight() >= list.get(0).scrollHeight - 50;
        for (var i = 0; i < data.length; i++) {
          var img = $("<img>")
            .attr("src", data[i].type == "SYSTEM"
              ? "/img/bang.svg" : "/img/message.svg")
            .addClass("chat-svg");
          var span = $("<span></span>")
            .addClass("chat-msg")
            .html(data[i].message);
          var elem = $("<div></div>").append(img).append(span);

          mMinimumChatId = data[i].id + 1;
          data[i] = elem;
        }
        list.append(data);
        if (shouldScroll && data.length > 0) {
          list.scrollTop(list.get(0).scrollHeight + list.innerHeight());
        }
        mChatLock = false;
      }
    });
  }

  function loadParticipants() {
    $.ajax({
      method: "POST",
      url: "/global.php?page=match&action=participants",
      dataType: "json",
      success: function(data) {
        var list = $("#partlist");
        for (var i = 0; i < data.length; i++) {
          if (!mParticipantResolver.hasOwnProperty(data[i].id)) {
            var name = $("<div></div>").addClass("part-name");
            var score = $("<div></div>").addClass("part-score");
            var type = $("<div></div>").addClass("part-type");
            var status = $("<div></div>").addClass("part-status");
            var newElem = $("<div></div>")
              .addClass("part")
              .append(name)
              .append(score)
              .append(type)
              .append(status);
            mParticipantResolver[data[i].id] = newElem;
          }
          var elem = mParticipantResolver[data[i].id];
          elem.children("div").eq(0).text(data[i].name);
          elem.children("div").eq(1).text(data[i].score + "pts");
          elem.children("div").eq(2)
            .text(data[i].picking ? "Picking" : "");
          // elem.children("div").eq(3).text("???");
          data[i] = elem;
        }
        list.empty().append(data);
      }
    });
  }

  function toggleSelect(handId) {
    if (!allowChoose) {
      return;
    }
    $.ajax({
      method: "POST",
      url: "/global.php?page=match&action=togglechoose",
      data: {
        "handId": handId
      },
      success: function() {
        var remove = false;
        var card = mHandResolver["OBJECT"][handId]
          || mHandResolver["VERB"][handId];

        // Remove card choices
        for (var i = 0; i < mSelectedCards.length; i++) {
          if (mSelectedCards[i] == card || remove) {
            mSelectedCards[i].removeClass("card-selected")
              .children(".card-label").eq(0).remove();
            mSelectedCards.splice(i--, 1);
            remove = true;
          }
        }

        // Mark new choices
        if (!remove) {
          if (mSelectedCards.length < mNumGaps) {
            mSelectedCards.push(card);
            var select = $("<div></div>").addClass("card-label").text("?");
            card.addClass("card-selected").prepend(select);
          }
        }

        updateSelectLabels();
      }
    });
  }

  function updateSelectLabels() {
    // Update the numbers on the cards
    for (var i = 0; i < mSelectedCards.length; i++) {
      mSelectedCards[i].children(".card-label").eq(0).text(i + 1);
    }
  }

  function updateCountdown() {
    var minutes = (Math.max(0, Math.floor(mCountDown / 60)) + "")
      .padStart(2, "0");
    var seconds = (Math.max(0, mCountDown) % 60 + "").padStart(2, "0");
    $("#countdown").text(minutes + ":" + seconds);
  }

  function pickTab(tab) {
    $(".hand-tab-header").removeClass("active-tab-header");
    $(".hand-area-set-row").css("display", "none");
    $("." + tab).css("display", "inherit");
    $("#" + tab).addClass("active-tab-header");
  }

  $('#chatinput').keypress(function (e) {
    var key = e.which;
    if (key == 13) {
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
  });

  $("#tab-actions").click(function() {
    pickTab("tab-actions");
  });

  $("#tab-objects").click(function() {
    pickTab("tab-objects");
  });

  loadStatus();
  loadParticipants();
  startTasks();
  pickTab('tab-actions');

  setInterval(loadChat, 500);
  setInterval(function() {
    mCountDown--;
    updateCountdown();
    if (mCountDown == 0 && mEnding) {
      window.location.assign("/global.php");
    }
  }, 1000);
})();
