<?php
    if (isset($_POST["pw"])) {
        $pw = $_POST["pw"];
        $correct_pw = trim(file_get_contents("config/site_password"));
        if ($pw == $correct_pw) {
            session_start();
            $_SESSION["login"] = true;
            header("Location: /dashboard.php");
        } else {
            header("Location: /?pw_fail=1");
        }
        exit();
    }
    header("Location: /");
?>
