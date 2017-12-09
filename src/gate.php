<?php
  if (isset($_POST["pw"])) {
    $pw = $_POST["pw"];
    $correctPw = trim(file_get_contents("config/site_password"));
    if ($pw === $correctPw) {
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
