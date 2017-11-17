<?php
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
    
    function format_card($card, $with_opts=false) {
        $res = '<div class="card-base ';
        if ($card["card_type"] == "STATEMENT") { $res .= "statement-card"; }
        if ($card["card_type"] == "OBJECT") { $res .= "object-card"; }
        if ($card["card_type"] == "VERB") { $res .= "verb-card"; }
        $res .= '">';
        $res .= $card["card_text"];
        $res .= '<div class="card-id">';
        if ($with_opts) {
            $res .= '<a href="/admin.php?delete_card='.$card["card_id"].'">Delete</a> - ';
        }
        $res .= '#';
        $res .= $card["card_id"];
        $res .= '</div></div>';
        return $res;
    }
?>
