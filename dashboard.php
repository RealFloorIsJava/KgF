<?php
    require "includes/session_check.php";
    require "includes/pdo.php";
    require "includes/user_state.php";
?>
<!DOCTYPE html>
<html>
    <head>
        <title>Karten gegen Flops</title>
        <link rel="stylesheet" type="text/css" href="/css/main.css">
        <link rel="stylesheet" type="text/css" href="/css/dark.css" id="theme">
    </head>
    <body>
        <div class="cupboard">
            <a href="?logout">Log Out</a> &mdash;
            You are known as <span id="username"><?= $_SESSION['nickname'] ?></span> (<a href="#" onclick="changeName()">Change</a>)
            <div style="float: right;"><a href="#" onclick="toggleLights()" id="lightLabel">Lights on</a></div><div style="clear: both;"></div>
        </div>
        
        <div class="card-container">
            <?php
                foreach ($db_handle->query("SELECT `card_text` FROM `kgf_cards` WHERE `card_type` = 'STATEMENT'") as $row) {
                    echo '<div class="statement-card card-base">'.$row["card_text"].'</div>';
                }
            ?>
        </div><br>
        
        <div class="card-container">
            <?php
                foreach ($db_handle->query("SELECT `card_text` FROM `kgf_cards` WHERE `card_type` = 'OBJECT'") as $row) {
                    echo '<div class="object-card card-base">'.$row["card_text"].'</div>';
                }
            ?>
        </div><br>
        
        <div class="card-container">
            <?php
                foreach ($db_handle->query("SELECT `card_text` FROM `kgf_cards` WHERE `card_type` = 'VERB'") as $row) {
                    echo '<div class="verb-card card-base">'.$row["card_text"].'</div>';
                }
            ?>
        </div>
        
        <script src="https://code.jquery.com/jquery-3.2.1.min.js" integrity="sha256-hwg4gsxgFZhOsEEamdOYGBf13FyQuiTwlAQgxVSNgt4=" crossorigin="anonymous"></script>
        <script type="text/javascript" src="/js/main.js"></script>
    </body>
</html>
