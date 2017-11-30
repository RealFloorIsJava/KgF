<?php
  /**
   * Represents the chat of a match
   */
  class Chat {
    /**
     * Prepared SQL queries
     */
    private static $sSqlQueries;
    /**
     * The match this chat belongs to
     */
    private $mMatch;

    /**
     * Used to provide a DB handle and to initialize all the queries
     */
    public static function provideDB($dbh) {
      self::$sSqlQueries = array(
        "fetchMatchOffset" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_match_chat` ".
          "WHERE `chat_id` >= :offset ".
            "AND `chat_match_id` = :match ".
          "ORDER BY `chat_id` ASC"
        ),
        "addMessage" => $dbh->prepare(
          "INSERT INTO `kgf_match_chat` ".
            "(`chat_id`, `chat_match_id`, `chat_type`, `chat_message`) ".
          "VALUES (NULL, :match, :type, :message)"
        )
      );
    }

    /**
     * Constructor
     */
    public function __construct($match) {
      $this->mMatch = $match;
    }

    /**
     * Sends a chat message in this chat
     */
    public function sendMessage($type, $msg) {
      $q = self::$sSqlQueries["addMessage"];
      $q->bindValue(":match", $this->mMatch->getId(), PDO::PARAM_INT);
      $q->bindValue(":type", $type, PDO::PARAM_STR);
      $q->bindValue(":message", $msg, PDO::PARAM_STR);
      $q->execute();
    }

    /**
     * Loads the chat messages from the given offset
     */
    public function load($offset) {
      $q = self::$sSqlQueries["fetchMatchOffset"];
      $q->bindValue(":match", $this->mMatch->getId(), PDO::PARAM_INT);
      $q->bindValue(":offset", $offset, PDO::PARAM_INT);
      $q->execute();
      $rows = $q->fetchAll();

      $msgs = array();
      foreach ($rows as $msg) {
        $msgs[] = new ChatMessage($msg["chat_id"], $this->mMatch,
          $msg["chat_type"], $msg["chat_message"]);
      }
      return $msgs;
    }
  }
?>
