<?php
    /**
     * Models the card storage
     */
    class Cards {
        /**
         * Prepared SQL queries
         */
        private static $sql_queries;
        
        /**
         * Used to provide a DB handle and to initialize all the queries
         */
        public static function provideDB($dbh) {
            self::$sql_queries = array(
                "all_cards" => $dbh->prepare("SELECT * FROM `kgf_cards`"),
                "get_card" => $dbh->prepare("SELECT * FROM `kgf_cards` WHERE `card_id` = :cardid")
            );
        }
        
        /**
         * Fetches all cards in the DB
         */
        public static function get_all_cards() {
            self::$sql_queries["all_cards"]->execute();
            $rows = self::$sql_queries["all_cards"]->fetchAll();
            $cards = array();
            foreach ($rows as $card) {
                $cards[$card["card_id"]] = new Card($card["card_id"], $card["card_text"], $card["card_type"]);
            }
            return $cards;
        }
        
        /**
         * Fetches one card from the DB
         */
        public static function get_card($id) {
            self::$sql_queries["get_card"]->bindValue(":cardid", $id, PDO::PARAM_INT);
            self::$sql_queries["get_card"]->execute();
            $rows = self::$sql_queries["get_card"]->fetchAll();
            foreach ($rows as $card) {
                return new Card($card["card_id"], $card["card_text"], $card["card_type"]);
            }
            return null;
        }
    }
    
    /**
     * Models one specific card
     */
    class Card {
        /**
         * Prepared SQL queries
         */
        private static $sql_queries;
        /**
         * The ID of this card
         */
        private $id;
        /**
         * The text on this card
         */
        private $text;
        /**
         * The type of this card
         */
        private $type;
        
        /**
         * Used to provide a DB handle and to initialize all the queries
         */
        public static function provideDB($dbh) {
            self::$sql_queries = array(
                "delete_card" => $dbh->prepare("DELETE FROM `kgf_cards` WHERE `card_id` = :cardid"),
                "set_card_mode" => $dbh->prepare("UPDATE `kgf_cards` SET `card_type` = :cardtype WHERE `card_id` = :cardid")
            );
        }
        
        public function __construct($id, $text, $type) {
            $this->id = $id;
            $this->text = $text;
            $this->type = $type;
        }
        
        /**
         * Deletes this card
         */
        public function delete_card() {            
            self::$sql_queries["delete_card"]->bindValue(":cardid", $this->id, PDO::PARAM_INT);
            self::$sql_queries["delete_card"]->execute();
        }
        
        /**
         * Changes the mode of this card
         */
        public function set_mode($type) {
            $this->type = $type;
            self::$sql_queries["set_card_mode"]->bindValue(":cardid", $this->id, PDO::PARAM_INT);
            self::$sql_queries["set_card_mode"]->bindValue(":cardtype", $this->type, PDO::PARAM_STR);
            self::$sql_queries["set_card_mode"]->execute();
        }
        
        /**
         * Returns the name of the CSS type class
         */
        public function get_type_class() {
            if ($this->type == "STATEMENT") {
                return "statement-card"; 
            } else if ($this->type == "OBJECT") {
                return "object-card";
            } else if ($this->type == "VERB") {
                return "verb-card";
            }
            return "unknown";
        }
        
        public function get_formatted_text() {
            return preg_replace("/_/", "<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>", $this->text);
        }
        
        public function get_id() {
            return $this->id;
        }
    }
?>
