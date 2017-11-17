<?php
    /**
     * Models the card storage
     */
    class Cards {
        /**
         * The database handle
         */
        private static $db_handle;
        /**
         * Prepared SQL queries
         */
        private static $sql_queries;
        
        /**
         * Used to provide a DB handle and to initialize all the queries
         */
        public static function provideDB($dbh) {
            self::$db_handle = $dbh;
            self::$sql_queries = array(
                "all_cards" => $dbh->prepare("SELECT * FROM `kgf_cards`"),
                "delete_card" => $dbh->prepare("DELETE FROM `kgf_cards` WHERE `card_id` = :cardid"),
                "set_card_mode" => $dbh->prepare("UPDATE `kgf_cards` SET `card_type` = :cardtype WHERE `card_id` = :cardid")
            );
        }
        
        /**
         * Fetches all cards in the DB
         */
        public static function get_all_cards() {
            self::$sql_queries["all_cards"]->execute();
            return self::$sql_queries["all_cards"]->fetchAll();
        }
        
        /**
         * Deletes the card with the given ID
         */
        public static function delete_card($id) {            
            self::$sql_queries["delete_card"]->bindValue(":cardid", $id, PDO::PARAM_INT);
            self::$sql_queries["delete_card"]->execute();
        }
        
        /**
         * Changes the mode of the card with the given ID
         */
        public static function set_mode($id, $type) {
            self::$sql_queries["set_card_mode"]->bindValue(":cardid", $id, PDO::PARAM_INT);
            self::$sql_queries["set_card_mode"]->bindValue(":cardtype", $type, PDO::PARAM_STR);
            self::$sql_queries["set_card_mode"]->execute();
        }
        
        /**
         * Returns HTML for a card
         */
        public static function format_card($card, $include_options) {
            $res = '<div class="card-base ';
            if ($card["card_type"] == "STATEMENT") {
                $res .= "statement-card"; 
            } else if ($card["card_type"] == "OBJECT") {
                $res .= "object-card";
            } else if ($card["card_type"] == "VERB") {
                $res .= "verb-card";
            }
            $res .= '">';
            $res .= self::expand_underscores($card["card_text"]);
            $res .= '<div class="card-id">';
            if ($include_options) {
                $res .= self::admin_card_options($card["card_id"]);
            }
            $res .= '#'.$card["card_id"];
            $res .= '</div></div>';
            return $res;
        }
    
        /**
         * Editing options for admins
         */
        private static function admin_card_options($id) {
            $res = '<a href="/global.php?page=admin&sub=list&action=mode-s&card='.$id.'" class="knob-statement">&nbsp;&nbsp;&nbsp;&nbsp;</a> - ';
            $res .= '<a href="/global.php?page=admin&sub=list&action=mode-o&card='.$id.'" class="knob-object">&nbsp;&nbsp;&nbsp;&nbsp;</a> - ';
            $res .= '<a href="/global.php?page=admin&sub=list&action=mode-v&card='.$id.'" class="knob-verb">&nbsp;&nbsp;&nbsp;&nbsp;</a> - ';
            $res .= '<a href="/global.php?page=admin&sub=list&action=delete&card='.$id.'">Delete</a> - ';
            return $res;
        }
    
        /**
         * Expands underscores to 8 space wide blocks
         */
        private static function expand_underscores($text) {
            return preg_replace("/_/", "<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>", $text);
        }
    }
?>
