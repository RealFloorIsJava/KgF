<?php
    require "includes/toolbox.php";
    require_login_or_logout();
    initialize_user();
    check_admin();
    
    $subpage = "";
    if (isset($_GET['s'])) {
        $subpage = $_GET['s'];
    }
    
    $status = "";
    $success = true;
    
    if (isset($_GET['delete_card'])) {
        $id = $_GET['delete_card'];
        db_delete_card($id);
        $status = "Card #".$id." successfully deleted!";
        $success = true;
    } else if (isset($_GET['mode'], $_GET['card'])) {
        $mode = $_GET['mode'];
        $id = $_GET['card'];
        $success = true;
        if ($mode == "s") {
            db_modify_card_mode($id, "STATEMENT");
        $status = "Card #".$id." is now a black card.";
        } else if ($mode == "o") {
            db_modify_card_mode($id, "OBJECT");
        $status = "Card #".$id." is now a red card.";
        } else if ($mode == "v") {
            db_modify_card_mode($id, "VERB");
        $status = "Card #".$id." is now a yellow card.";
        } else {
            $success = false;
            $status = "Illegal mode";
        }
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
            if ($status != "") {
                if ($success) {
                    echo '<div class="status-box success-box">'.$status.'</div>';
                } else {
                    echo '<div class="status-box failure-box">'.$status.'</div>';
                }
            }
            
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
