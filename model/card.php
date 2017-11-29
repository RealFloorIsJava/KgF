<?php
  /**
   * Models one specific card
   */
  class Card {
    /**
     * Prepared SQL queries
     */
    private static $sSqlQueries;
    /**
     * The ID->Card cache
     */
    private static $sIdCache = array();
    /**
     * The ID of this card
     */
    private $mId;
    /**
     * The text on this card
     */
    private $mText;
    /**
     * The type of this card
     * One of STATEMENT VERB OBJECT
     */
    private $mType;

    /**
     * Used to provide a DB handle and to initialize all the queries
     */
    public static function provideDB($dbh) {
      self::$sSqlQueries = array(
        "allCards" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_cards`"
        ),
        "getCard" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_cards` ".
          "WHERE `card_id` = :cardid"
        ),
        "deleteCard" => $dbh->prepare(
          "DELETE FROM `kgf_cards` ".
          "WHERE `card_id` = :cardid"
        ),
        "setCardMode" => $dbh->prepare(
          "UPDATE `kgf_cards` ".
          "SET `card_type` = :cardtype ".
          "WHERE `card_id` = :cardid"
        ),
        "randomCard" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_cards` ".
          "WHERE `card_type` = :cardtype ".
          "ORDER BY RAND() ".
          "LIMIT 1"
        )
      );
    }

    /**
     * Fetches all cards in the DB
     */
    public static function getAllCards() {
      // There is no real efficient way to only load the cards the cache is
      // missing. So in this case, we'll load them all.
      $q = self::$sSqlQueries["allCards"];
      $q->execute();
      $rows = $q->fetchAll();

      $cards = array();
      foreach ($rows as $card) {
        // We'll take those that we already have cached from the cache
        $id = $card["card_id"];
        if (!isset(self::$sIdCache[$id])) {
          self::$sIdCache[$id] = new Card($card["card_id"], $card["card_text"],
            $card["card_type"]);
        }
        $cards[$id] = self::$sIdCache[$id];
      }
      return $cards;
    }

    /**
     * Fetches one card from the DB
     */
    public static function getCard($id) {
      if (!isset(self::$sIdCache[$id])) {
        $q = self::$sSqlQueries["getCard"];
        $q->bindValue(":cardid", $id, PDO::PARAM_INT);
        $q->execute();
        $card = $q->fetch();
        self::$sIdCache[$id] = new Card($card["card_id"], $card["card_text"],
          $card["card_type"]);
      }
      return self::$sIdCache[$id];
    }

    /**
     * Returns a random card of the given type
     */
    public static function randomCard($type) {
      $q = self::$sSqlQueries["randomCard"];
      $q->bindValue(":cardtype", $type, PDO::PARAM_STR);
      $q->execute();
      $card = $q->fetch();
      if (!isset(self::$sIdCache[$card["card_id"]])) {
        self::$sIdCache[$card["card_id"]] = new Card($card["card_id"],
          $card["card_text"], $card["card_type"]);
      }
      return self::$sIdCache[$card["card_id"]];
    }

    /**
     * Private constructor to prevent instance creation
     */
    private function __construct($id, $text, $type) {
      $this->mId = intval($id);
      $this->mText = $text;
      $this->mType = $type;
    }

    /**
     * Deletes this card
     */
    public function deleteCard() {
      $q = self::$sSqlQueries["deleteCard"];
      $q->bindValue(":cardid", $this->mId, PDO::PARAM_INT);
      $q->execute();
      unset(self::$sIdCache[$this->mId]);
    }

    /**
     * Changes the mode of this card
     */
    public function setMode($type) {
      $this->mType = $type;
      $q = self::$sSqlQueries["setCardMode"];
      $q->bindValue(":cardid", $this->mId, PDO::PARAM_INT);
      $q->bindValue(":cardtype", $this->mType, PDO::PARAM_STR);
      $q->execute();
    }

    /**
     * Returns the name of the CSS type class
     */
    public function getTypeClass() {
      if ($this->mType === "STATEMENT") {
        return "statement-card";
      } else if ($this->mType === "OBJECT") {
        return "object-card";
      } else if ($this->mType === "VERB") {
        return "verb-card";
      }
      return "unknown";
    }

    /**
     * Returns the HTML-formatted text of the card
     */
    public function getFormattedText() {
      return preg_replace("/_/",
        "<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>",
        $this->mText);
    }

    /**
     * ID getter
     */
    public function getId() {
      return $this->mId;
    }
  }
?>
