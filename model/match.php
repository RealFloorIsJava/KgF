<?php
  /**
   * Represents a match
   */
  class Match {
    /**
     * The minimum amount of players for a match
     */
    const MINIMUM_PLAYERS = 4;
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
     * The current black card (may be null)
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
     * Whether this match has been deleted
     */
    private $mDeleted;

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
              "WHERE mp.`mp_match` = `match_id`) < 1 "
        ),
        "deleteMatch" => $dbh->prepare(
          "DELETE FROM `kgf_match` ".
          "WHERE `match_id` = :match"
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
          "VALUES (NULL, :timer, NULL, 'PENDING')"
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
        ),
        "modifyTimer" => $dbh->prepare(
          "UPDATE `kgf_match` ".
          "SET `match_timer` = :newtimer ".
          "WHERE `match_id` = :match"
        ),
        "modifyState" => $dbh->prepare(
          "UPDATE `kgf_match` ".
          "SET `match_state` = :newstate ".
          "WHERE `match_id` = :match"
        ),
        "modifyCard" => $dbh->prepare(
          "UPDATE `kgf_match` ".
          "SET `match_card_id` = :newcard ".
          "WHERE `match_id` = :match"
        )
      );
    }

    /**
     * Performs housekeeping tasks
     */
    public static function performHousekeeping() {
      $q = self::$sSqlQueries["housekeeping"];
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
          $matchObj = new Match($match["match_id"], $match["match_timer"],
            null, $match["match_state"]);
              $card = $match["match_card_id"];
          if (!is_null($card)) {
            $card = Card::getByIdForMatch($card, $matchObj);
            $matchObj->mCurrentCard = $card;
          }
          $matches[] = $matchObj;
        } else {
          $matches[] = self::$sIdCache[$id];
        }
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

      if (!$row) {
        return null;
      }

      $match = new Match($row["match_id"], $row["match_timer"], null,
        $row["match_state"]);

      $card = $row["match_card_id"];
      if (!is_null($card)) {
        $card = Card::getByIdForMatch($card, $match);
        $match->mCurrentCard = $card;
      }

      return $match;
    }

    /**
     * Creates an empty match
     */
    public static function createEmpty($startTime) {
      $q = self::$sSqlQueries["createEmpty"];
      $q->bindValue(":timer", $startTime, PDO::PARAM_INT);
      $q->execute();

      // We're in a transaction, so this should be the one we just created
      $q = self::$sSqlQueries["fetchLatest"];
      $q->execute();
      $match = $q->fetch();

      $obj = new Match($match["match_id"], $match["match_timer"], null,
        $match["match_state"]);
      $obj->getChat()->sendMessage("SYSTEM", "<b>Match was created</b>");
      return $obj;
    }

    /**
     * Private constructor to prevent instance creation
     */
    private function __construct($id, $timer, $card, $state) {
      self::$sIdCache[$this->mId] = $this;
      $this->mId = intval($id);
      $this->mTimer = intval($timer);
      $this->mCurrentCard = $card;
      $this->mState = $state;
      $this->mParticipants = Participant::loadForMatch($this);
      $this->mChat = new Chat($this);
      $this->mDeleted = false;

      $this->refreshTimerIfNecessary();
      $this->updateState();
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

      if ($this->mTimer - time() < 30) {
        $this->setTimer(time() + 30);
      }
    }

    /**
     * Reads the given deck file and creates a deck from it
     */
    public function createMatchDeck($file) {
      $tsvData = file_get_contents($file);
      $tsvData = preg_split("/\n|\r|\r\n/", $tsvData);

      $minimumCardLimit = array(
        "STATEMENT" => 10,
        "OBJECT" => 10,
        "VERB" => 10
      );

      // Limit to 2000 cards
      $amount = min(count($tsvData), 2000);
      for ($i = 0; $i < $amount; $i++) {
        $line = trim($tsvData[$i]);
        if (empty($line)) {
          continue;
        }

        $tsv = preg_split("/\t/", $line);
        if (count($tsv) != 2) {
          continue;
        }

        $text = substr(htmlspecialchars($tsv[0]), 0, 255);
        $type = $tsv[1];
        if (!Card::isValidType($type)) {
          continue;
        }

        $underscores = substr_count($text, "_");
        if ($underscores > 0) {
          if ($type !== "STATEMENT") {
            continue;
          }
          if ($underscores > 3) {
            continue;
          }
        }

        Card::createForMatch($text, $type, $this);
        $minimumCardLimit[$type]--;
      }

      foreach ($minimumCardLimit as $type => $value) {
        $orig = $value;
        while ($value-- > 0) {
          Card::createForMatch("Your deck needs at least ".$orig.
            " more ".strtolower($type)." cards", $type, $this);
        }
      }
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
     * Checks whether this match is deleted
     */
    public function isDeleted() {
      return $this->mDeleted;
    }

    /**
     * Checks whether the match is ending
     */
    public function isEnding() {
      return $this->mState === "ENDING";
    }

    /**
     * Checks whether the current match has a card
     */
    public function hasCard() {
      if ($this->mState == "ENDING") {
        return false;
      }
      return $this->mCurrentCard !== null;
    }

    /**
     * Fetches the current card of the match
     */
    public function getCard() {
      return $this->mCurrentCard;
    }

    /**
     * Fetches a line about the status of this match
     */
    public function getStatus() {
      if ($this->mState == "PENDING") {
        return "Waiting for players...";
      } else if ($this->mState == "CHOOSING") {
        return "Players are choosing cards...";
      } else if ($this->mState == "PICKING") {
        $picker = "<unknown>";
        for ($i = 0; $i < count($this->mParticipants); $i++) {
          if ($this->mParticipants[$i]->isPicking()) {
            $picker = $this->mParticipants[$i]->getName();
            break;
          }
        }
        return $picker." is picking a winner...";
      } else if ($this->mState == "COOLDOWN") {
        return "The next round is about to start...";
      } else if ($this->mState == "ENDING") {
        return "The match is ending...";
      }
      return "<State of Match unknown>";
    }

    /**
     *
     */
    private function setCurrentCard($card) {
      $this->mCurrentCard = $card;
      $q = self::$sSqlQueries["modifyCard"];
      $q->bindValue(":newcard", $card->getId(), PDO::PARAM_INT);
      $q->bindValue(":match", $this->mId, PDO::PARAM_INT);
      $q->execute();
    }

    /**
     * Changes the match timer to the given value
     */
    private function setTimer($timer) {
      $this->mTimer = $timer;
      $q = self::$sSqlQueries["modifyTimer"];
      $q->bindValue(":newtimer", $this->mTimer, PDO::PARAM_INT);
      $q->bindValue(":match", $this->mId, PDO::PARAM_INT);
      $q->execute();
    }

    /**
     * Changes the match state to the given value
     */
    private function setState($state) {
      $this->mState = $state;
      $q = self::$sSqlQueries["modifyState"];
      $q->bindValue(":newstate", $this->mState, PDO::PARAM_STR);
      $q->bindValue(":match", $this->mId, PDO::PARAM_INT);
      $q->execute();
    }

    /**
     * Deletes this match
     */
    private function delete() {
      $q = self::$sSqlQueries["deleteMatch"];
      $q->bindValue(":match", $this->mId, PDO::PARAM_INT);
      $q->execute();
      $this->mDeleted = true;
    }

    /**
     * Refreshes the match timer if it is necessary, e.g. when the match can't
     * be started due to lack of players
     */
    private function refreshTimerIfNecessary() {
      if ($this->mState === "PENDING") {
        if ($this->mTimer - time() < 10) {
          if (count($this->mParticipants) < self::MINIMUM_PLAYERS) {
            $this->setTimer(time() + 60);
          }
        }
      }
    }

    /**
     * Updates the state of this match if the needed conditions are met
     */
    private function updateState() {
      if ($this->mState === "PENDING") {
        if ($this->mTimer <= time()) {
          $this->selectPicker();
          $this->selectMatchCard();
          $this->setState("CHOOSING");
          $this->setTimer(time() + 60);
        }
      } else if ($this->mState === "ENDING") {
        if ($this->mTimer <= time()) {
          $this->delete();
        }
      }

      if ($this->mState !== "PENDING" && $this->mState !== "ENDING") {
        if (count($this->mParticipants) < self::MINIMUM_PLAYERS) {
          $this->setState("ENDING");
          $this->setTimer(time() + 30);
        }
      }
    }

    /**
     * Select the next person to pick cards
     */
    private function selectPicker() {
      $first = $this->mParticipants[0];
      $next = false;
      for ($i = 0; $i < count($this->mParticipants); $i++) {
        $part = $this->mParticipants[$i];
        if ($next) {
          $part->setPicking(true);
          break;
        } else if ($part->isPicking()) {
          $next = true;
          $part->setPicking(false);
        }
      }
      if (!$next) {
        $first->setPicking(true);
      }
    }

    /**
     * Selects a statement card for the match
     */
    private function selectMatchCard() {
      $card = Card::getRandomStatementForMatch($this);
      $this->setCurrentCard($card);
    }
  }
?>
