<?php
    require_once "config/db.php";
    $dsn = "mysql:host=".$db_host.";dbname=".$db_name;
    try {
        $db_handle = new PDO($dsn, $db_user, $db_pw);
    } catch (PDOException $e) {
        die("Database connection failed!");
    }
    unset($db_user, $db_pw, $db_host, $db_name);
?>
