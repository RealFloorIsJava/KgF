<?php
    require "includes/toolbox.php";
    require_login_or_logout();
    initialize_user();
?>
<!DOCTYPE html>
<html>
    <head>
        <title>Karten gegen Flopsigkeit</title>
        <link rel="stylesheet" type="text/css" href="/css/main.css">
        <link rel="stylesheet" type="text/css" href="/css/dark.css" id="theme">
    </head>
    <body>
        <div class="cupboard">
            <a href="?logout">Log Out</a> &mdash;
            You are known as <span id="username"><?= $_SESSION['nickname'] ?></span> (<a href="#" onclick="changeName()">Change</a>)
            <div style="float: right;">
                <?php
                    if ($_SESSION['admin'] === true) {
                        echo '<a href="#" onclick="enterACP(true)">Admin CP</a>';
                    } else {
                        echo '<a href="#" onclick="enterACP(false)">Admin CP</a>';
                    }
                ?> &mdash;
                <a href="#" onclick="toggleLights()" id="lightLabel">Lights on</a>
            </div>
            <div style="clear: both;"></div>
        </div>
        
        Game selection will be here and stuff.

        <script src="https://code.jquery.com/jquery-3.2.1.min.js" integrity="sha256-hwg4gsxgFZhOsEEamdOYGBf13FyQuiTwlAQgxVSNgt4=" crossorigin="anonymous"></script>
        <script type="text/javascript" src="/js/main.js"></script>
        <script type="text/javascript" src="/js/theme.js"></script>
    </body>
</html>
