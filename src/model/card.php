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
        ),
        "randomStatement" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_cards` ".
          "WHERE `card_match_id` = :match ".
            "AND `card_type` = 'STATEMENT' ".
          "ORDER BY RAND()"
        )
      );
    }

    /**
     * Creates a card for the given match
     */
    public static function createForMatch($text, $type, Match $match) {
      $text = strval($text);
      $type = strval($type);
      $q = self::$sSqlQueries["createForMatch"];
      $q->bindValue(":text", $text, PDO::PARAM_STR);
      $q->bindValue(":type", $type, PDO::PARAM_STR);
      $q->bindValue(":match", $match->getId(), PDO::PARAM_INT);
      $q->execute();
    }

    /**
     * Fetches a card by its ID for the given match
     */
    public static function getByIdForMatch($id, Match $match) {
      $id = intval($id);
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

      return new Card($row, array(
        "match" => $match
      ));/*$row["card_id"], $row["card_text"], $row["card_type"],
        $match);*/
    }

    /**
     * Fetches a random statement card for the given match
     */
    public static function getRandomStatementForMatch(Match $match) {
      $q = self::$sSqlQueries["randomStatement"];
      $q->bindValue(":match", $match->getId(), PDO::PARAM_INT);
      $q->execute();
      $row = $q->fetch();
      if (!$row) {
        return null;
      }

      if (isset(self::$sIdCache[$row["card_id"]])) {
        return self::$sIdCache[$id];
      }

      return new Card($row, array(
        "match" => $match
      ));
    }

    /**
     * Checks whether the given card type is valid
     */
    public static function isValidType($type) {
      $type = strval($type);
      return $type === "STATEMENT" || $type === "OBJECT" || $type === "VERB";
    }

    /**
     * Private constructor to prevent instance creation
     */
    private function __construct(array $row, array $kwargs = array()) {
      $this->mId = intval($row["card_id"]);

      self::$sIdCache[$this->mId] = $this;

      $this->mText = $row["card_text"];
      $this->mType = $row["card_type"];

      assert(isset($kwargs["match"]), "match has to be supplied");
      $this->mMatch = $kwargs["match"];
    }

    /**
     * ID getter
     */
    public function getId() {
      return $this->mId;
    }

    /**
     * ID getter
     */
    public function getText() {
      return $this->mText;
    }

    /**
     * Type getter
     */
    public function getType() {
      return $this->mType;
    }
  }
?>
