<?php
    require "includes/toolbox.php";
    require_login_or_logout();
    initialize_user();
    check_admin();
    
    $subpage = "";
    if (isset($_GET['s'])) {
        $subpage = $_GET['s'];
    }
    
    if (isset($_GET['delete_card'])) {
        $id = $_GET['delete_card'];
        db_delete_card($id);
    }
?>
<!DOCTYPE html>
<html>
    <head>
        <title>Admin CP</title>
        <link rel="stylesheet" type="text/css" href="/css/main.css">
        <link rel="stylesheet" type="text/css" href="/css/dark.css" id="theme">
    </head>
    <body>
        <div class="cupboard">
            <a href="?logout">Log Out</a>
            <div style="float: right;">
                <a href="/admin.php">Admin CP tool selection</a> &mdash;
                <a href="/dashboard.php">Dashboard</a> &mdash;
                <a href="#" onclick="toggleLights()" id="lightLabel">Lights on</a>
            </div>
            <div style="clear: both;"></div>
        </div>
        <?php
            if ($subpage == "list") {
        ?>
        <div class="card-container">
            <?php
                $cards = db_all_cards();
                foreach ($cards as $card) {
                    echo format_card($card, true);
                }
            ?>
        </div>
        <?php
            } else {
        ?>
        <div class="default-container">
            <a href="?s=list">List cards</a><br>
        </div>
        <?php
            }
        ?>
        <script src="https://code.jquery.com/jquery-3.2.1.min.js" integrity="sha256-hwg4gsxgFZhOsEEamdOYGBf13FyQuiTwlAQgxVSNgt4=" crossorigin="anonymous"></script>
        <script type="text/javascript" src="/js/theme.js"></script>
    </body>
</html>
