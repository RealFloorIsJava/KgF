<?php
  /**
   * Models a card in the hand of a participant
   */
  class HandCard {
    /**
     * Prepared SQL queries
     */
    private static $sSqlQueries;
    /**
     * The ID->Hand card cache
     */
    private static $sIdCache = array();
    /**
     * The ID of the hand card
     */
    private $mId;
    /**
     * The actual card
     */
    private $mCard;
    /**
     * The participant who owns this hand card
     */
    private $mParticipant;
    /**
     * The choice index of the card. This is NULL if the card is not chosen
     */
    private $mChosen;

    /**
     * Used to provide a DB handle and to initialize all the queries
     */
    public static function provideDB($dbh) {
      self::$sSqlQueries = array(
        "loadHand" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_hand` ".
          "WHERE `hand_participant` = :partid"
        ),
        "replenishCardType" => $dbh->prepare(
          "INSERT INTO `kgf_hand` ".
            "(`hand_id`, `hand_participant`, `hand_card`, `hand_choice`) ".
            "SELECT NULL, :partid, `card_id`, NULL ".
            "FROM `kgf_cards` ".
            "WHERE `card_id` NOT IN ( ".
              "SELECT `hand_card` ".
              "FROM `kgf_hand` ".
              "WHERE `hand_participant` = :partid ".
              ") AND `card_type` = :type ".
            "ORDER BY RAND() ".
            "LIMIT :num"
        ),
        "updateChoice" => $dbh->prepare(
          "UPDATE `kgf_hand` ".
          "SET `hand_choice` = :choice ".
          "WHERE `hand_id` = :handid"
        ),
        "deleteCard" => $dbh->prepare(
          "DELETE FROM `kgf_hand` ".
          "WHERE `hand_id` = :handid"
        )
      );
    }

    /**
     * Loads the hand of a participant
     */
    public static function loadHandCards(Participant $participant) {
      $q = self::$sSqlQueries["loadHand"];
      $q->bindValue(":partid", $participant->getId(), PDO::PARAM_INT);
      $q->execute();

      $rows = $q->fetchAll();
      $res = array();
      foreach ($rows as $row) {
        if (!isset(self::$sIdCache[$row["hand_id"]])) {
          $res[$row["hand_id"]] = new HandCard($row, array(
            "participant" => $participant
          ));
        } else {
          $res[$row["hand_id"]] = self::$sIdCache[$row["hand_id"]];
        }
      }
      return $res;
    }

    /**
     * Replenishes the hand for the given participant with the given number of
     * cards of the given type
     */
    public static function replenishHandFor(Participant $participant, $type,
        $num) {
      $type = strval($type);
      $num = intval($num);
      $q = self::$sSqlQueries["replenishCardType"];
      $q->bindValue(":partid", $participant->getId(), PDO::PARAM_INT);
      $q->bindValue(":type", $type, PDO::PARAM_STR);
      $q->bindValue(":num", $num, PDO::PARAM_INT);
      $q->execute();
    }

    /**
     * Private constructor to prevent instance creation
     */
    private function __construct(array $row, array $kwargs = array()) {
      $this->mId = intval($row["hand_id"]);

      self::$sIdCache[$this->mId] = $this;

      $this->mChosen = is_null($row["hand_choice"])
        ? null
        : intval($row["hand_choice"]);

      assert(isset($kwargs["participant"]), "participant has to be supplied");
      $this->mParticipant = $kwargs["participant"];

      $this->mCard = Card::getByIdForMatch($row["hand_card"],
        $this->mParticipant->getMatch());
    }

    /**
     * Card getter
     */
    public function getCard() {
      return $this->mCard;
    }

    /**
     * Checks whether this card is chosen
     */
    public function isChosen() {
      return !is_null($this->mChosen);
    }

    /**
     * Fetches the choice id of this card
     */
    public function getChoiceId() {
      return $this->mChosen;
    }

    /**
     * Chooses this card
     */
    public function choose($requestedChoiceId) {
      $requestedChoiceId = intval($requestedChoiceId);
      if ($this->isChosen()) {
        return;
      }
      $q = self::$sSqlQueries["updateChoice"];
      $q->bindValue(":handid", $this->mId, PDO::PARAM_INT);
      $q->bindValue(":choice", $requestedChoiceId, PDO::PARAM_INT);
      $q->execute();

      $this->mChosen = $requestedChoiceId;
    }

    /**
     * Unchooses this card
     */
    public function unchoose() {
      if (!$this->isChosen()) {
        return;
      }
      $q = self::$sSqlQueries["updateChoice"];
      $q->bindValue(":handid", $this->mId, PDO::PARAM_INT);
      $q->bindValue(":choice", null, PDO::PARAM_INT);
      $q->execute();

      $this->mChosen = null;
    }

    /**
     * Deletes this hand card
     */
    public function delete() {
      $q = self::$sSqlQueries["deleteCard"];
      $q->bindValue(":handid", $this->mId, PDO::PARAM_INT);
      $q->execute();

      unset(self::$sIdCache[$this->mId]);
    }
  }
?>
