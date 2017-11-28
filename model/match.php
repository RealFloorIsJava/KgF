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
     * The ID->Match cache
     */
    private static $id_cache = array();
    /**
     * The ID of this match
     */
    private $id;
    /**
     * The timestamp when this match state ends
     */
    private $timer;
    /**
     * The current black card
     */
    private $current_card;
    /**
     * The state of this match
     * One of PENDING CHOOSING PICKING COOLDOWN ENDING
     */
    private $state;
    /**
     * The participants of this match
     */
    private $participants;
    /**
     * The chat of this match
     */
    private $chat;

    /**
     * Used to provide a DB handle and to initialize all the queries
     */
    public static function provideDB($dbh) {
      self::$sql_queries = array(
        "housekeeping" => $dbh->prepare(
          "DELETE FROM `kgf_match` ".
          "WHERE ".
            "(SELECT COUNT(*) ".
              "FROM `kgf_match_participant` mp ".
              "WHERE mp.`mp_match` = `match_id`) < 1 ".
            "OR ((SELECT COUNT(*) ".
              "FROM `kgf_match_participant` mp ".
              "WHERE mp.`mp_match` = `match_id`) < 3 ".
            "AND `match_state` != 'PENDING')"
        ),
        "extend_empty_match_timer" => $dbh->prepare(
          "UPDATE `kgf_match` m ".
          "SET `match_timer` = :newtimer ".
          "WHERE `match_timer` <= :curtimer ".
            "AND (SELECT COUNT(*) ".
              "FROM `kgf_match_participant` ".
              "WHERE `mp_match` = m.`match_id`) < 4" // TODO make this code
        ),
        "extend_timer_on_join" => $dbh->prepare(
          "UPDATE `kgf_match` ".
          "SET `match_timer` = :newtimer ".
          "WHERE `match_timer` <= :curtimer ".
            "AND `match_id` = :match"
        ),
        "all_matches" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_match` ".
          "ORDER BY (`match_state` = 'PENDING') DESC, ".
            "`match_timer` ASC"
        ),
        "create_empty" => $dbh->prepare(
          "INSERT INTO `kgf_match` ".
            "(`match_id`, `match_timer`, `match_card_id`, `match_state`) ".
          "VALUES (NULL, :timer, :cardid, 'PENDING')"
        ),
        "fetch_by_id" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_match` ".
          "WHERE `match_id` = :matchid"
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
     * Performs housekeeping tasks
     */
    public static function perform_housekeeping() {
      $q = self::$sql_queries["housekeeping"];
      $q->execute();

      $q = self::$sql_queries["extend_empty_match_timer"];
      $q->bindValue(":newtimer", time() + 60, PDO::PARAM_INT);
      $q->bindValue(":curtimer", time() + 10, PDO::PARAM_INT);
      $q->execute();
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
        $id = $match["match_id"];
        if (!isset(self::$id_cache[$id])) {
          self::$id_cache[$id] = new Match($match["match_id"],
            $match["match_timer"], Card::get_card($match["match_card_id"]),
            $match["match_state"]);
        }
        $matches[] = self::$id_cache[$id];
      }
      return $matches;
    }

    /**
     * Fetches a match by its ID
     */
    public static function get_by_id($id) {
      if (isset(self::$id_cache[$id])) {
        return self::$id_cache[$id];
      }

      $q = self::$sql_queries["fetch_by_id"];
      $q->bindValue(":matchid", $id, PDO::PARAM_INT);
      $q->execute();
      $row = $q->fetch();
      self::$id_cache[$row["match_id"]] = new Match($row["match_id"],
        $row["match_timer"], Card::get_card($row["match_card_id"]),
        $row["match_state"]);
      return self::$id_cache[$row["match_id"]];
    }

    /**
     * Creates an empty match
     */
    public static function create_empty($starttime, $card) {
      $q = self::$sql_queries["create_empty"];
      $q->bindValue(":timer", $starttime, PDO::PARAM_INT);
      $q->bindValue(":cardid", $card->get_id(), PDO::PARAM_INT);
      $q->execute();

      // We're in a transaction, so this should be the one we just created
      $q = self::$sql_queries["fetch_latest"];
      $q->execute();
      $match = $q->fetch();

      self::$id_cache[$match["match_id"]] = new Match($match["match_id"],
        $match["match_timer"], $card, $match["match_state"]);
      self::$id_cache[$match["match_id"]]->get_chat()->send_message("SYSTEM",
        "<b>Match was created</b>");
      return self::$id_cache[$match["match_id"]];
    }

    /**
     * Private constructor to prevent instance creation
     */
    private function __construct($id, $timer, $card, $state) {
      $this->id = intval($id);
      $this->timer = intval($timer);
      $this->current_card = $card;
      $this->state = $state;
      $this->participants = Participant::load_for_match($this);
      $this->chat = new Chat($this);
    }

    /**
     * Returns whether this match has already started
     */
    public function has_started() {
      return $this->state != "PENDING";
    }

    /**
     * Adds this user to this match
     */
    public function add_user($user, $timeout) {
      $this->participants[] = Participant::create_from_user_and_match($user,
        $this, $timeout);
      $this->get_chat()->send_message("SYSTEM",
        "<b>".$user->get_nickname()." joined</b>");

      $q = self::$sql_queries["extend_timer_on_join"];
      $q->bindValue(":newtimer", time() + 30, PDO::PARAM_INT);
      $q->bindValue(":curtimer", time() + 30, PDO::PARAM_INT);
      $q->bindValue(":match", $this->id);
      $q->execute();
    }

    /**
     * Returns the number of seconds that remain until the next match phase
     * starts
     */
    public function get_seconds_to_next_phase() {
      return $this->timer - time();
    }

    /**
     * Returns the name of the owner of this match, i.e. the first participant
     */
    public function get_owner_name() {
      if (count($this->participants) < 1) {
        return "[unknown]";
      }
      return $this->participants[0]->get_name();
    }

    /**
     * Returns the number of participants
     */
    public function get_participant_count() {
      return count($this->participants);
    }

    /**
     * Participant getter
      */
    public function get_participants() {
      return $this->participants;
    }

    /**
     * ID getter
     */
    public function get_id() {
      return $this->id;
    }

    /**
     * Chat getter
     */
    public function get_chat() {
      return $this->chat;
    }

    /**
     * Fetches a line about the status of this match
     */
    public function get_status() {
      if ($this->state == "PENDING") {
        return "Waiting for players...";
      } else if ($this->state == "ENDING") {
        return "Match is ending...";
      }
      return "<State of Match unknown>";
    }
  }
?>
