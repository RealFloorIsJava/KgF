<!DOCTYPE html>
<html>
    <head>
        <title>Karten gegen Flopsigkeit</title>
        <link rel="stylesheet" type="text/css" href="/css/main.css">
        <?= $this->user->get_theme_loader() ?>
    </head>
    <body>
        <div class="cupboard">
            <a href="?logout">Log Out</a> &mdash;
            <a href="/global.php?page=match&action=abandon">Abandon match</a>
            <div style="float: right;">
                <a href="#" onclick="toggleLights()" id="lightLabel">Lights are being checked...</a>
            </div>
            <div style="clear: both;"></div>
        </div>
        <?= $this->get_status_format() ?>

        <script src="https://code.jquery.com/jquery-3.2.1.min.js" integrity="sha256-hwg4gsxgFZhOsEEamdOYGBf13FyQuiTwlAQgxVSNgt4=" crossorigin="anonymous"></script>
        <script type="text/javascript" src="/js/theme.js"></script>
    </body>
</html>
