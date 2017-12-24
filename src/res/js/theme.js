$("#lightLabel").click(function() {
  theme = (theme == "dark") ? "light" : "dark";
  checkLights();
  document.getElementById("theme").href = '/css/min/' + theme + '.css';
  $.ajax({
    method: "POST",
    url: "/global.php?page=ajax&action=settheme",
    data: {
      selection: theme
    }
  });
});

function checkLights() {
  $("#lightLabel").html("Lights " + (theme == "light" ? "off" : "on"));
}

checkLights();
