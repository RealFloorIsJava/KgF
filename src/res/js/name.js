"use strict";

(function(){
  /**
   * Changes the name of the user.
   */
  function changeName() {
    var newName = prompt("What name would you like to have?")
    if (newName === null) {
      return
    }
    if (newName === "" || newName.length >= 32) {
      alert("Invalid name! Please use between 1 and 31 characters.")
      return
    }
    $("#username").text(newName)
    $.ajax({
      method: "POST",
      url: "/options",
      data: {name: newName}
    })
  }

  $("#nameChangeLabel").click(changeName)
})()
