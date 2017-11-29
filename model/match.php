<?php
  require_once "model/participant.php";
  require_once "model/card.php";
  require_once "model/chat.php";

  /**
   * Represents a match
   */
  class Match {
    /**
     * Prepared SQL queries
     */
    private static $sSqlQueries;
    /**
     * The ID->Match cache
     */
    private static $sIdCache = array();
    /**
     * The ID of this match
     */
    private $mId;
    /**
     * The timestamp when this match state ends
     */
    private $mTimer;
    /**
     * The current black card
     */
    private $mCurrentCard;
    /**
     * The state of this match
     * One of PENDING CHOOSING PICKING COOLDOWN ENDING
     */
    private $mState;
    /**
     * The participants of this match
     */
    private $mParticipants;
    /**
     * The chat of this match
     */
    private $mChat;

    /**
     * Used to provide a DB handle and to initialize all the queries
     */
    public static function provideDB($dbh) {
      self::$sSqlQueries = array(
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
        "extendEmptyMatchTimer" => $dbh->prepare(
          "UPDATE `kgf_match` m ".
          "SET `match_timer` = :newtimer ".
          "WHERE `match_timer` <= :curtimer ".
            "AND (SELECT COUNT(*) ".
              "FROM `kgf_match_participant` ".
              "WHERE `mp_match` = m.`match_id`) < 4" // TODO make this code
        ),
        "extendTimerOnJoin" => $dbh->prepare(
          "UPDATE `kgf_match` ".
          "SET `match_timer` = :newtimer ".
          "WHERE `match_timer` <= :curtimer ".
            "AND `match_id` = :match"
        ),
        "allMatches" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_match` ".
          "ORDER BY (`match_state` = 'PENDING') DESC, ".
            "`match_timer` ASC"
        ),
        "createEmpty" => $dbh->prepare(
          "INSERT INTO `kgf_match` ".
            "(`match_id`, `match_timer`, `match_card_id`, `match_state`) ".
          "VALUES (NULL, :timer, :cardid, 'PENDING')"
        ),
        "fetchById" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_match` ".
          "WHERE `match_id` = :matchid"
        ),
        "fetchLatest" => $dbh->prepare(
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
    public static function performHousekeeping() {
      $q = self::$sSqlQueries["housekeeping"];
      $q->execute();

      $q = self::$sSqlQueries["extendEmptyMatchTimer"];
      $q->bindValue(":newtimer", time() + 60, PDO::PARAM_INT);
      $q->bindValue(":curtimer", time() + 10, PDO::PARAM_INT);
      $q->execute();
    }

    /**
     * Fetches all matches in the DB
     */
    public static function getAllMatches() {
      $q = self::$sSqlQueries["allMatches"];
      $q->execute();
      $rows = $q->fetchAll();

      $matches = array();
      foreach ($rows as $match) {
        $id = $match["match_id"];
        if (!isset(self::$sIdCache[$id])) {
          self::$sIdCache[$id] = new Match($match["match_id"],
            $match["match_timer"], Card::getCard($match["match_card_id"]),
            $match["match_state"]);
        }
        $matches[] = self::$sIdCache[$id];
      }
      return $matches;
    }

    /**
     * Fetches a match by its ID
     */
    public static function getById($id) {
      if (isset(self::$sIdCache[$id])) {
        return self::$sIdCache[$id];
      }

      $q = self::$sSqlQueries["fetchById"];
      $q->bindValue(":matchid", $id, PDO::PARAM_INT);
      $q->execute();
      $row = $q->fetch();
      self::$sIdCache[$row["match_id"]] = new Match($row["match_id"],
        $row["match_timer"], Card::getCard($row["match_card_id"]),
        $row["match_state"]);
      return self::$sIdCache[$row["match_id"]];
    }

    /**
     * Creates an empty match
     */
    public static function createEmpty($startTime, $card) {
      $q = self::$sSqlQueries["createEmpty"];
      $q->bindValue(":timer", $startTime, PDO::PARAM_INT);
      $q->bindValue(":cardid", $card->getId(), PDO::PARAM_INT);
      $q->execute();

      // We're in a transaction, so this should be the one we just created
      $q = self::$sSqlQueries["fetchLatest"];
      $q->execute();
      $match = $q->fetch();

      self::$sIdCache[$match["match_id"]] = new Match($match["match_id"],
        $match["match_timer"], $card, $match["match_state"]);
      self::$sIdCache[$match["match_id"]]->getChat()->sendMessage("SYSTEM",
        "<b>Match was created</b>");
      return self::$sIdCache[$match["match_id"]];
    }

    /**
     * Private constructor to prevent instance creation
     */
    private function __construct($id, $timer, $card, $state) {
      $this->mId = intval($id);
      $this->mTimer = intval($timer);
      $this->mCurrentCard = $card;
      $this->mState = $state;

      $this->mParticipants = Participant::loadForMatch($this);
      $this->mChat = new Chat($this);
    }

    /**
     * Returns whether this match has already started
     */
    public function hasStarted() {
      return $this->mState != "PENDING";
    }

    /**
     * Adds this user to this match
     */
    public function addUser($user, $timeout) {
      $this->mParticipants[] = Participant::createFromUserAndMatch($user, $this,
        $timeout);
      $this->getChat()->sendMessage("SYSTEM",
        "<b>".$user->getNickname()." joined</b>");

      $q = self::$sSqlQueries["extendTimerOnJoin"];
      $q->bindValue(":newtimer", time() + 30, PDO::PARAM_INT);
      $q->bindValue(":curtimer", time() + 30, PDO::PARAM_INT);
      $q->bindValue(":match", $this->mId);
      $q->execute();
    }

    /**
     * Returns the number of seconds that remain until the next match phase
     * starts
     */
    public function getSecondsToNextPhase() {
      return $this->mTimer - time();
    }

    /**
     * Returns the name of the owner of this match, i.e. the first participant
     */
    public function getOwnerName() {
      if (count($this->mParticipants) < 1) {
        return "[unknown]";
      }
      return $this->mParticipants[0]->getName();
    }

    /**
     * Returns the number of participants
     */
    public function getParticipantCount() {
      return count($this->mParticipants);
    }

    /**
     * Participant getter
      */
    public function getParticipants() {
      return $this->mParticipants;
    }

    /**
     * ID getter
     */
    public function getId() {
      return $this->mId;
    }

    /**
     * Chat getter
     */
    public function getChat() {
      return $this->mChat;
    }

    /**
     * Fetches a line about the status of this match
     */
    public function getStatus() {
      if ($this->mState == "PENDING") {
        return "Waiting for players...";
      } else if ($this->mState == "ENDING") {
        return "Match is ending...";
      }
      return "<State of Match unknown>";
    }
  }
?>
