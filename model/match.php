<?php
    /**
     * Represents a match
     */
    class Match {
        /**
         * Prepared SQL queries
         */
        private static $sql_queries;
        /**
         * The ID of this match
         */
        private $id;
        /**
         * The timestamp when this match will begin
         */
        private $start_time;
        /**
         * The current black card
         */
        private $current_card;
        /**
         * The participants of this match
         */
        private $participants;
        
        /**
         * Used to provide a DB handle and to initialize all the queries
         */
        public static function provideDB($dbh) {
            self::$sql_queries = array(
                "all_matches" => $dbh->prepare(
                    "SELECT `match_id`, `match_start`, `match_card_id` ".
                    "FROM `kgf_match` ".
                    "ORDER BY (`match_start` < UNIX_TIMESTAMP()) ASC, ".
                        "`match_start` ASC"
                )
            );
        }
        
        /**
         * Fetches all matches in the DB
         */
        public static function get_all_matches() {
            $q = self::$sql_queries["all_matches"];
            $q->execute();
            $rows = $q->fetchAll();
            $matches = array();
            foreach ($rows as $match) {
                $matches[] = new Match($match["match_id"], $match["match_start"], Card::get_card($match["match_card_id"]));
            }
            return $matches;
        }
        
        public function __construct($id, $start, $card) {
            $this->id = intval($id);
            $this->start_time = intval($start);
            $this->current_card = $card;
            $this->participants = Participant::load_for_match($this);
        }
        
        /**
         * Returns whether this match has already started
         */
        public function has_started() {
            return $this->start_time <= time();
        }
        
        public function get_seconds_to_start() {
            return $this->start_time - time();
        }
        
        public function get_owner_name() {
            return $this->participants[0]->get_name();
        }
        
        public function get_participant_count() {
            return count($this->participants);
        }
        
        public function get_id() {
            return $this->id;
        }
    }
    
    /**
     * Represents a participant of a match
     */
    class Participant {
        /**
         * Prepared SQL queries
         */
        private static $sql_queries;
        /**
         * The ID of this participant
         */
        private $id;
        /**
         * The ID of the player
         */
        private $player_id;
        /**
         * The name of the player
         */
        private $player_name;
        /**
         * The match this participant participates in
         */
        private $match;
        /**
         * The score of this participant
         */
        private $score;
        /**
         * Whether this participant is currently picking
         */
        private $picking;
        
        /**
         * Used to provide a DB handle and to initialize all the queries
         */
        public static function provideDB($dbh) {
            self::$sql_queries = array(
                "all_for_match" => $dbh->prepare(
                    "SELECT * ".
                    "FROM `kgf_match_participant` ".
                    "WHERE `mp_match` = :matchid ".
                    "ORDER BY `mp_id` ASC"
                )
            );
        }
        
        /**
         * Loads the participants of the given match
         */
        public static function load_for_match($match) {
            $q = self::$sql_queries["all_for_match"];
            $q->bindValue(":matchid", $match->get_id(), PDO::PARAM_INT);
            $q->execute();
            $rows = $q->fetchAll();
            $parts = array();
            foreach ($rows as $part) {
                $parts[] = new Participant($part["mp_id"], $part["mp_player"], $part["mp_name"], $match, $part["mp_score"], intval($part["mp_picking"]) != 0);
            }
            return $parts;
        }
        
        public function __construct($id, $player_id, $name, $match, $score, $picking) {
            $this->id = intval($id);
            $this->player_id = $player_id;
            $this->player_name = $name;
            $this->match = $match;
            $this->score = intval($score);
            $this->picking = $picking;
        }
        
        public function get_name() {
            return $this->player_name;
        }
    }
?>
