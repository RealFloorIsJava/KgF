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
  /**
   * Toggles the theme of the page and syncs the change.
   */
  function toggleLights() {
    theme = (theme == "dark") ? "light" : "dark"
    checkLights()
    $("#theme").attr("href", `/res/css/${theme}.css`)
    $.ajax({
      method: "POST",
      url: "/options",
      data: {"theme": theme}
    })
  }

  /**
   * Check the theme and update the light label accordingly.
   */
  function checkLights() {
    $("#lightLabel").html("Lights " + (theme == "light" ? "off" : "on"))
  }

  checkLights()
  $("#lightLabel").click(toggleLights)
})()
