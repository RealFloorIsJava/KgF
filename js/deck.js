var fr = null;
var idCounter = 1;
var cards = [];
var cardNodes = [];
var editId = 1;

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
    fr = new FileReader();
    fr.onload = displayDeck;
    fr.readAsText(file);
  }
}

function displayDeck() {
  var lines = fr.result.split(/\r|\n|\r\n/);

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
  cards = [];
  cardNodes = [];
  idCounter = 1;
}

function createCard(tsv, curId, armed) {
  var node = $("<div></div>");
  node.addClass("card-base");
  node.addClass(tsv[1].toLowerCase() + "-card");
  node.append($("<span></span>").html(getFormatted(tsv[0])));

  var tools = $("<div></div>");
  tools.addClass("card-id");

  if (armed) {
    var typeKnob = $("<a></a>");
    typeKnob.addClass("knob-" + tsv[1].toLowerCase());
    typeKnob.attr("href", "#");
    typeKnob.html("&nbsp;&nbsp;&nbsp;&nbsp;");
    typeKnob.click(function() {
      node.removeClass(cards[curId][1].toLowerCase() + "-card");
      typeKnob.removeClass("knob-" + cards[curId][1].toLowerCase());
      if (cards[curId][1] == "STATEMENT") {
        cards[curId][1] = "OBJECT";
      } else if (cards[curId][1] == "OBJECT") {
        cards[curId][1] = "VERB";
      } else if (cards[curId][1] == "VERB") {
        cards[curId][1] = "STATEMENT";
      }
      typeKnob.addClass("knob-" + cards[curId][1].toLowerCase());
      node.addClass(cards[curId][1].toLowerCase() + "-card");
      markDirty();
    });
    tools.append(typeKnob);
    tools.append(" - ");
    var editLink = $("<a></a>");
    editLink.attr("href", "#");
    editLink.html("Edit");
    editLink.click(function() {
      editId = curId;
      openEditor();
    });
    tools.append(editLink);
    tools.append(" - ");
    var deleteLink = $("<a></a>");
    deleteLink.attr("href", "#");
    deleteLink.html("Delete");
    deleteLink.click(function() {
      node.remove();
      cards[curId] = false;
      markDirty();
    });
    tools.append(deleteLink);
    tools.append(" - ");
  }

  tools.append("#" + curId);

  node.append(tools);
  return node;
}

function displayCard(tsv) {
  var curId = idCounter++;
  var node = createCard(tsv, curId, true);
  $("#deck-display").append(node);
  cards[curId] = tsv;
  cardNodes[curId] = node;
}

function addCard() {
  displayCard(["Text", "STATEMENT"]);
  editId = idCounter - 1;
  openEditor();
}

function sortCards() {
  var sorting = cards.slice(0);
  sorting.sort(function(a, b) {
    if (!a && !b) {
      return 0;
    }
    if (!a) {
      return -1;
    }
    if (!b) {
      return 1;
    }
    if (a[1] == b[1]) {
      return 0;
    }
    if (a[1] == "STATEMENT") {
      return -1;
    }
    if (a[1] == "VERB") {
      return 1;
    }
    if (a[1] == "OBJECT") {
      return b[1] == "STATEMENT" ? 1 : -1;
    }
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
  if (cards.length > 0) {
    var data = "";
    for (var i = 0; i < idCounter; i++) {
      if (cards[i]) {
        data += cards[i].join("\t") + "\n";
      }
    }
    download(data, "deck.tsv", "text/tab-separated-values");
  }
  markClean();
}

function openEditor() {
  $(".card-editor-container").css("display", "flex");
  $(".card-editor-card-display").empty().append(
    createCard(cards[editId], editId, false));
  $("#card-text-input").val(cards[editId][0]);
  $("#card-text-input").focus();
}

function closeEditor() {
  $(".card-editor-container").css("display", "none");
  cards[editId][0] = $("#card-text-input").val();
  cardNodes[editId].children("span").eq(0).html(getFormatted(cards[editId][0]));
}

function getFormatted(str) {
  return str.replace(/\|/g, "&shy;").replace(/_/g,
    "<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>");
}

$("#card-text-input").bind("input", function() {
  var str = getFormatted($("#card-text-input").val());
  $(".card-editor-card-display").children("div").children("span").eq(0)
    .html(str);
});
