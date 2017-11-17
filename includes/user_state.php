<?php
    if (!isset($_SESSION['id'])) {
        $_SESSION['id'] = uniqid();
    }
    
    if (!isset($_SESSION['admin'])) {
        $_SESSION['admin'] = false;
    }
    
    if (!isset($_SESSION['nickname'])) {
        $_SESSION['nickname'] = "Meme".rand(10000,99999);
    }
?>
