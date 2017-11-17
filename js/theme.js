function toggleLights() {
    lightsOn = !lightsOn;
    if (lightsOn) {
        document.getElementById("lightLabel").innerHTML = 'Lights off';
        document.getElementById("theme").href = '/css/light.css';
    } else {
        document.getElementById("lightLabel").innerHTML = 'Lights on';
        document.getElementById("theme").href = '/css/dark.css';
    }
    $.ajax({
        method: "POST",
        url: "/ajax.php?action=theme",
        data: {
            selection: (lightsOn ? "light" : "dark")
        }
    })
}
