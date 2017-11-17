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

function changeName() {
    var newName = prompt("What name would you like to have?");
    $.ajax({
        method: "POST",
        url: "/ajax.php?action=rename",
        data: {
            name: newName
        }
    }).done(function( msg ) {
        document.getElementById("username").innerHTML = newName;
    });
}
