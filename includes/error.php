<?php
    if (!is_dir("logs")) {
        mkdir("logs");
        file_put_contents("logs/.htaccess", "Deny from all");
        file_put_contents("logs/err.log", "ERROR LOG\n");
    }
    
    function handle_errors($errno, $errstr, $errfile, $errline) {
        error_log("Error #".$errno." - ".$errstr." in ".$errfile.":".$errline."\n", 3, "logs/err.log");
        exit();
    }
    
    function handle_exceptions($ex) {
        handle_errors(get_class($ex), $ex->getMessage(), $ex->getFile(), $ex->getLine());
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
