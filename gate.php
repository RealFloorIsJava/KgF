<?php
    if (isset($_POST["pw"])) {
        $pw = $_POST["pw"];
        $correct_pw = trim(file_get_contents("config/site_password"));
        if ($pw == $correct_pw) {
            // Set the login stub
            session_start();
            $_SESSION["login"] = true;
            
            // Redirect to the dispatcher where the further steps for login are taken
            header("Location: /global.php");
        } else {
            header("Location: /?pw_fail=1");
        }
        exit();
    }
    
    // Trying to access the gate.php without the form
    header("Location: /");
?>
