<?php
    require "includes/toolbox.php";
    require_login_or_logout();
    initialize_user();
    check_admin();
    require "includes/pdo.php";
    
    $subpage = "";
    if (isset($_GET['s'])) {
        $subpage = $_GET['s'];
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
                foreach ($db_handle->query("SELECT * FROM `kgf_cards`") as $row) {
                    echo format_card($row, true);
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
