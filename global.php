<?php
    // Already needed here because the session contains user objects
    require "model/user.php";
    session_start();
    
    // Handle logout requests before session-failure kicks are handled
    if (isset($_GET["logout"])) {
        $_SESSION = array();
        session_unset();
        session_destroy();
    }
    
    // Require a valid login for the dispatcher
    if (!isset($_SESSION["login"])) {
        header("Location: /?auth_fail=1");
        exit();
    }
    
    // Connect to the DB and import the $db_handle into the scope
    require "includes/pdo.php";
    
    // Check the user's existence
    if (!isset($_SESSION["user"])) {
        $_SESSION["user"] = new User();
    }
    $user = $_SESSION["user"];
    
    // Fetch the page name
    $page = "dashboard";
    if (isset($_GET["page"])) {
        $page = $_GET["page"];
    }
    
    // For security reasons, only [a-z] are allowed
    if (!preg_match("/[a-z]+/", $page)) {
        $page = "dashboard";
    }
    
    // Construct the page file, 404-fallback
    $pagefile = "pages/page".$page.".php";
    if (!file_exists($pagefile)) {
        $pagefile = "pages/pagedashboard.php";
        $page = "dashboard";
    }
    
    // Load the page model and the page itself
    require "model/page.php";
    require $pagefile;
    
    // Load more stuff that might be needed for the page
    require "model/cards.php";
    require "model/match.php";
    
    // Initialize stuff
    Match::provideDB($db_handle);
    Participant::provideDB($db_handle);
    Card::provideDB($db_handle);
    
    Match::perform_housekeeping();
    
    // Display the page
    $pageclass = "Page".ucfirst($page);
    $page = new $pageclass($db_handle, $user);
    $page->display();
?>
