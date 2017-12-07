$("#nameChangeLabel").click(function() {
  var newName = prompt("What name would you like to have?");
  if (newName != null && newName != "" && newName.length < 32) {
    $.ajax({
      method: "POST",
      url: "/global.php?page=ajax&action=rename",
      data: {
        name: newName
      }
    }).done(function(msg) {
      $("#username").text(newName);
    });
  } else {
    alert("Invalid name!");
  }
});
