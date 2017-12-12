<?php
  require_once "lib/minify.php";
  use MatthiasMullie\Minify;

  function minifyAssets() {
    minifyAll("./css", "./css/min");
    minifyAll("./js", "./js/min");
  }

  function minifyAll($path, $out) {
    $notMinified = array();
    $it = new DirectoryIterator($path);
    foreach ($it as $info) {
      if (!$info->isDot() && !$info->isDir()) {
        $notMinified[] = array(
          "orig" => $path."/".$info->getFilename(),
          "min" => $out."/".$info->getFilename(),
          "ext" => $info->getExtension()
        );
      }
    }

    if (!is_dir($out)) {
      mkdir($out);
      chmod($out, 0777);
    }

    foreach ($notMinified as $tuple) {
      $minifyThis = false;
      if (!file_exists($tuple["min"])) {
        $minifyThis = true;
      } else {
        $originalMTime = filemtime($tuple["orig"]);
        $outMTime = filemtime($tuple["min"]);
        if ($originalMTime > $outMTime) {
          // To prevent modification while the file is still uploading, check
          // with the current time
          if ($originalMTime < time() - 2) {
            $minifyThis = true;
          }
        }
      }
      if ($minifyThis) {
        minifyAsset($tuple["orig"], $tuple["min"], $tuple["ext"]);
      }
    }
  }

  function minifyAsset($from, $to, $type) {
    if ($type == "js") {
      $minifier = new Minify\JS($from);
    } else if ($type == "css") {
      $minifier = new Minify\CSS($from);
    } else {
      throw new Exception("Invalid minify type: ".$type);
    }
    $minifier->minify($to);
  }

  minifyAssets();
?>
