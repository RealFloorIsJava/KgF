<?php
    require "includes/toolbox.php";
    require_login_or_logout();
    initialize_user();
    
    if (!isset($_GET['action'])) {
        exit();
    }
    $action = $_GET['action'];
    
    require "includes/session_check.php";
    require "includes/user_state.php";
    
    if ($action == "rename" && isset($_POST['name'])) {
        $name = htmlspecialchars($_POST['name']);
        if ($name != "" && strlen($name) < 64) {
            $_SESSION['nickname'] = htmlspecialchars($_POST['name']);
        }
    } else if ($action == "theme" && isset($_POST['selection'])) {
        $_SESSION['theme'] = $_POST['selection'];
    } else if ($action == "escalate" && isset($_POST['token'])) {
        $token = sha1($_POST['token']);
        $correct_token = trim(file_get_contents("config/mgr_password"));
        if ($token == $correct_token) {
            $_SESSION['admin'] = true;
        }
    }
?>
