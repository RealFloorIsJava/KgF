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
     * Minimum amount of cards of each type.
     * Don't set this lower than 6 for each type.
     */
    const MINIMUM_STATEMENT_CARDS = 10;
    const MINIMUM_OBJECT_CARDS = 10;
    const MINIMUM_VERB_CARDS = 10;
    /**
     * Timer constants, all values in seconds
     */
    const INITIAL_MATCH_TIMER = 60;
    const USERADD_REPLENISH_AMOUNT = 30;
    const STATE_CHOOSING_TIME = 60;
    const STATE_PICKING_TIME = 60;
    const STATE_COOLDOWN_TIME = 15;
    const STATE_ENDING_TIME = 20;
    /**
     * Timer thresholds, all values in seconds
     */
    const USERADD_REPLENISH_THRESHOLD = 30;
    const PENDING_REFRESH_THRESHOLD = 10;
    const CHOOSING_FINAL_THRESHOLD = 10;
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
          $matches[] = new Match($match);
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
      $id = intval($id);
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

      return new Match($row);
    }

    /**
     * Creates an empty match
     */
    public static function createEmpty() {
      $q = self::$sSqlQueries["createEmpty"];
      $q->bindValue(":timer", time() + self::INITIAL_MATCH_TIMER,
        PDO::PARAM_INT);
      $q->execute();

      // We're in a transaction, so this should be the one we just created
      $q = self::$sSqlQueries["fetchLatest"];
      $q->execute();
      $match = $q->fetch();

      $obj = new Match($match);
      $obj->getChat()->sendMessage("SYSTEM", "<b>Match was created.</b>");
      return $obj;
    }

    /**
     * Private constructor to prevent instance creation
     */
    private function __construct(array $row) {
      $this->mId = intval($row["match_id"]);

      self::$sIdCache[$this->mId] = $this;

      $this->mTimer = intval($row["match_timer"]);
      $this->mState = $row["match_state"];
      $this->mDeleted = false;

      $this->mParticipants = Participant::loadForMatch($this);
      $this->mChat = new Chat($this);

      $this->mCurrentCard = null;
      if (!is_null($row["match_card_id"])) {
        $this->mCurrentCard = Card::getByIdForMatch($row["match_card_id"],
          $this);
      }
    }

    /**
     * Returns whether this match has already started
     */
    public function hasStarted() {
      return $this->mState !== "PENDING";
    }

    /**
     * Adds this user to this match
     */
    public function addUser(User $user, $timeout) {
      $timeout = intval($timeout);
      $this->mParticipants[] = Participant::createFromUserAndMatch($user, $this,
        $timeout);
      $this->getChat()->sendMessage("SYSTEM",
        "<b>".$user->getNickname()." joined.</b>");

      if ($this->mTimer - time() < self::USERADD_REPLENISH_THRESHOLD) {
        $this->setTimer(time() + self::USERADD_REPLENISH_AMOUNT);
      }
    }

    /**
     * Removes a participant by ID, but only from the cached match.
     */
    public function removeParticipant($id) {
      $id = strval($id);
      $i = 0;
      for (; $i < count($this->mParticipants); $i++) {
        if ($this->mParticipants[$i]->getId() === $id) {
          break;
        }
      }
      if ($i < count($this->mParticipants)) {
        array_splice($this->mParticipants, $i, 1);
      }
      if (count($this->mParticipants) < 1) {
        $this->mDeleted = true;
      }
    }

    /**
     * Reads the given deck file and creates a deck from it
     */
    public function createMatchDeck($file) {
      $file = strval($file);
      $tsvData = file_get_contents($file);
      $tsvData = preg_split("/\n|\r|\r\n/", $tsvData);

      $minimumCardLimit = array(
        "STATEMENT" => self::MINIMUM_STATEMENT_CARDS,
        "OBJECT" => self::MINIMUM_OBJECT_CARDS,
        "VERB" => self::MINIMUM_VERB_CARDS
      );

      // Limit to 2000 cards
      $amount = min(count($tsvData), 2000);
      for ($i = 0; $i < $amount; $i++) {
        $line = trim($tsvData[$i]);
        if (empty($line)) {
          continue;
        }

        $tsv = preg_split("/\t/", $line);
        if (count($tsv) !== 2) {
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
            // Underscores on a non-statement card
            continue;
          }
          if ($underscores > 3) {
            // Too many underscores
            continue;
          }
        } else {
          if ($type === "STATEMENT") {
            // Statement card without underscores
            continue;
          }
        }

        Card::createForMatch($text, $type, $this);
        $minimumCardLimit[$type]--;
      }

      $noteGiven = false;
      foreach ($minimumCardLimit as $type => $value) {
        $orig = $value;
        while ($value-- > 0) {
          if (!$noteGiven) {
            $noteGiven = true;
            $this->getChat()->sendMessage("SYSTEM",
              "<b>Your deck is insufficient. ".
              "Placeholder cards have been added to the match.</b>");
          }
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
      if ($this->mState === "ENDING") {
        return false;
      }
      return !is_null($this->mCurrentCard);
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
      if ($this->mState === "PENDING") {
        return "Waiting for players...";
      } else if ($this->mState === "CHOOSING") {
        return "Players are choosing cards...";
      } else if ($this->mState === "PICKING") {
        $picker = "<unknown>";
        foreach ($this->mParticipants as $part) {
          if ($part->isPicking()) {
            $picker = $part->getName();
            break;
          }
        }
        return $picker." is picking a winner...";
      } else if ($this->mState === "COOLDOWN") {
        return "The next round is about to start...";
      } else if ($this->mState === "ENDING") {
        return "The match is ending...";
      }
      return "<State of Match unknown>";
    }

    /**
     *
     */
    private function setCurrentCard(Card $card) {
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
      $timer = intval($timer);
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
      $state = strval($state);

      $state = $this->onStateLeave($state);
      $this->mState = $state;
      $q = self::$sSqlQueries["modifyState"];
      $q->bindValue(":newstate", $this->mState, PDO::PARAM_STR);
      $q->bindValue(":match", $this->mId, PDO::PARAM_INT);
      $q->execute();
      $this->onStateEnter();
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
    public function refreshTimerIfNecessary() {
      if ($this->mState === "PENDING") {
        if ($this->mTimer - time() < self::PENDING_REFRESH_THRESHOLD) {
          if (count($this->mParticipants) < self::MINIMUM_PLAYERS) {
            $this->setTimer(time() + self::INITIAL_MATCH_TIMER);
            $this->getChat()->sendMessage("SYSTEM",
              "<b>There are not enough players, ".
              "the timer has been restarted!</b>");
          }
        }
      }
    }

    /**
     * Updates the state of this match if the needed conditions are met
     */
    public function updateState() {
      $timerUp = $this->mTimer <= time();
      if ($timerUp) {
        if ($this->mState === "PENDING") {
          $this->setState("CHOOSING");
        } else if ($this->mState === "CHOOSING") {
          $this->setState("PICKING");
        } else if ($this->mState === "PICKING") {
          $this->setState("COOLDOWN");
        } else if ($this->mState === "COOLDOWN") {
          $this->setState("CHOOSING");
        } else if ($this->mState === "ENDING") {
          $this->delete();
        }
      }

      if ($this->mState !== "PENDING" && $this->mState !== "ENDING") {
        if (count($this->mParticipants) < self::MINIMUM_PLAYERS) {
          $this->setState("ENDING");
        }
      }
    }

    /**
     * Called directly before leaving a state
     */
    private function onStateLeave($target) {
      if ($this->mState === "COOLDOWN") {
        // TODO check if match should end
      }
      return $target;
    }

    /**
     * Called directly after entering a state
     */
    private function onStateEnter() {
      if ($this->mState === "CHOOSING") {
        $this->selectNextPicker();
        $this->shuffleParticipantOrder();
        $this->selectMatchCard();
        foreach ($this->mParticipants as $part) {
          $part->getHand()->replenish();
        }
        $this->setTimer(time() + self::STATE_CHOOSING_TIME);
      } else if ($this->mState === "PICKING") {
        // TODO maybe check if a playable selection was submitted, otherwise
        // jump directly to cooldown?
        // TODO dynamic for amount of cards
        $this->setTimer(time() + self::STATE_PICKING_TIME);
      } else if ($this->mState === "COOLDOWN") {
        $this->setTimer(time() + self::STATE_COOLDOWN_TIME);
      } else if ($this->mState === "ENDING") {
        $this->setTimer(time() + self::STATE_ENDING_TIME);
        $this->getChat()->sendMessage("SYSTEM", "<b>Match is ending.</b>");
      }
    }

    /**
     * Select the next person to pick cards
     */
    private function selectNextPicker() {
      $first = $this->mParticipants[0];
      $next = false;
      foreach ($this->mParticipants as $part) {
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
     * Shuffles the order of the participants
     */
    private function shuffleParticipantOrder() {
      $order = range(1, count($this->mParticipants));
      shuffle($order);

      $n = count($order);
      for ($i = 0; $i < $n; $i++) {
        $this->mParticipants[$i]->assignOrder($order[$i]);
      }
    }

    /**
     * Selects a statement card for the match
     */
    private function selectMatchCard() {
      $card = Card::getRandomStatementForMatch($this);
      $this->setCurrentCard($card);
    }

    /**
     * Returns the number of gaps on the currently selected card (at least 1
     * at all times)
     */
    public function getCardGapCount() {
      if (is_null($this->mCurrentCard)) {
        return 1;
      }
      return max(1, substr_count($this->mCurrentCard->getText(), "_"));
    }

    /**
     * Checks whether the picked hand cards may be modified right now
     */
    public function canPickHandNow() {
      return $this->mState === "CHOOSING";
    }

    /**
     * Whether participants can see each others picks yet
     */
    public function canViewOthersPick() {
      return $this->mState === "PICKING" || $this->mState === "COOLDOWN";
    }

    /**
     * Checks if each player has chosen sufficiently many cards for choosing to
     * finish earlier and change the timer accordingly
     */
    public function checkIfChoosingDone() {
      $gaps = $this->getCardGapCount();
      $done = true;
      foreach ($this->mParticipants as $part) {
        if ($part->getHand()->getPickCount() !== $gaps) {
          $done = false;
          break;
        }
      }
      if (!$done) {
        return;
      }

      $timeLeft = $this->mTimer - time();
      if ($timeLeft > self::CHOOSING_FINAL_THRESHOLD) {
        $this->setTimer(time() + self::CHOOSING_FINAL_THRESHOLD);
      }
    }
  }
?>
