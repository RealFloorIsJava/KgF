<?php
  require_once "config/db.php";
  $dsn = "mysql:host=".$dbHost.";dbname=".$dbName;
  try {
    $dbHandle = new PDO($dsn, $dbUser, $dbPw);
  } catch (PDOException $e) {
    die("Database connection failed!");
  }
  unset($dbUser, $dbPw, $dbHost, $dbName);

  $dbHandle->beginTransaction();

  function dbhAutocommit() {
    global $dbHandle;
    $dbHandle->commit();
  }
  register_shutdown_function('dbhAutocommit');
?>
