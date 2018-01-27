/**
 * Part of KgF.
 *
 * MIT License
 * Copyright (c) 2017-2018 LordKorea
 * Copyright (c) 2018 Arc676/Alessandro Vinciguerra
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
  let countDown = 0
  let ending = false
  let numGaps = 0
  let allowChoose = false
  let allowPick = false
  let isSpectator = false
  let isPicker = false
  let externalUpdateAllowed = true
  let handResolver = new Map([
    ["OBJECT", new Map()],
    ["VERB", new Map()]
  ])
  let numSelected = 0
  let selectedCards = new Map()

  /**
   * Loads the match's status.
   */
  function loadStatus() {
    $.ajax({
      method: "GET",
      url: "/api/status",
      dataType: "json",
      success: updateStatus,
      error: (x, e, f) => console.log(`/api/status error: ${e} ${f}`)
    })
  }

  /**
   * Updates the status of the match.
   *
   * @param data The JSON data which was retrieved from the API.
   */
  function updateStatus(data) {
    countDown = data.timer
    $("#matchstatus").html(data.status)
    ending = data.ending
    numGaps = data.gaps
    allowChoose = data.allowChoose
    allowPick = data.allowPick
    isSpectator = data.isSpectator

    $("#cardcount").html("Selected: " + numSelected + " of " + numGaps);
    $("#cardcount").toggleClass("invisible", !allowChoose)

    if (isSpectator) {
      $(".match-hand").addClass("invisible")
    }
    isPicker = data.isPicker

    updateMatchStatement(data.hasCard, data.cardText || "Waiting...")

    updateCountdown()
    if (ending && countDown < 3) {
      window.location.assign("/dashboard")
    }
  }

  /**
   * Updates the countdown timer.
   */
  function updateCountdown() {
    let minutes = (Math.max(0, Math.floor(countDown / 60)) + "")
    minutes = minutes.padStart(2, "0")
    let seconds = (Math.max(0, countDown) % 60 + "").padStart(2, "0")
    $("#countdown").text(`${minutes}:${seconds}`)
  }

  /**
   * Updates the match's statement card.
   *
   * @param hasCard Whether the match has a statement card.
   * @param text The text of the statement card.
   */
  function updateMatchStatement(hasCard, text) {
    let elem = $("#match-statement")
    elem.html(applyCardTextFormat(text))
    if (hasCard) {
      elem.addClass("statement-card").removeClass("system-card")
    } else {
      elem.addClass("system-card").removeClass("statement-card")
    }
  }

  /**
   * Loads the match's cards (hand and played).
   */
  function loadCards() {
    $.ajax({
      method: "GET",
      url: "/api/cards",
      dataType: "json",
      success: updateCards,
      error: (x, e, f) => console.log(`/api/cards error: ${e} ${f}`)
    })
  }

  /**
   * Updates the cards (hand and played) of the match.
   *
   * @param data The JSON data which was retrieved from the API.
   */
  function updateCards(data) {
    let sentHand = new Map([
      ["OBJECT", new Map()],
      ["VERB", new Map()]
    ])
    if (data.hasOwnProperty("hand")) {
      for (let type of sentHand.keys()) {
        for (let key in data.hand[type]) {
          sentHand.get(type).set(key, data.hand[type][key])
        }
        updateHand(sentHand.get(type), type)
      }
    }
    updatePlayed(data.played)
  }

  /**
   * Updates the played card area.
   *
   * @param data The played cards data.
   */
  function updatePlayed(data) {
    let area = $(".match-played-cards")
    let sets = area.children(".match-played-set")
    if (sets.length === 0) {
      area.prepend(createCardSet(1))
      sets = area.children(".match-played-set")
    }
    let key = 0
    for (let dataSet of data) {
      while (key > sets.length) {
        sets.last().after(createCardSet(key))
        sets = area.children(".match-played-set")
      }

      let set = sets.eq(key - 1)
      set.empty()
      set.css("display", "none")
      for (let card of dataSet) {
        let elem = createPlayedCard(card)
        set.append(elem)
        set.css("display", "flex")
      }

      key++
    }
  }

  /**
   * Creates a played card element.
   *
   * @param card The card data for the card that should be created.
   */
  function createPlayedCard(card) {
    if (card.hasOwnProperty("redacted")) {
      return (
        $("<div></div>", {"class": "card-base system-card"}).prepend(
          $("<div></div>", {"class": "card-label"}).text("?")
        )
      )
    } else {
      return (
        $("<div></div>", {
          "class": `card-base ${card.type.toLowerCase()}-card`
        }).html(applyCardTextFormat(card.text))
      )
    }
  }

  /**
   * Creates a card set for the participant with the given ID.
   *
   * @param key The ID of the participant.
   * @return The element for the set.
   */
  function createCardSet(key) {
    $(document).on("click", `#played-id-${key}`, {}, () => clickPlayed(key))
    return (
      $("<div></div>", {
        "class": "match-played-set",
        "id": `played-id-${key}`
      }).css("display", "none")
    )
  }

  /**
   * Handles clicking on a card set.
   *
   * @param key The order key of the card set.
   */
  function clickPlayed(key) {
    if (!allowPick) {
      return
    }
    $.ajax({
      method: "POST",
      url: "/api/pick",
      data: {"playedId": key}
    })
  }

  /**
   * Updates the hand of the client.
   *
   * @param hand The hand that was sent by the server.
   * @param type The card type of the hand.
   */
  function updateHand(hand, type) {
    let lowerType = type.toLowerCase()
    let container = $(`#${lowerType}-hand`)
    let resolver = handResolver.get(type)

    // Unselect hand cards that have been unselected on the server side.
    // This is not possible one second after a newly chosen card is marked.
    if (externalUpdateAllowed) {
      for (let [id, data] of hand.entries()) {
        if (data.chosen === null && resolver.has(id)) {
          unselectHandCard(resolver.get(id))
        }
      }
    }

    // Add new cards
    for (let id of hand.keys().filter(x => !resolver.has(x))) {
      let elem = createHandCard(lowerType, id, hand.get(id).text)
      if (hand.get(id).chosen !== null) {
        selectHandCard(elem, hand.get(id).chosen)
      }
      container.append(elem)
      resolver.set(id, elem)
    }

    // Delete old cards (uses array because of concurrent modification)
    for (let id of Array.from(resolver.keys().filter(x => !hand.has(x)))) {
      unselectHandCard(resolver.get(id))
      resolver.get(id).remove()
      resolver.delete(id)
    }

    if (resolver.size > 0) {
      container.children(".system-card").remove()
    } else {
      container.empty().append(createSystemCard())
    }

    $(".hand-set").find(".card-base").toggleClass("grey-card", isPicker)
  }

  /**
   * Marks a card with a selection watermark.
   *
   * @param card The card that should be watermarked.
   * @param k The number that should be put on the card.
   */
  function selectHandCard(card, k) {
    if (card.children(".card-label").length === 0) {
      card.prepend($("<div></div>").addClass("card-label").text("" + (k + 1)))
    } else {
      card.children(".card-label").text("" + (k + 1))
    }
    card.addClass("card-selected")
    selectedCards.set(k, card)
    numSelected++;
  }

  /**
   * Removes the watermark from the given card.
   *
   * @param card The card that should have its watermark removed.
   */
  function unselectHandCard(card) {
    card.children(".card-label").remove()
    card.removeClass("card-selected")
    for (let [id, entry] of selectedCards.entries()) {
      if (entry === card) {
        selectedCards.delete(id)
        numSelected--
        break
      }
    }
  }

  /**
   * Creates a system card.
   *
   * @return The system card element.
   */
  function createSystemCard() {
    return (
      $("<div></div>", {
        "class": "card-base system-card"
      }).text("No cards on your hand.")
    )
  }

  /**
   * Creates a hand card element.
   *
   * @param type The card type.
   * @param id The ID of the hand card.
   * @param text The text of the hand card.
   * @return The hand card element.
   */
  function createHandCard(type, id, text) {
    $(document).on("click", `#hand-id-${id}`, {}, () => toggleSelect(id))
    return (
      $("<div></div>", {
        "class": `card-base ${type}-card`,
        "id": `hand-id-${id}`
      }).html(applyCardTextFormat(text))
    )
  }

  /**
   * Toggles selection of the hand card with the given ID.
   *
   * @param id The ID of the hand card.
   */
  function toggleSelect(id) {
    if (!allowChoose) {
      return
    }
    $.ajax({
      method: "POST",
      url: "/api/choose",
      data: {"handId": id},
      success: () => updateSelection(id),
      error: (x, e, f) => console.log(`/api/choose error: ${e} ${f}`)
    })
  }

  /**
   * Updates the hand selection.
   *
   * @param id The ID of the card.
   */
  function updateSelection(id) {
    externalUpdateAllowed = false
    setTimeout(() => externalUpdateAllowed = true, 1000)

    let remove = false
    let card = handResolver.get("OBJECT").get(id)
    card = card || handResolver.get("VERB").get(id)

    // Remove card choices
    for (let i = 0; i < 4; i++) {
      if (!selectedCards.has(i)) {
        continue
      }
      if (selectedCards.get(i) === card || remove) {
        unselectHandCard(selectedCards.get(i))
        remove = true
      }
    }

    // Add a new card
    if (!remove) {
      if (numSelected < numGaps) {
        selectHandCard(card, numSelected)
      }
    }
  }

  /**
   * Picks and shows the hand tab with the given ID.
   *
   * @param tab The ID of the tab.
   */
  function pickTab(tab) {
    $(".hand-tab-header").removeClass("active-tab-header")
    $(".hand-set").css("display", "none")
    $(`.${tab}`).css("display", "inherit")
    $(`#${tab}`).addClass("active-tab-header")
  }

  /**
   * Chooses the actions tab.
   */
  function chooseActionsTab() {
    pickTab("tab-actions")
  }

  /**
   * Chooses the objects tab.
   */
  function chooseObjectsTab() {
    pickTab("tab-objects")
  }

  /**
   * Sends POST request to skip the remaining time
   */
  function skipTime() {
    $.ajax({
      method: "POST",
      url: "/api/skip"
    })
  }

  /**
   * Toggle hand visibility
   */
   function toggleHand() {
     $("#hand-container").hide()
   }

  setInterval(loadStatus, 1000)
  loadStatus()
  setInterval(loadCards, 1000)
  loadCards()
  pickTab("tab-actions")
  $("#tab-actions").click(chooseActionsTab)
  $("#tab-objects").click(chooseObjectsTab)
  $("#skip-button").click(skipTime)
  $("#toggle-hand-button").click(toggleHand)
})()
