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
  let minimumChatId = 0

  /**
   * Loads the match's chat.
   */
  function loadChat() {
    let logError = (x, e, f) => console.log(`/api/chat error: ${e} ${f}`)
    $.ajax({
      method: "POST",
      url: "/api/chat",
      data: {offset: minimumChatId},
      dataType: "json",
      success: updateChat,
      error: (x, e, f) => {logError(x, e, f); scheduleChatLoad()}
    })
  }

  /**
   * Updates the chat of the match.
   *
   * @param data The JSON data which was retrieved from the API.
   */
  function updateChat(data) {
    let list = $("#chatlist")
    let scrollPos = list.scrollTop() + list.innerHeight()
    let shouldScroll = scrollPos >= list[0].scrollHeight - 50
    for (let msg of data) {
      let node = createChatMessage(msg.type, msg.message)
      list.append(node)
      minimumChatId = msg.id + 1
    }
    if (shouldScroll && data.length > 0) {
      list.scrollTop(list[0].scrollHeight + list.innerHeight())
    }
    scheduleChatLoad()
  }

  /**
   * Creates a chat message DOM element.
   *
   * @param type The type of the chat message.
   * @param msg The message's text.
   */
  function createChatMessage(type, msg) {
    let typeImg = (type === "SYSTEM"
      ? "/res/images/bang.svg"
      : "/res/images/message.svg")
    return (
      $("<div></div>").append([
        $("<img>", {"src": typeImg, "class": "chat-svg"}),
        $("<span></span>", {"class": "chat-msg"}).html(msg)
      ])
    )
  }

  /**
   * Sends a chat message.
   */
  function sendMessage(ev) {
    let key = ev.which
    if (key !== 13) {
      return
    }

    let text = $("#chatinput").val()
    $("#chatinput").val("")
    if (text.trim().length > 0) {
      $.ajax({
        method: "POST",
        url: "/api/chat/send",
        data: {
          message: text
        }
      })
    }
  }

  /**
   * Schedules loading the chat.
   */
  function scheduleChatLoad() {
    setTimeout(loadChat, 500)
  }

  loadChat()
  $("#chatinput").keypress(sendMessage)
})()
