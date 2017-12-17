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
    public function __construct(array $row) {
      $this->mId = intval($row["chat_id"]);
      $this->mType = $row["chat_type"];
      $this->mMessage = $row["chat_message"];
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
