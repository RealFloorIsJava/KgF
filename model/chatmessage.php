<?php
  /**
   * Represents a chat message
   */
  class ChatMessage {
    /**
     * The ID of this participant
     */
    private $id;
    /**
     * The match of this message
     */
    private $match;
    /**
     * The type of this message
     */
    private $type;
    /**
     * The message
     */
    private $message;

    /**
     * Constructor
     */
    public function __construct($id, $match, $type, $message) {
      $this->id = intval($id);
      $this->match = $match;
      $this->type = $type;
      $this->message = $message;
    }

    /**
     * ID getter
     */
    public function get_id() {
      return $this->id;
    }

    /**
     * Type getter
     */
    public function get_type() {
      return $this->type;
    }

    /**
     * Message getter
     */
    public function get_message() {
      return $this->message;
    }
  }
?>
