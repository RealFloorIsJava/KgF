/**
 * Part of KgF.
 *
 * MIT License
 * Copyright (c) 2017-2018 LordKorea
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
  let matchResolver = new Map()

  /**
   * Loads all matches and displays them on the page.
   */
  function loadMatches() {
    $.ajax({
      method: "GET",
      url: "/api/list",
      dataType: "json",
      success: displayMatches,
      error: (x, e, f) => console.log(`/api/list error: ${e} ${f}`)
    })
  }

  /**
   * Displays the matches that were received from the API.
   *
   * @param json The JSON data object that was received.
   */
  function displayMatches(json) {
    let matchList = $("#matchlist")
    let addIds = new Set()
    let removeIds = new Set(matchResolver.keys())

    // Modify DOM elements
    for (let match of json) {
      removeIds.delete(match.id)
      if (!matchResolver.has(match.id)) {
        addIds.add(match.id)
        matchResolver.set(match.id, createMatchDiv(match.id))
      }
      let elem = matchResolver.get(match.id)
      let [divStarting, divRunning] = jqUnpack(elem.children("div"))

      // The DIV for when the match can be joined
      let [bOwner, bParts, bSeconds] = jqUnpack(divStarting.find("b"))
      bOwner.html(match.owner)
      bParts.html(match.participants)
      bSeconds.html(match.seconds)
      divStarting.toggleClass("invisible", match.started)

      // The DIV for when the match can't be joined
      let [bOwner2, bParts2] = jqUnpack(divRunning.find("b"))
      bOwner2.html(match.owner)
      bParts2.html(match.participants)
      divRunning.toggleClass("invisible", !match.started)
    }

    // Delete all gone matches
    for (let id of removeIds) {
      let dom = matchResolver.get(id)
      dom.remove()
      matchResolver.delete(id)
    }

    // Add all new matches
    for (let id of addIds) {
      matchList.append(matchResolver.get(id))
    }
  }

  /**
   * Creates a DIV for the given ID
   *
   * @param id The id of the match.
   * @return The DOM element.
   */
  function createMatchDiv(id) {
    $("#matchlist").on("click", `#id-joinmatch-${id}`, {}, () => joinMatch(id))
    return (
      $("<div></div>", {"class": "match-box"}).append([
        $("<div></div>", {"class": "match-box-contents"}).append([
          $("<div></div>").append([
            $("<b></b>"),
            "'s match &mdash; ",
            $("<b></b>"),
            " participants &mdash; Starting in ",
            $("<b></b>"),
            " seconds..."
          ]),
          $("<div></div>").append([
            $("<button>Join match</button>").attr("id", `id-joinmatch-${id}`)
          ])
        ]),
        $("<div></div>", {"class": "match-box-contents"}).append([
          $("<div></div>").append([
            $("<b></b>"),
            "'s match &mdash; ",
            $("<b></b>"),
            " participants"
          ]),
          $("<div></div>").append([
            $("<button>Can't join now</button>").prop("disabled", true)
          ])
        ])
      ])
    )
  }

  /**
   * Opens the deck editor.
   */
  function openEditor() {
    window.location.assign("/deckedit")
  }

  /**
   * Joins a match.
   *
   * @param id The ID of the match that will be joined.
   */
  function joinMatch(id) {
    window.location.assign("/match/join/" + id)
  }

  $("#deckEditButton").click(openEditor)
  setInterval(loadMatches, 1000)
  loadMatches()
})()
