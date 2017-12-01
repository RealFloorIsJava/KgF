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
     * The match this card belongs to
     */
    private $mMatch;

    /**
     * Used to provide a DB handle and to initialize all the queries
     */
    public static function provideDB($dbh) {
      self::$sSqlQueries = array(
        "createForMatch" => $dbh->prepare(
          "INSERT INTO `kgf_cards` ".
            "(`card_id`, `card_text`, `card_type`, `card_match_id`) ".
          "VALUES (NULL, :text, :type, :match)"
        ),
        "getById" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_cards` ".
          "WHERE `card_id` = :id"
        )
      );
    }

    /**
     * Creates a card for the given match
     */
    public static function createForMatch($text, $type, $match) {
      $q = self::$sSqlQueries["createForMatch"];
      $q->bindValue(":text", $text, PDO::PARAM_STR);
      $q->bindValue(":type", $type, PDO::PARAM_STR);
      $q->bindValue(":match", $match->getId(), PDO::PARAM_INT);
      $q->execute();
    }

    public static function getByIdForMatch($id, $match) {
      if (isset(self::$sIdCache[$id])) {
        return self::$sIdCache[$id];
      }

      $q = self::$sSqlQueries["getById"];
      $q->bindValue(":id", $id, PDO::PARAM_INT);
      $q->execute();
      $row = $q->fetch();

      if (!$row) {
        return null;
      }

      return new Card($row["card_id"], $row["card_text"], $row["card_type"],
        $match);
    }

    /**
     * Checks whether the given card type is valid
     */
    public static function isValidType($type) {
      return $type === "STATEMENT" || $type === "OBJECT" || $type === "VERB";
    }

    /**
     * Private constructor to prevent instance creation
     */
    private function __construct($id, $text, $type, $match) {
      $this->mId = intval($id); //TODO
      $this->mText = $text;
      $this->mType = $type;
      $this->mMatch = $match;
      self::$sIdCache[$this->mId] = $this;
    }
  }
?>
