<?php
    if ($_SESSION["admin"] !== true) {
        header("Location: /dashboard.php");
        exit();
    }
?>
