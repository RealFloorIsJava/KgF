<?php
  if (!file_exists("./includes/err.log")) {
    file_put_contents("./includes/err.log", "");
    chmod("./includes/err.log", 0666);
  }
  // This is necessary as open_basedir checking does not quite work in
  // the error handler (or the pwd is mangled)
  $errorFn = realpath("./includes/err.log");
  $errorTpl = realpath("./templates/err.html");

  function handleErrors($errno, $errstr, $errfile, $errline) {
    global $errorFn, $errorTpl;
    $c = file_get_contents($errorFn);
    $line = "Error #".$errno." - ".$errstr." in ".$errfile.":".
      $errline."\n";
    file_put_contents($errorFn, $c.$line);
    echo file_get_contents($errorTpl);

    // Kill the script to prevent errors from getting worse
    exit();
  }

  function handleExceptions($ex) {
    handleErrors(get_class($ex), $ex->getMessage(), $ex->getFile(),
      $ex->getLine());
  }

  function logFatalErrors() {
    $err = error_get_last();
    if ($err["type"] == E_ERROR) {
      handleErrors($err["type"], $err["message"], $err["file"],
        $err["line"]);
    }
  }

  register_shutdown_function("logFatalErrors");
  set_error_handler("handleErrors", E_ALL);
  set_exception_handler("handleExceptions");

  ini_set("display_errors", "off");
  error_reporting(E_ALL);
?>
