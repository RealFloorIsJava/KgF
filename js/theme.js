function toggleLights() {
    theme = (theme == "dark") ? "light" : "dark";
    checkLights();
    document.getElementById("theme").href = '/css/' + theme + '.css';
    $.ajax({
        method: "POST",
        url: "/global.php?page=ajax&action=settheme",
        data: {
            selection: theme
        }
    })
}

function checkLights() {
    if (theme == "light") {
        document.getElementById("lightLabel").innerHTML = 'Lights off';
    } else {
        document.getElementById("lightLabel").innerHTML = 'Lights on';
    }
}

checkLights();
