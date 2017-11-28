<?php
  // Initialize error logging
  require_once "includes/error.php";

  // Initialize the session
  require_once "model/user.php";
  require_once "includes/session.php";

  // Connect to the DB and import the $db_handle into the scope
  require_once "includes/pdo.php";

  // Initialize stuff
  require_once "model/participant.php";
  require_once "model/match.php";
  require_once "model/chat.php";
  require_once "model/card.php";

  // Provide the DB handle to all db-interacting classes
  Participant::provideDB($db_handle);
  Match::provideDB($db_handle);
  Chat::provideDB($db_handle);
  Card::provideDB($db_handle);

  // First clear old participants, then their matches
  Participant::perform_housekeeping();
  Match::perform_housekeeping();

  require_once "model/page.php";
  // Fetch the page source (include/class array)
  $source = Page::get_page_source(
  isset($_GET["page"]) ? $_GET["page"] : "dashboard");

  // Load, create and display the page
  require_once $source[0];
  $pageclass = $source[1];
  (new $pageclass($_SESSION["user"]))->display();
?>
