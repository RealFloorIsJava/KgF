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
    </head>
    <body>
        <div class="cupboard">
            <a href="?logout">Log Out</a> &mdash; You are known as <?= $_SESSION['nickname'] ?>
        </div>
        
        <div class="card-container">
            <?php
                foreach ($db_handle->query("SELECT `card_text` FROM `kgf_cards` WHERE `card_type` = 'STATEMENT'") as $row) {
                    echo '<div class="statement-card">'.$row["card_text"].'</div>';
                }
            ?>
        </div><br>
        
        <div class="card-container">
            <?php
                foreach ($db_handle->query("SELECT `card_text` FROM `kgf_cards` WHERE `card_type` = 'OBJECT'") as $row) {
                    echo '<div class="object-card">'.$row["card_text"].'</div>';
                }
            ?>
        </div><br>
        
        <div class="card-container">
            <?php
                foreach ($db_handle->query("SELECT `card_text` FROM `kgf_cards` WHERE `card_type` = 'VERB'") as $row) {
                    echo '<div class="verb-card">'.$row["card_text"].'</div>';
                }
            ?>
        </div>
    </body>
</html>
