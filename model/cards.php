<?php
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
         * One of STATEMENT VERB OBJECT
         */
        private $type;
        
        /**
         * Used to provide a DB handle and to initialize all the queries
         */
        public static function provideDB($dbh) {
            self::$sql_queries = array(
                "all_cards" => $dbh->prepare(
                    "SELECT * ".
                    "FROM `kgf_cards`"
                ),
                "get_card" => $dbh->prepare(
                    "SELECT * ".
                    "FROM `kgf_cards` ".
                    "WHERE `card_id` = :cardid"
                ),
                "delete_card" => $dbh->prepare(
                    "DELETE FROM `kgf_cards` ".
                    "WHERE `card_id` = :cardid"
                ),
                "set_card_mode" => $dbh->prepare(
                    "UPDATE `kgf_cards` ".
                    "SET `card_type` = :cardtype ".
                    "WHERE `card_id` = :cardid"
                ),
                "random_card" => $dbh->prepare(
                    "SELECT * ".
                    "FROM `kgf_cards` ".
                    "WHERE `card_type` = :cardtype ".
                    "ORDER BY RAND() ".
                    "LIMIT 1"
                )
            );
        }
        
        /**
         * Fetches all cards in the DB
         */
        public static function get_all_cards() {
            $q = self::$sql_queries["all_cards"];
            $q->execute();
            $rows = $q->fetchAll();
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
            $q = self::$sql_queries["get_card"];
            $q->bindValue(":cardid", $id, PDO::PARAM_INT);
            $q->execute();
            $rows = $q->fetchAll();
            foreach ($rows as $card) {
                return new Card($card["card_id"], $card["card_text"], $card["card_type"]);
            }
            return null;
        }
        
        /**
         * Returns a random card of the given type
         */
        public static function random_card($type) {
            $q = self::$sql_queries["random_card"];
            $q->bindValue(":cardtype", $type, PDO::PARAM_STR);
            $q->execute();
            $rows = $q->fetchAll();
            foreach ($rows as $row) {
                return new Card($row["card_id"], $row["card_text"], $row["card_type"]);
            }
            return null;
        }
        
        private function __construct($id, $text, $type) {
            $this->id = intval($id);
            $this->text = $text;
            $this->type = $type;
        }
        
        /**
         * Deletes this card
         */
        public function delete_card() {
            $q = self::$sql_queries["delete_card"];
            $q->bindValue(":cardid", $this->id, PDO::PARAM_INT);
            $q->execute();
        }
        
        /**
         * Changes the mode of this card
         */
        public function set_mode($type) {
            $this->type = $type;
            $q = self::$sql_queries["set_card_mode"];
            $q->bindValue(":cardid", $this->id, PDO::PARAM_INT);
            $q->bindValue(":cardtype", $this->type, PDO::PARAM_STR);
            $q->execute();
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
        
        /**
         * Returns the HTML-formatted text of the card
         */
        public function get_formatted_text() {
            return preg_replace("/_/", "<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>", $this->text);
        }
        
        public function get_id() {
            return $this->id;
        }
    }
?>
