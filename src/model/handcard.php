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
     * The pick index of the card. This is NULL if the card is not picked
     */
    private $mPicked;

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
            "(`hand_id`, `hand_participant`, `hand_card`, `hand_pick`) ".
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
        "updatePick" => $dbh->prepare(
          "UPDATE `kgf_hand` ".
          "SET `hand_pick` = :pick ".
          "WHERE `hand_id` = :handid"
        )
      );
    }

    /**
     * Loads the hand of a participant
     */
    public static function loadHandCards($participant) {
      $q = self::$sSqlQueries["loadHand"];
      $q->bindValue(":partid", $participant->getId(), PDO::PARAM_INT);
      $q->execute();

      $rows = $q->fetchAll();
      $res = array();
      foreach ($rows as $row) {
        if (!isset(self::$sIdCache[$row["hand_id"]])) {
          $res[$row["hand_id"]] = new HandCard($row["hand_id"], $participant,
            Card::getByIdForMatch($row["hand_card"], $participant->getMatch()),
            $row["hand_pick"]);
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
    public static function replenishHandFor($participant, $type, $num) {
      $q = self::$sSqlQueries["replenishCardType"];
      $q->bindValue(":partid", $participant->getId(), PDO::PARAM_INT);
      $q->bindValue(":type", $type, PDO::PARAM_STR);
      $q->bindValue(":num", $num, PDO::PARAM_INT);
      $q->execute();
    }

    /**
     * Private constructor to prevent instance creation
     */
    private function __construct($id, $participant, $card, $pickId) {
      $this->mId = $id;
      $this->mCard = $card;
      $this->mParticipant = $participant;
      $this->mPicked = $pickId;

      self::$sIdCache[$this->mId] = $this;
    }

    /**
     * Card getter
     */
    public function getCard() {
      return $this->mCard;
    }

    /**
     * Checks whether this card is picked
     */
    public function isPicked() {
      return !is_null($this->mPicked);
    }

    /**
     * Fetches the pick id of this card
     */
    public function getPickId() {
      return $this->mPicked;
    }

    /**
     * Picks this card
     */
    public function pick($requestedPickId) {
      if ($this->isPicked()) {
        return;
      }
      $q = self::$sSqlQueries["updatePick"];
      $q->bindValue(":handid", $this->mId, PDO::PARAM_INT);
      $q->bindValue(":pick", $requestedPickId, PDO::PARAM_INT);
      $this->mPicked = $requestedPickId;
      $q->execute();
    }

    /**
     * Unpicks this card
     */
    public function unpick() {
      if (!$this->isPicked()) {
        return;
      }
      $q = self::$sSqlQueries["updatePick"];
      $q->bindValue(":handid", $this->mId, PDO::PARAM_INT);
      $q->bindValue(":pick", null, PDO::PARAM_INT);
      $this->mPicked = null;
      $q->execute();
    }
  }
?>
