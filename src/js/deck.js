(function(){
  var mFileReader = null;
  var mIdCounter = 1;
  var mCards = [];
  var mCardNodes = [];
  var mEditId = 1;

  function markDirty() {
    window.onbeforeunload = function() {
        return 'Please make sure you save all unsaved data you want to keep!';
    };
  }

  function markClean() {
    window.onbeforeunload = null;
  }

  function openDeck() {
    var elem = $("#deckinput")[0];
    if (elem.files && elem.files[0]) {
      var file = elem.files[0];
      mFileReader = new FileReader();
      mFileReader.onload = displayDeck;
      mFileReader.readAsText(file);
    }
  }

  function displayDeck() {
    var lines = mFileReader.result.split(/\r|\n|\r\n/);
    clearCards();
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i].trim();
      if (line.length == 0) {
        continue;
      }
      displayCard(line.split(/\t/));
    }
  }

  function clearCards() {
    $("#deck-display").empty();
    mCcards = [];
    mCardNodes = [];
    mIdCounter = 1;
  }

  function createCard(anchor, tsv, curId, armed) {
    var node = $("<div></div>")
      .addClass("card-base")
      .addClass(tsv[1].toLowerCase() + "-card")
      .append($("<span></span>")
        .html(getFormatted(tsv[0]))
      );

    var tools = $("<div></div>")
      .addClass("card-id");

    if (armed) {
      var typeKnob = $("<a></a>")
        .addClass("knob-" + tsv[1].toLowerCase())
        .attr("href", "#")
        .attr("id", "knob-id-" + curId)
        .html("&nbsp;&nbsp;&nbsp;&nbsp;");
      tools.append(typeKnob).append(" - ");

      var editLink = $("<a></a>")
        .attr("href", "#")
        .html("Edit")
        .attr("id", "edit-id-" + curId);
      tools.append(editLink).append(" - ");

      var deleteLink = $("<a></a>")
        .attr("href", "#")
        .attr("id", "del-id-" + curId)
        .html("Delete");
      tools.append(deleteLink).append(" - ");

      if (anchor != null) {
        anchor.on("click", "#del-id-" + curId, {}, function() {
          node.remove();
          mCards[curId] = false;
          markDirty();
        });
        anchor.on("click", "#edit-id-" + curId, {}, function() {
          mEditId = curId;
          openEditor();
        });
        anchor.on("click", "#knob-id-" + curId, {}, function() {
          node.removeClass(mCards[curId][1].toLowerCase() + "-card");
          typeKnob.removeClass("knob-" + mCards[curId][1].toLowerCase());
          if (mCards[curId][1] == "STATEMENT") {
            mCards[curId][1] = "OBJECT";
          } else if (mCards[curId][1] == "OBJECT") {
            mCards[curId][1] = "VERB";
          } else if (mCards[curId][1] == "VERB") {
            mCards[curId][1] = "STATEMENT";
          }
          typeKnob.addClass("knob-" + mCards[curId][1].toLowerCase());
          node.addClass(mCards[curId][1].toLowerCase() + "-card");
          markDirty();
        });
      }
    }

    node.append(tools.append("#" + curId));
    return node;
  }

  function displayCard(tsv) {
    var curId = mIdCounter++;
    var node = createCard($("#deck-display"), tsv, curId, true);
    $("#deck-display").append(node);
    mCards[curId] = tsv;
    mCardNodes[curId] = node;
  }

  function addCard() {
    displayCard(["Card Text", "STATEMENT"]);
    mEditId = mIdCounter - 1;
    openEditor();
  }

  function sortCards() {
    var sorting = mCards.slice(0);
    sorting.sort(function(a, b) {
      if (!a || !b) {
        return (!a && !b) ? 0 : (!a ? -1 : 1);
      }
      return (a[1] == b[1]) ? 0 : (a[1] == "VERB" ? 1
        : (a[1] == "STATEMENT" ? -1 : (b[1] == "STATEMENT" ? 1 : -1)));
    });
    clearCards();
    for (var i = 0; i < sorting.length; i++) {
      if (sorting[i]) {
        displayCard(sorting[i]);
      }
    }
    markDirty();
  }

  function exportDeck() {
    var data = "";
    for (var i = 0; i < mIdCounter; i++) {
      if (mCards[i]) {
        data += mCards[i].join("\t") + "\n";
      }
    }
    if (data != "") {
      // hack for utf8
      download(unescape(encodeURIComponent(data)), "deck.tsv",
        "text/tab-separated-values");
    }
    markClean();
  }

  function openEditor() {
    $(".card-editor-container").css("display", "flex");
    $(".card-editor-card-display").empty().append(
      createCard(null, mCards[mEditId], mEditId, false));
    $("#card-text-input").val(mCards[mEditId][0]);
    $("#card-text-input").focus();
  }

  function closeEditor() {
    $(".card-editor-container").css("display", "none");
    mCards[mEditId][0] = $("#card-text-input").val();
    mCardNodes[mEditId].children("span").eq(0).html(
      getFormatted(mCards[mEditId][0]));
  }

  $("#openDeckButton").click(openDeck);
  $("#addCardButton").click(addCard);
  $("#sortCardsButton").click(sortCards);
  $("#exportDeckButton").click(exportDeck);
  $("#closeEditorButton").click(closeEditor);

  $("#card-text-input").bind("input", function() {
    var str = getFormatted($("#card-text-input").val());
    $(".card-editor-card-display").children("div").children("span").eq(0)
      .html(str);
  });
})();
