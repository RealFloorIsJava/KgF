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
  let participantResolver = new Map()

  /**
   * Loads the match's participants.
   */
  function loadParticipants() {
    $.ajax({
      method: "GET",
      url: "/api/participants",
      dataType: "json",
      success: updateParticipants,
      error: (x, e, f) => console.log(`/api/participants error: ${e} ${f}`)
    })
  }

  /**
   * Updates the participant list of the match.
   *
   * @param data The JSON data which was retrieved from the API.
   */
  function updateParticipants(data) {
    let list = $("#partlist")
    let removeIds = new Set(participantResolver.keys())
    let addIds = new Set()
    for (let part of data) {
      removeIds.delete(part.id)
      if (!participantResolver.has(part.id)) {
        addIds.add(part.id)
        participantResolver.set(part.id, createParticipant())
      }
      let elem = participantResolver.get(part.id)
      elem.children(".part-name").text(part.name)
      elem.children(".part-score").text(`${part.score}pts`)
      elem.children(".part-type").text(part.picking ? "Picking" : "")
    }

    // Remove missing participants
    for (let id of removeIds.values()) {
      let elem = participantResolver.get(id)
      elem.remove()
      participantResolver.delete(id)
    }

    // Add new participants
    for (let id of addIds.values()) {
      list.append(participantResolver.get(id))
    }
    $("#defaultPart").remove()
  }

  /**
   * Creates a participant DIV.
   *
   * @return The created participant DIV.
   */
  function createParticipant() {
    return (
      $("<div></div>", {"class": "part"}).append([
        $("<div></div>", {"class": "part-name"}),
        $("<div></div>", {"class": "part-score"}),
        $("<div></div>", {"class": "part-type"}),
        $("<div></div>", {"class": "part-status"})
      ])
    )
  }

  setInterval(loadParticipants, 1500)
  loadParticipants()
})()
