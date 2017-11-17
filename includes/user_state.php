<?php
    if (!isset($_SESSION['nickname'])) {
        $_SESSION['nickname'] = "Meme".rand(10000,99999);
    }
?>
