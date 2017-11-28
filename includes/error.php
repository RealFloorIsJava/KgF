<?php
  if (!is_dir("./logs")) {
    mkdir("./logs");
    file_put_contents("./logs/.htaccess", "Deny from all");
    file_put_contents("./logs/err.log", "");
    chmod("./logs", 0777);
    chmod("./logs/.htaccess", 0666);
    chmod("./logs/err.log", 0666);
  }
  // This is necessary as open_basedir checking does not quite work in the error handler
  // (or the pwd is mangled)
  $error_fn = realpath("./logs/err.log");
  $error_tpl = realpath("./templates/err.html");

  function handle_errors($errno, $errstr, $errfile, $errline) {
    global $error_fn, $error_tpl;
    $c = file_get_contents($error_fn);
    $line = "Error #".$errno." - ".$errstr." in ".$errfile.":".$errline."\n";
    file_put_contents($error_fn, $c.$line);
    echo file_get_contents($error_tpl);
    exit();
  }

  function handle_exceptions($ex) {
    handle_errors(get_class($ex), $ex->getMessage(), $ex->getFile(),
      $ex->getLine());
  }

  function log_fatal_errors() {
    $err = error_get_last();
    if ($err["type"] == E_ERROR) {
      handle_errors($err["type"], $err["message"], $err["file"], $err["line"]);
    }
  }

  register_shutdown_function("log_fatal_errors");
  set_error_handler("handle_errors", E_ALL);
  set_exception_handler("handle_exceptions");

  ini_set("display_errors", "off");
  error_reporting(E_ALL);
?>
