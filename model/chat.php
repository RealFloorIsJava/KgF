<?php
  /**
   * Represents the chat of a match
   */
  class Chat {
    /**
     * Prepared SQL queries
     */
    private static $sql_queries;
    /**
     * The match this chat belongs to
     */
    private $match;

    /**
     * Used to provide a DB handle and to initialize all the queries
     */
    public static function provideDB($dbh) {
      self::$sql_queries = array(
        "fetch_match_offset" => $dbh->prepare(
          "SELECT * ".
          "FROM `kgf_match_chat` ".
          "WHERE `chat_id` >= :offset ".
            "AND `chat_match_id` = :match ".
          "ORDER BY `chat_id` ASC"
        ),
        "add_message" => $dbh->prepare(
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
      $this->match = $match;
    }

    /**
     * Sends a chat message for the given match
     */
    public function send_message($type, $msg) {
      $q = self::$sql_queries["add_message"];
      $q->bindValue(":match", $this->match->get_id(), PDO::PARAM_INT);
      $q->bindValue(":type", $type, PDO::PARAM_STR);
      $q->bindValue(":message", $msg, PDO::PARAM_STR);
      $q->execute();
    }

    /**
     * Loads the chat messages of the given match from the given offset
     */
    public function load_for_match($offset) {
      $q = self::$sql_queries["fetch_match_offset"];
      $q->bindValue(":match", $this->match->get_id(), PDO::PARAM_INT);
      $q->bindValue(":offset", $offset, PDO::PARAM_INT);
      $q->execute();
      $rows = $q->fetchAll();

      $msgs = array();
      foreach ($rows as $msg) {
        $msgs[] = new ChatMessage($msg["chat_id"], $this->match,
          $msg["chat_type"], $msg["chat_message"]);
      }
      return $msgs;
    }
  }
?>
