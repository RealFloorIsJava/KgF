var deckjs = new (function(){
  /**
   * The file reader that is used for deck parsing
   */
  this.fileReader = null;
  /**
   * The ID for the next card
   */
  this.idCounter = 1;
  /**
   * The cards as TSV arrays
   */
  this.cards = [];
  /**
   * The jQuery elements representing the cards
   */
  this.cardNodes = [];
  /**
   * The ID of the card currently being edited
   */
  this.editId = 1;

  /**
   * Marks the deck editor as dirty and requires a close confirmation
   */
  this.markDirty = function() {
    window.onbeforeunload = function() {
        return 'Please make sure you save all unsaved data you want to keep!';
    };
  };

  /**
   * Marks the deck editor as clean
   */
  this.markClean = function() {
    window.onbeforeunload = null;
  };

  /**
   * Opens the deck file
   */
  this.openDeck = function() {
    var elem = $("#deckinput")[0];
    if (elem.files && elem.files[0]) {
      var file = elem.files[0];
      this.fileReader = new FileReader();
      this.fileReader.onload = (function() {
        this.displayDeck();
      }).bind(this);
      this.fileReader.readAsText(file);
    }
  };

  /**
   * Displays the deck that was read by the FileReader
   */
  this.displayDeck = function() {
    var lines = this.fileReader.result.split(/\r|\n|\r\n/);
    this.clearCards();
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i].trim();
      if (line.length == 0) {
        continue;
      }
      this.displayCard(line.split(/\t/));
    }
  };

  /**
   * Clears all cards from the card display
   */
  this.clearCards = function() {
    $("#deck-display").empty();
    this.cards = [];
    this.cardNodes = [];
    this.idCounter = 1;
  };

  /**
   * Creates a card from the given TSV array with the given ID.
   * If armed is set to true then the card will contain the editing tools.
   */
  this.createCard = function(tsv, curId, armed) {
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
        .html("&nbsp;&nbsp;&nbsp;&nbsp;")
        .click((function() {
          node.removeClass(this.cards[curId][1].toLowerCase() + "-card");
          typeKnob.removeClass("knob-" + this.cards[curId][1].toLowerCase());
          if (this.cards[curId][1] == "STATEMENT") {
            this.cards[curId][1] = "OBJECT";
          } else if (this.cards[curId][1] == "OBJECT") {
            this.cards[curId][1] = "VERB";
          } else if (this.cards[curId][1] == "VERB") {
            this.cards[curId][1] = "STATEMENT";
          }
          typeKnob.addClass("knob-" + this.cards[curId][1].toLowerCase());
          node.addClass(this.cards[curId][1].toLowerCase() + "-card");
          this.markDirty();
        }).bind(this));
      tools.append(typeKnob).append(" - ");

      var editLink = $("<a></a>")
        .attr("href", "#")
        .html("Edit")
        .click((function() {
          this.editId = curId;
          this.openEditor();
        }).bind(this));
      tools.append(editLink).append(" - ");

      var deleteLink = $("<a></a>")
        .attr("href", "#")
        .html("Delete")
        .click((function() {
          node.remove();
          this.cards[curId] = false;
          this.markDirty();
        }).bind(this));
      tools.append(deleteLink).append(" - ");
    }

    node.append(tools.append("#" + curId));
    return node;
  };

  /**
   * Displays the given card in the deck card list
   */
  this.displayCard = function(tsv) {
    var curId = this.idCounter++;
    var node = this.createCard(tsv, curId, true);
    $("#deck-display").append(node);
    this.cards[curId] = tsv;
    this.cardNodes[curId] = node;
  };

  /**
   * Adds a new card to the deck and opens it for editing
   */
  this.addCard = function() {
    this.displayCard(["Text", "STATEMENT"]);
    this.editId = this.idCounter - 1;
    this.openEditor();
  };

  /**
   * Sorts the cards by card type
   */
  this.sortCards = function() {
    var sorting = this.cards.slice(0);
    sorting.sort(function(a, b) {
      if (!a || !b) {
        return (!a && !b) ? 0 : (!a ? -1 : 1);
      }
      return (a[1] == b[1]) ? 0 : (a[1] == "VERB" ? 1
        : (a[1] == "STATEMENT" ? -1 : (b[1] == "STATEMENT" ? 1 : -1)));
    });
    this.clearCards();
    for (var i = 0; i < sorting.length; i++) {
      if (sorting[i]) {
        this.displayCard(sorting[i]);
      }
    }
    this.markDirty();
  };

  /**
   * Exports the current deck to a file
   */
  this.exportDeck = function() {
    var data = "";
    for (var i = 0; i < this.idCounter; i++) {
      if (this.cards[i]) {
        data += this.cards[i].join("\t") + "\n";
      }
    }
    if (data != "") {
      // hack for utf8
      download(unescape(encodeURIComponent(data)), "deck.tsv", "text/tab-separated-values");
    }
    this.markClean();
  };

  /**
   * Opens the card editor
   */
  this.openEditor = function() {
    $(".card-editor-container").css("display", "flex");
    $(".card-editor-card-display").empty().append(
      this.createCard(this.cards[this.editId], this.editId, false));
    $("#card-text-input").val(this.cards[this.editId][0]);
    $("#card-text-input").focus();
  };

  /**
   * Closes the card editor
   */
  this.closeEditor = function() {
    $(".card-editor-container").css("display", "none");
    this.cards[this.editId][0] = $("#card-text-input").val();
    this.cardNodes[this.editId].children("span").eq(0).html(
      getFormatted(this.cards[this.editId][0]));
  };
})();

$("#card-text-input").bind("input", function() {
  var str = getFormatted($("#card-text-input").val());
  $(".card-editor-card-display").children("div").children("span").eq(0)
    .html(str);
});
