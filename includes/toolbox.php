<?php
    require "includes/pdo.php";

    ///// ACCOUNT STUFF /////
    
    session_start();

    function require_login_or_logout() {
        if (isset($_GET["logout"])) {
            $_SESSION = array();
            session_unset();
            session_destroy();
        }
        if (!isset($_SESSION["login"])) {
            header("Location: /?auth_fail=1");
            exit();
        }
    }
    
    function check_admin() {
        if (!isset($_SESSION["admin"]) || $_SESSION["admin"] !== true) {
            header("Location: /dashboard.php");
            exit();
        }
    }
    
    function initialize_user() {
        $req = array(
            "id" => uniqid(),
            "admin" => false,
            "nickname" => "Meme".rand(10000,99999)
        );
        
        foreach ($req as $key => $value) {
            if (!isset($_SESSION[$key])) {
                $_SESSION[$key] = $value;
            }
        }
    }
    
    ///// HELPER STUFF /////
    
    function expand_underscores($text) {
        return preg_replace("/_/", "<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>", $text);
    }
    
    function format_card($card, $with_opts=false) {
        $res = '<div class="card-base ';
        if ($card["card_type"] == "STATEMENT") { $res .= "statement-card"; }
        if ($card["card_type"] == "OBJECT") { $res .= "object-card"; }
        if ($card["card_type"] == "VERB") { $res .= "verb-card"; }
        $res .= '">';
        $res .= expand_underscores($card["card_text"]);
        $res .= '<div class="card-id">';
        if ($with_opts) {
            $res .= '<a href="/admin.php?s=list&delete_card='.$card["card_id"].'">Delete</a> - ';
        }
        $res .= '#';
        $res .= $card["card_id"];
        $res .= '</div></div>';
        return $res;
    }
    
    ///// DB STUFF /////
    
    $sql_queries = array(
        "all_cards" => $db_handle->prepare("SELECT * FROM `kgf_cards`"),
        "delete_card" => $db_handle->prepare("DELETE FROM `kgf_cards` WHERE `card_id` = :cardid")
    );
    
    function db_all_cards() {
        global $sql_queries;
        $sql_queries["all_cards"]->execute();
        return $sql_queries["all_cards"]->fetchAll();
    }
    
    function db_delete_card($id) {
        global $sql_queries;
        $sql_queries["delete_card"]->bindValue(":cardid", $id, PDO::PARAM_INT);
        $sql_queries["delete_card"]->execute();
    }
?>
