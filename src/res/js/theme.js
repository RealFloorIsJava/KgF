"use strict";

(function(){
  /**
   * Toggles the theme of the page and syncs the change.
   */
  function toggleLights() {
    theme = (theme == "dark") ? "light" : "dark"
    checkLights()
    $("#theme").attr("href", "/res/css-${theme}-css")
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
