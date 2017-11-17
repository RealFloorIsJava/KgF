var lightsOn = false;

function toggleLights() {
    lightsOn = !lightsOn;
    if (lightsOn) {
        document.getElementById("lightLabel").innerHTML = 'Lights off';
        document.getElementById("theme").href = '/css/light.css';
    } else {
        document.getElementById("lightLabel").innerHTML = 'Lights on';
        document.getElementById("theme").href = '/css/dark.css';
    }
}
