<?php
  /**
   * Represents a participant of a match
   */
  class Participant {
    /**
     * Prepared SQL queries
     */
    private static $sSqlQueries;
    /**
     * The ID->Participant cache
     */
    private static $sIdCache;
    /**
     * The PlayerID->Participant cache
     */
    private static $sPlayerCache;
    /**
     * The ID of this participant
     */
    private $mId;
    /**
     * The ID of the player
     */
    private $mPlayerId;
    /**
     * The name of the player
     */
    private $mPlayerName;
    /**
     * The match this participant participates in
     */
    private $mMatch;
    /**
     * The score of this participant
     */
    private $mScore;
    /**
     * Whether this participant is currently picking
     */
    private $mPicking;
    /**
     * The point in time when this participant will be kicked due to timeout
     */
    private $mTimeout;

    /**
     * Used to provide a DB handle and to initialize all the queries
     */
    public static function provideDB($dbh) {
      self::$sSqlQueries = array(
        "housekeepingFind" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_match_participant` ".
          "WHERE `mp_timeout` <= UNIX_TIMESTAMP()"
        ),
        "housekeeping" => $dbh->prepare(
          "DELETE FROM `kgf_match_participant` ".
          "WHERE `mp_timeout` <= UNIX_TIMESTAMP()"
        ),
        "allForMatch" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_match_participant` ".
          "WHERE `mp_match` = :matchid ".
          "ORDER BY `mp_id` ASC"
        ),
        "getParticipant" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_match_participant` ".
          "WHERE `mp_player` = :playerid"
        ),
        "addParticipant" => $dbh->prepare(
          "INSERT INTO `kgf_match_participant` ".
            "(`mp_id`, `mp_player`, `mp_name`, `mp_match`, `mp_score`, ".
              "`mp_picking`, `mp_timeout`) ".
          "VALUES (NULL, :playerid, :playername, :matchid, 0, 0, :timeout)"
        ),
        "fetchLatest" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_match_participant` ".
          "ORDER BY `mp_id` DESC ".
          "LIMIT 1"
        ),
        "abandon" => $dbh->prepare(
          "DELETE FROM `kgf_match_participant` ".
          "WHERE `mp_id` = :partid"
        ),
        "heartbeat" => $dbh->prepare(
          "UPDATE `kgf_match_participant` ".
          "SET `mp_timeout` = :timeout ".
          "WHERE `mp_id` = :partid"
        ),
        "modifyPicking" => $dbh->prepare(
          "UPDATE `kgf_match_participant` ".
          "SET `mp_picking` = :picking ".
          "WHERE `mp_id` = :partid"
        )
      );
    }

    /**
     * Performs housekeeping tasks
     */
    public static function performHousekeeping() {
      $q = self::$sSqlQueries["housekeepingFind"];
      $q->execute();
      $rows = $q->fetchAll();
      foreach ($rows as $part) {
        Match::getById($part["mp_match"])->getChat()->sendMessage("SYSTEM",
          "<b>".$part["mp_name"]." timed out</b>");
      }

      $q = self::$sSqlQueries["housekeeping"];
      $q->execute();
    }

    /**
     * Loads the participants of the given match
     */
    public static function loadForMatch($match) {
      $q = self::$sSqlQueries["allForMatch"];
      $q->bindValue(":matchid", $match->getId(), PDO::PARAM_INT);
      $q->execute();
      $rows = $q->fetchAll();

      $parts = array();
      foreach ($rows as $part) {
        $id = $part["mp_id"];
        $pid = $part["mp_player"];
        if (!isset(self::$sIdCache[$id])) {
          $parts[] = new Participant($part["mp_id"],
            $part["mp_player"], $part["mp_name"], $match,
            intval($part["mp_score"]), intval($part["mp_picking"]) != 0,
            intval($part["mp_timeout"]));
        } else {
          $parts[] = self::$sIdCache[$id];
        }
      }
      return $parts;
    }

    /**
     * Fetches the participant for this player
     */
    public static function getParticipant($player) {
      if (isset(self::$sPlayerCache[$player])) {
        return self::$sPlayerCache[$player];
      }

      $q = self::$sSqlQueries["getParticipant"];
      $q->bindValue(":playerid", $player, PDO::PARAM_STR);
      $q->execute();
      $row = $q->fetch();
      if (!$row) {
        return null;
      }

      $part = new Participant($row["mp_id"], $player, $row["mp_name"],
        null, intval($row["mp_score"]),
        intval($row["mp_picking"]) != 0, intval($row["mp_timeout"]));
      $part->mMatch = Match::getById($row["mp_match"]);
      return $part;
    }

    /**
     * Creates a participant from an User and a Match
     */
    public static function createFromUserAndMatch($user, $match, $timeout) {
      $q = self::$sSqlQueries["addParticipant"];
      $q->bindValue(":playerid", $user->getId(), PDO::PARAM_STR);
      $q->bindValue(":playername", $user->getNickname(), PDO::PARAM_STR);
      $q->bindValue(":matchid", $match->getId(), PDO::PARAM_INT);
      $q->bindValue(":timeout", $timeout, PDO::PARAM_INT);
      $q->execute();

      // We're in a transaction, so this should be the one we just created
      $q = self::$sSqlQueries["fetchLatest"];
      $q->execute();

      $row = $q->fetch();
      $id = $row["mp_id"];
      $pid = $row["mp_player"];

      return new Participant($id, $pid, $row["mp_name"], $match,
        $row["mp_score"], intval($row["mp_picking"]) != 0, $row["mp_timeout"]);
    }

    /**
     * Private constructor to prevent instance creation
     */
    private function __construct($id, $playerId, $name, $match, $score,
      $picking, $timeout) {
      $this->mId = intval($id);
      $this->mPlayerId = $playerId;
      $this->mPlayerName = $name;
      $this->mMatch = $match;
      $this->mScore = intval($score);
      $this->mPicking = $picking;
      $this->mTimeout = $timeout;

      self::$sIdCache[$this->mId] = $this;
      self::$sPlayerCache[$this->mPlayerId] = $this;
    }

    /**
     * Leaves the match (and thus destroys this participant)
     */
    public function leaveMatch() {
      $this->mMatch->getChat()->sendMessage("SYSTEM",
        "<b>".$this->getName()." left</b>");

      $q = self::$sSqlQueries["abandon"];
      $q->bindValue(":partid", $this->mId, PDO::PARAM_INT);
      $q->execute();
      unset(self::$sIdCache[$this->mId]);
      unset(self::$sPlayerCache[$this->mPlayerId]);
    }

    /**
     * Registers a heartbeat (i.e. the timeout will be reset) for the given
     * amount of seconds
     */
    public function heartbeat($seconds) {
      $q = self::$sSqlQueries["heartbeat"];
      $q->bindValue(":timeout", time() + $seconds, PDO::PARAM_INT);
      $q->bindValue(":partid", $this->mId, PDO::PARAM_INT);
      $q->execute();
    }

    /**
     * ID getter
     */
    public function getId() {
      return $this->mId;
    }

    /**
     * Name getter
     */
    public function getName() {
      return $this->mPlayerName;
    }

    /**
     * Match getter
     */
    public function getMatch() {
      return $this->mMatch;
    }

    /**
     * Score getter
     */
    public function getScore() {
      return $this->mScore;
    }

    /**
     * Check whether the participant is picking cards
     */
    public function isPicking() {
      return $this->mPicking;
    }

    /**
     * Sets whether this participant is picking cards
     */
    public function setPicking($val) {
      $this->mPicking = $val;
      $q = self::$sSqlQueries["modifyPicking"];
      $q->bindValue(":picking", $this->mPicking ? 1 : 0, PDO::PARAM_INT);
      $q->bindValue(":partid", $this->mId, PDO::PARAM_INT);
      $q->execute();
    }
  }
?>
