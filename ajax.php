<?php
    if (!isset($_GET['action'])) {
        exit();
    }
    $action = $_GET['action'];
    
    require "includes/session_check.php";
    require "includes/user_state.php";
    
    if ($action == "rename" && isset($_POST['name'])) {
        $_SESSION['nickname'] = htmlspecialchars($_POST['name']);
        exit();
    }
?>
