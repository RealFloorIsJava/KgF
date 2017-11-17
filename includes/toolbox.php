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
    
    function admin_card_options($id) {
        $res = '<a href="/admin.php?s=list&mode=s&card='.$id.'" class="knob-statement">&nbsp;&nbsp;&nbsp;&nbsp;</a> - ';
        $res .= '<a href="/admin.php?s=list&mode=o&card='.$id.'" class="knob-object">&nbsp;&nbsp;&nbsp;&nbsp;</a> - ';
        $res .= '<a href="/admin.php?s=list&mode=v&card='.$id.'" class="knob-verb">&nbsp;&nbsp;&nbsp;&nbsp;</a> - ';
        $res .= '<a href="/admin.php?s=list&delete_card='.$id.'">Delete</a> - ';
        return $res;
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
            $res .= admin_card_options($card["card_id"]);
        }
        $res .= '#'.$card["card_id"];
        $res .= '</div></div>';
        return $res;
    }
    
    ///// DB STUFF /////
    
    $sql_queries = array(
        "all_cards" => $db_handle->prepare("SELECT * FROM `kgf_cards`"),
        "delete_card" => $db_handle->prepare("DELETE FROM `kgf_cards` WHERE `card_id` = :cardid"),
        "set_card_mode" => $db_handle->prepare("UPDATE `kgf_cards` SET `card_type` = :cardtype WHERE `card_id` = :cardid")
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
    
    function db_modify_card_mode($id, $type) {
        global $sql_queries;
        $sql_queries["set_card_mode"]->bindValue(":cardid", $id, PDO::PARAM_INT);
        $sql_queries["set_card_mode"]->bindValue(":cardtype", $type, PDO::PARAM_STR);
        $sql_queries["set_card_mode"]->execute();
    }
?>
