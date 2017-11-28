<?php
    // Sessions contain two elements: login (set iff logged in)
    // and user (the user object)
    session_start();
    
    // Handle logout requests before session-failure kicks are handled
    if (isset($_GET["logout"])) {
        $_SESSION = array();
        session_unset();
        session_destroy();
    }
    
    // Require a valid login for the dispatcher (or redirect after a
    //  logout)
    if (!isset($_SESSION["login"])) {
        header("Location: /?auth_fail=1");
        exit();
    }
    
    // Check the user's existence and create a new user if necessary
    if (!isset($_SESSION["user"])) {
        $_SESSION["user"] = new User();
    }
?>
