<?php
  // Initialize error logging
  require_once "includes/error.php";

  // Initialize the session
  require_once "model/user.php";
  require_once "includes/session.php";

  // Connect to the DB and import the $dbHandle into the scope
  require_once "includes/pdo.php";

  // Initialize stuff
  require_once "model/card.php";
  require_once "model/chat.php";
  require_once "model/chatmessage.php";
  require_once "model/match.php";
  require_once "model/participant.php";

  // Provide the DB handle to all db-interacting classes
  Participant::provideDB($dbHandle);
  Match::provideDB($dbHandle);
  Chat::provideDB($dbHandle);
  Card::provideDB($dbHandle);

  // First clear old participants, then their matches
  Participant::performHousekeeping();
  Match::performHousekeeping();

  require_once "model/page.php";
  // Fetch the page source (include/class array)
  $source = Page::getPageSource(
    isset($_GET["page"]) ? $_GET["page"] : "dashboard");

  // Load, create and display the page
  require_once $source[0];
  $pageclass = $source[1];
  (new $pageclass($_SESSION["user"]))->display();
?>
