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
                ),
                "create_empty" => $dbh->prepare(
                    "INSERT INTO `kgf_match` ".
                    "(`match_id`, `match_start`, `match_card_id`) ".
                    "VALUES (NULL, :starttime, :cardid)"
                ),
                "fetch_latest" => $dbh->prepare(
                    "SELECT * ".
                    "FROM `kgf_match` ".
                    "ORDER BY `match_id` DESC ".
                    "LIMIT 1"
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
        
        /**
         * Creates an empty match
         */
        public static function create_empty($starttime, $card) {
            $q = self::$sql_queries["create_empty"];
            $q->bindValue(":starttime", $starttime, PDO::PARAM_INT);
            $q->bindValue(":cardid", $card->get_id(), PDO::PARAM_INT);
            $q->execute();
            
            // We're in a transaction, so this should be the one we just created
            $q = self::$sql_queries["fetch_latest"];
            $q->execute();
            $rows = $q->fetchAll();
            foreach ($rows as $row) {
                return new Match($row["match_id"], $row["match_start"], $card);
            }
            return null;
        }
        
        private function __construct($id, $start, $card) {
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
        
        /**
         * Adds the given participant to the cached list of participants
         */
        public function add_participant($participant) {
            $this->participants[] = $participant;
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
                ),
                "is_in_match" => $dbh->prepare(
                    "SELECT COUNT(*) AS `count` ".
                    "FROM `kgf_match_participant` ".
                    "WHERE `mp_player` = :playerid"
                ),
                "add_participant" => $dbh->prepare(
                    "INSERT INTO `kgf_match_participant` ".
                    "(`mp_id`, `mp_player`, `mp_name`, `mp_match`, `mp_score`, `mp_picking`) ".
                    "VALUES (NULL, :playerid, :playername, :matchid, 0, 0)"
                ),
                "fetch_latest" => $dbh->prepare(
                    "SELECT * ".
                    "FROM `kgf_match_participant` ".
                    "ORDER BY `mp_id` DESC ".
                    "LIMIT 1"
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
        
        /**
         * Checks whether the given player is in a match
         */
        public static function is_in_match($player) {
            $q = self::$sql_queries["is_in_match"];
            $q->bindValue(":playerid", $player, PDO::PARAM_STR);
            $q->execute();
            $rows = $q->fetchAll();
            foreach ($rows as $row) {
                return intval($row["count"]) != 0;
            }
            die("Count of matches could not be retrieved");
        }
        
        /**
         * Adds the user as a participant to the given match
         */
        public static function add_user_to_match($user, $match) {
            $q = self::$sql_queries["add_participant"];
            $q->bindValue(":playerid", $user->get_id(), PDO::PARAM_STR);
            $q->bindValue(":playername", $user->get_nickname(), PDO::PARAM_STR);
            $q->bindValue(":matchid", $match->get_id(), PDO::PARAM_INT);
            $q->execute();
            
            // We're in a transaction, so this should be the one we just created
            $q = self::$sql_queries["fetch_latest"];
            $q->execute();
            $rows = $q->fetchAll();
            $part = null;
            foreach ($rows as $row) {
                $part = new Participant($row["mp_id"], $row["mp_player"], $row["mp_name"], $match, $row["mp_score"], intval($row["mp_picking"]) != 0);
                break;
            }
            
            $match->add_participant($part);
        }
        
        private function __construct($id, $player_id, $name, $match, $score, $picking) {
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
