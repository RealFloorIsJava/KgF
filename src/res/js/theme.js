$("#lightLabel").click(function() {
  theme = (theme == "dark") ? "light" : "dark";
  checkLights();
  document.getElementById("theme").href = '/res/css-' + theme + '-css';
  $.ajax({
    method: "POST",
    url: "/options",
    data: {
      "theme": theme
    }
  });
});

function checkLights() {
  $("#lightLabel").html("Lights " + (theme == "light" ? "off" : "on"));
}

checkLights();
