<?php
  if (!is_dir("./uploads")) {
    mkdir("./uploads");
    chmod("./uploads", 0777);
    file_put_contents("./uploads/.htaccess", "Deny from all");
  }
?>
