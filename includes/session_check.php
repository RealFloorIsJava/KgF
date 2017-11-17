<?php
    session_start();
    if (isset($_GET["logout"])) {
        $_SESSION = array();
        session_unset();
        session_destroy();
    }
    if (!isset($_SESSION["login"])) {
        header("Location: /?auth_fail=1");
        exit();
    }
?>
