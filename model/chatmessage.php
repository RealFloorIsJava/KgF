<?php
  /**
   * Represents a chat message
   */
  class ChatMessage {
    /**
     * The ID of this participant
     */
    private $mId;
    /**
     * The match of this message
     */
    private $mMatch;
    /**
     * The type of this message
     */
    private $mType;
    /**
     * The message
     */
    private $mMessage;

    /**
     * Constructor
     */
    public function __construct($id, $match, $type, $message) {
      $this->mId = intval($id);
      $this->mMatch = $match;
      $this->mType = $type;
      $this->mMessage = $message;
    }

    /**
     * ID getter
     */
    public function getId() {
      return $this->mId;
    }

    /**
     * Type getter
     */
    public function getType() {
      return $this->mType;
    }

    /**
     * Message getter
     */
    public function getMessage() {
      return $this->mMessage;
    }
  }
?>
