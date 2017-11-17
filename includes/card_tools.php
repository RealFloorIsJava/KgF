<?php
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
