(function(){
  var mExternalUpdateAllowed = true;
  var mSelectedCards = {};
  var mNumSelected = 0;
  var mNumGaps = 0;
  var mHandResolver = {
    "OBJECT": {},
    "VERB": {}
  };
  var allowChoose = false;
  var allowPick = false;

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
      method: "GET",
      url: "/api/status",
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
        allowPick = data["allowPick"];
      }
    });
  }

  function onPlayedClick(event) {
    if (!allowPick) {
      return;
    }
    $.ajax({
      method: "POST",
      url: "/global.php?page=match&action=pickwinner",
      data: {
        "playedId": event.data["playedId"]
      }
    });
  }

  function updatePlayed(played) {
    var area = $(".card-area-played");
    var sets = area.children(".card-area-set");
    if (sets.length == 0) {
      var set = $("<div></div>")
        .addClass("card-area-set")
        .css("display", "none")
        .attr("id", "played-id-1");
      area.prepend(set);
      sets = area.children(".card-area-set");
      area.on("click", "#played-id-1", {
        "playedId": 1
      }, onPlayedClick);
    }

    for (var key in played) {
      if (played.hasOwnProperty(key)) {
        while (key > sets.length) {
          var set = $("<div></div>")
            .addClass("card-area-set")
            .css("display", "none")
            .attr("id", "played-id-" + key);
          sets.last().after(set);
          sets = area.children(".card-area-set");
          area.on("click", "#played-id-" + key, {
            "playedId": key
          }, onPlayedClick);
        }
        var set = sets.eq(key - 1);
        set.empty();
        set.css("display", "none");
        for (var j = 0; j < played[key].length; j++) {
          var card = $("<div></div>").addClass("card-base");
          if (played[key][j].hasOwnProperty("redacted")) {
            card.addClass("system-card");
            card.prepend($("<div></div>").addClass("card-label").text("?"));
          } else {
            card.addClass(played[key][j]["type"].toLowerCase() + "-card");
            card.html(getFormatted(played[key][j]["text"]));
          }
          set.append(card);
          set.css("display", "flex");
        }
      }
    }
  }

  function updateHand(hand, type) {
    var lowerType = type.toLowerCase();
    var container = $("#" + lowerType + "-hand");
    var resolver = mHandResolver[type];
    var diff = symmetricKeyDifference(resolver, hand);

    if (mExternalUpdateAllowed) {
      for (var handId in hand) {
        if (hand.hasOwnProperty(handId)) {
          if (hand[handId]["chosen"] == null
              && resolver.hasOwnProperty(handId)) {
            unselectHandCard(resolver[handId]);
          }
        }
      }
    }

    for (var i = 0; i < diff.onlyB.length; i++) {
      var handId = diff.onlyB[i];

      var elem = $("<div></div>")
        .addClass("card-base")
        .addClass(lowerType + "-card")
        .attr("id", "hand-id-" + handId)
        .html(getFormatted(hand[handId]["text"]));

      if (hand[handId]["chosen"] != null) {
        selectHandCard(elem, hand[handId]["chosen"]);
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
      unselectHandCard(resolver[diff.onlyA[i]]);
      resolver[diff.onlyA[i]].remove();
    }

    var needsSystemCard = true;
    for (var handId in resolver) {
      if (resolver.hasOwnProperty(handId)) {
        needsSystemCard = false;
        container.children(".system-card").remove();
        break;
      }
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
      url: "/api/chat",
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
              ? "/res/images-bang-svg" : "/res/images-message-svg")
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
        mExternalUpdateAllowed = false;
        setTimeout(function(){
          mExternalUpdateAllowed = true;
        }, 1000);
        var remove = false;
        var card = mHandResolver["OBJECT"][handId]
          || mHandResolver["VERB"][handId];

        // Remove card choices
        for (var i = 0; i < 4; i++) {
          if (!mSelectedCards.hasOwnProperty(i)) {
            continue;
          }
          if (mSelectedCards[i] == card || remove) {
            unselectHandCard(mSelectedCards[i]);
            remove = true;
          }
        }

        // Mark new choices
        if (!remove) {
          if (mNumSelected < mNumGaps) {
            selectHandCard(card, mNumSelected);
          }
        }
      }
    });
  }

  function selectHandCard(card, k) {
    if (card.children(".card-label").length == 0) {
      card.prepend($("<div></div>").addClass("card-label").text("" + (k + 1)));
    } else {
      card.children(".card-label").text("" + (k + 1));
    }
    card.addClass("card-selected");
    mSelectedCards[k] = card;
    mNumSelected++;
  }

  function unselectHandCard(card) {
    card.children(".card-label").remove();
    card.removeClass("card-selected");
    for (var key in mSelectedCards) {
      if (mSelectedCards.hasOwnProperty(key)) {
        if (mSelectedCards[key] == card) {
          delete mSelectedCards[key];
          mNumSelected--;
          break;
        }
      }
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
          url: "/api/chat/send",
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
