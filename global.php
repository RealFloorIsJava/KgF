<?php
  // Initialize error logging
  require "includes/error.php";

  // Load all models already here because deserializing the session
  // could require class definitions to be present.
  require "model/user.php";
  require "model/cards.php";
  require "model/match.php";
  require "model/page.php";

  // Initialize the session
  require "includes/session.php";

  // Connect to the DB and import the $db_handle into the scope
  require "includes/pdo.php";

  // Initialize stuff
  Match::provideDB($db_handle);
  Participant::provideDB($db_handle);
  ChatMessage::provideDB($db_handle);
  Card::provideDB($db_handle);

  // Perform housekeeping
  Participant::perform_housekeeping();
  Match::perform_housekeeping();

  // Fetch the page source (include/class array)
  $source = Page::get_page_source(
  isset($_GET["page"]) ? $_GET["page"] : "dashboard");

  // Load, create and display the page
  require $source[0];
  $pageclass = $source[1];
  (new $pageclass($_SESSION["user"]))->display();
?>
