/**
 * Part of KgF.
 *
 * MIT License
 * Copyright (c) 2017 LordKorea
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */
"use strict";

(function(){
  let fileReader = null
  let idCounter = 1
  let cards = new Map()
  let editId = -1
  let isAddEdit = false

  /**
   * Represents a card in a deck.
   */
  class Card {

    /**
     * Constructor.
     *
     * @param text The text of the card.
     * @param type The type of the card.
     * @param node The DOM element of the card in the editor.
     */
    constructor(text, type, node) {
      this.text = text
      this.type = type
      this.node = node
    }

    /**
     * Removes events for this card for the associated ID
     *
     * @param id The ID.
     */
    removeEvents(id) {
      $(document).off("click", `#del-id-${id}`)
      $(document).off("click", `#knob-id-${id}`)
      $("#deck-display").off("click", `#edit-id-${id}`)
    }
  }

  /**
   * Loads a deck from a file and displays it.
   */
  function openDeck() {
    if (window.onbeforeunload !== null) {
      let chk = confirm("You have unsaved changes. Continue?")
      if (!chk) {
        return
      }
    }
    let finput = $("#deckinput")[0]
    if (finput.files && finput.files[0]) {
      let file = finput.files[0]
      fileReader = new FileReader()
      fileReader.onload = displayDeck
      fileReader.readAsText(file)
    }
  }

  /**
   * Displays the deck that has been loaded from the file.
   */
  function displayDeck() {
    let lines = fileReader.result.split(/\r|\n|\r\n/)
    clearCards()
    for (let i = 0; i < lines.length; i++) {
      let line = lines[i].trim()
      if (line.length === 0) {
        continue
      }
      displayCard(line.split(/\t/))
    }
  }

  /**
   * Displays a card for the given TSV data.
   *
   * New cards are prepended to the editor.
   *
   * @param tsv The TSV data as an array.
   * @param prepend Whether to prepend the card.
   */
  function displayCard(tsv, prepend=false) {
    let curId = idCounter++
    let node = createCard(tsv, curId, true)
    if (prepend) {
      $("#deck-display").prepend(node)
    } else {
      $("#deck-display").append(node)
    }
    cards.set(curId, new Card(tsv[0], tsv[1], node))
  }

  /**
   * Creates a card in the editor view.
   *
   * @param tsv The TSV data for the card.
   * @param id The ID of the card.
   */
  function createCard(tsv, id) {
    const text = applyCardTextFormat(tsv[0])
    const type = tsv[1].toLowerCase()
    $(document).on("click", `#del-id-${id}`, {}, () => deleteCard(id))
    $(document).on("click", `#knob-id-${id}`, {}, () => triggerKnob(id))
    // Setting this handler to the deck display prevents editing when the card
    // is in the editor
    $("#deck-display").on("click", `#edit-id-${id}`, {}, () => editCard(id))
    let prefId = ("" + id).padStart(4, "0")
    return (
      $("<div></div>", {
          "class": `card-base ${type}-card`,
          "id": `card-id-${id}`
        }).append([
        $("<span></span>").html(text),
        $("<div></div>", {"class": "card-id"}).append([
          ($("<span></span>", {"class": `knob-${type}`})
            .attr("id", `knob-id-${id}`)
            .html("&nbsp;&nbsp;&nbsp;&nbsp;")),
          " - ",
          ($("<span>Edit</span>").addClass("fake-anchor")
            .attr("id", `edit-id-${id}`)),
          " - ",
          ($("<span>Delete</span>").addClass("fake-anchor")
            .attr("id", `del-id-${id}`)),
          " - ",
          `#${prefId}`
        ])
      ])
    )
  }

  /**
   * Deletes the card with the given ID.
   *
   * @param id The ID of the card.
   */
  function deleteCard(id) {
    if (id === editId) {
      closeEditor()
    }
    cards.get(id).removeEvents(id)
    cards.get(id).node.remove()
    cards.delete(id)
    markDirty()
  }

  /**
   * Opens the card for editing.
   *
   * @param id The ID of the card.
   */
  function editCard(id) {
    editId = id
    openEditor()
  }

  /**
   * Opens the card detail editor.
   */
  function openEditor() {
    let card = cards.get(editId)
    $(".card-editor-container").removeClass("invisible")
    $("#card-text-input").val(card.text)
    $("#card-text-input").focus()

    // Reattach the card that should be edited
    card.node.appendTo($(".card-editor-card-display"))
  }

  /**
   * Triggers the type knob of the card with the given ID.
   *
   * @param id The ID of the card.
   */
  function triggerKnob(id) {
    const successors = {
      "STATEMENT": "OBJECT",
      "OBJECT": "VERB",
      "VERB": "STATEMENT"
    }
    let card = cards.get(id)
    let typeKnob = $(`#knob-id-${id}`)
    card.node.removeClass(`${card.type.toLowerCase()}-card`)
    typeKnob.removeClass(`knob-${card.type.toLowerCase()}`)
    card.type = successors[card.type]
    typeKnob.addClass(`knob-${card.type.toLowerCase()}`)
    card.node.addClass(`${card.type.toLowerCase()}-card`)
    markDirty()
  }

  /**
   * Removes all cards from the display and resets the editor.
   */
  function clearCards() {
    for (let [id, card] of cards.entries()) {
      card.removeEvents(id)
    }
    $("#deck-display").empty()
    cards.clear()
    idCounter = 1
  }

  /**
   * Sorts the cards by type.
   */
  function sortCards() {
    const rank = {
      "STATEMENT": {
        "STATEMENT": 0,
        "OBJECT": -1,
        "VERB": -1
      },
      "OBJECT": {
        "STATEMENT": 1,
        "OBJECT": 0,
        "VERB": -1
      },
      "VERB": {
        "STATEMENT": 1,
        "OBJECT": 1,
        "VERB": 0
      }
    }
    let sorting = []
    for (let card of cards.values()) {
      sorting.push(card)
    }
    sorting.sort((a, b) => rank[a.type][b.type])
    clearCards()
    for (let card of sorting) {
      displayCard([card.text, card.type])
    }
    markDirty()
  }

  /**
   * Adds a new card and opens the detail editor.
   */
  function addCard() {
    displayCard(["Card Text", "STATEMENT"], true)
    editId = idCounter - 1
    isAddEdit = true
    openEditor()
    markDirty()
  }

  /**
   * Updates the card text of the currently edited card.
   */
  function updateCardText() {
    let str = applyCardTextFormat($("#card-text-input").val())
    let card = $(".card-editor-card-display").children("div")
    card.children("span").eq(0).html(str)
  }

  /**
   * Exports the current deck as a download.
   */
  function exportDeck() {
    let data = ""
    for (let card of cards.values()) {
      data += [card.text, card.type].join("\t") + "\n"
    }
    if (data !== "") {
      // Hack for UTF8 encoding
      let utf8data = unescape(encodeURIComponent(data))
      download(utf8data, "deck.tsv", "text/tab-separated-values")
    }
    markClean()
  }

  /**
   * Closes the editor.
   */
  function closeEditor() {
    $(".card-editor-container").addClass("invisible")
    let card = cards.get(editId)
    card.text = $("#card-text-input").val()
    card.node.children("span").eq(0).html(applyCardTextFormat(card.text))
    markDirty()

    // Reattach the card to the card editor view
    if (isAddEdit) {
      // Add edit: Insert at beginning
      $("#deck-display").prepend(card.node)
    } else {
      // First: Find a card before it. Second: Insert the card after it.
      let validId = editId - 1
      while (!cards.has(validId) && validId > 0) {
        validId--
      }
      if (validId === 0) {
        $("#deck-display").prepend(card.node)
      } else {
        $(`#card-id-${validId}`).after(card.node)
      }
    }

    // Reset detail editor
    editId = -1
    isAddEdit = false
  }

  /**
   * Marks the editor state as dirty.
   */
  function markDirty() {
    window.onbeforeunload = () => "Please make sure you save all unsaved data!"
  }

  /**
   * Marks the editor state as clean.
   */
  function markClean() {
    window.onbeforeunload = null;
  }

  $("#openDeckButton").click(openDeck)
  $("#addCardButton").click(addCard)
  $("#sortCardsButton").click(sortCards)
  $("#exportDeckButton").click(exportDeck)
  $("#closeEditorButton").click(closeEditor)
  $("#card-text-input").bind("input", updateCardText)
})()
