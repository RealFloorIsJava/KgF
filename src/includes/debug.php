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

  function takeRandomRequestSample() {
    global $benchStart;
    if (rand(0, 5000) == 0) {
      logDebug("Random request metrics:");
      logDebug("       Date: ".date("Y-m-d H:i:s"));
      logDebug("        URI: ".$_SERVER["REQUEST_URI"]);
      logDebug("       Time: ".(microtime(true) - $benchStart));
      logDebug("        Mem: ".strval(floor(memory_get_usage() / 1024))."K");
      logDebug("    PeakMem: ".strval(floor(memory_get_peak_usage() / 1024)).
        "K");
      logDebug("      Limit: ".ini_get("memory_limit"));
    }
  }
?>
