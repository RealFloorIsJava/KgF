<?php
  if (!file_exists("./includes/debug.log")) {
    file_put_contents("./includes/debug.log", "");
    chmod("./includes/debug.log", 0666);
  }

  function logDebug($str) {
    $file = realpath("./includes/debug.log");
    $bt = debug_backtrace();
    $line = $bt[0]["file"].":".$bt[0]["line"].": ".$str."\n";
    file_put_contents($file, file_get_contents($file).$line);
  }
?>
