<!DOCTYPE html>
<html>
    <head>
        <title>Admin CP</title>
        <link rel="stylesheet" type="text/css" href="/css/main.css">
        <?= $this->user->get_theme_loader() ?>
    </head>
    <body>
        <div class="cupboard">
            <a href="?logout">Log Out</a>
            <div style="float: right;">
                <a href="/global.php?page=admin&sub=index">Admin CP tool selection</a> &mdash;
                <a href="/global.php?page=dashboard">Dashboard</a> &mdash;
                <a href="#" onclick="toggleLights()" id="lightLabel">Lights are being checked...</a>
            </div>
            <div style="clear: both;"></div>
        </div>
        <?= $this->get_status_format() ?>
        <div class="card-container">
            <?php
                $cards = Cards::get_all_cards();
                foreach ($cards as $card) {
                    echo Cards::format_card($card, true);
                }
            ?>
        </div>
        <script src="https://code.jquery.com/jquery-3.2.1.min.js" integrity="sha256-hwg4gsxgFZhOsEEamdOYGBf13FyQuiTwlAQgxVSNgt4=" crossorigin="anonymous"></script>
        <script type="text/javascript" src="/js/theme.js"></script>
    </body>
</html>
