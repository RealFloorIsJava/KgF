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
     * The relative ordering key for this participant. This changes every round
     * to randomize card display
     */
    private $mOrder;
    /**
     * The hand of this participant
     */
    private $mHand;

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
              "`mp_picking`, `mp_timeout`, `mp_order`) ".
          "VALUES (NULL, :playerid, :playername, :matchid, 0, 0, :timeout, ".
            "NULL)"
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
        ),
        "modifyOrder" => $dbh->prepare(
          "UPDATE `kgf_match_participant` ".
          "SET `mp_order` = :newkey ".
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
          "<b>".$part["mp_name"]." timed out.</b>");
      }

      $q = self::$sSqlQueries["housekeeping"];
      $q->execute();
    }

    /**
     * Loads the participants of the given match
     */
    public static function loadForMatch(Match $match) {
      $q = self::$sSqlQueries["allForMatch"];
      $q->bindValue(":matchid", $match->getId(), PDO::PARAM_INT);
      $q->execute();
      $rows = $q->fetchAll();

      $parts = array();
      foreach ($rows as $part) {
        $id = $part["mp_id"];
        if (!isset(self::$sIdCache[$id])) {
          $parts[] = new Participant($part, array(
            "match" => $match
          ));
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
      $player = strval($player);
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

      $part = new Participant($row);
      return $part;
    }

    /**
     * Creates a participant from an User and a Match
     */
    public static function createFromUserAndMatch(User $user, Match $match,
        $timeout) {
      $timeout = intval($timeout);
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

      return new Participant($row, array(
        "match" => $match
      ));
    }

    /**
     * Private constructor to prevent instance creation
     */
    private function __construct(array $row, array $kwargs = array()) {
      $this->mId = intval($row["mp_id"]);
      $this->mPlayerId = $row["mp_player"];

      self::$sIdCache[$this->mId] = $this;
      self::$sPlayerCache[$this->mPlayerId] = $this;

      $this->mPlayerName = $row["mp_name"];
      $this->mScore = intval($row["mp_score"]);
      $this->mPicking = intval($row["mp_picking"]) !== 0;
      $this->mTimeout = intval($row["mp_timeout"]);
      $this->mOrder = is_null($row["mp_order"])
        ? null
        : intval($row["mp_order"]);

      if (isset($kwargs["match"])) {
        $this->mMatch = $kwargs["match"];
      } else {
        $this->mMatch = Match::getById($row["mp_match"]);
      }

      $this->mHand = Hand::loadHand($this);
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
      $seconds = intval($seconds);
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
     * Fetches the hand of this participant
     */
    public function getHand() {
      return $this->mHand;
    }

    /**
     * Participant order getter
     */
    public function getOrder() {
      return $this->mOrder;
    }

    /**
     * Assigns the given key as the order of this participant
     */
    public function assignOrder($key) {
      $key = intval($key);
      $this->mOrder = $key;
      $q = self::$sSqlQueries["modifyOrder"];
      $q->bindValue(":newkey", $this->mOrder, PDO::PARAM_INT);
      $q->bindValue(":partid", $this->mId, PDO::PARAM_INT);
      $q->execute();
    }

    /**
     * Sets whether this participant is picking cards
     */
    public function setPicking($val) {
      $val = boolval($val);
      $this->mPicking = $val;
      $q = self::$sSqlQueries["modifyPicking"];
      $q->bindValue(":picking", $this->mPicking ? 1 : 0, PDO::PARAM_INT);
      $q->bindValue(":partid", $this->mId, PDO::PARAM_INT);
      $q->execute();
    }
  }
?>
