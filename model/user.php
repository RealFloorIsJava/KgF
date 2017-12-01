<?php
  /**
   * Represents a user (logged in) and all associated data
   */
  class User {
    /**
     * The ID of the user, has to be unique
     */
    private $mId;
    /**
     * The theme of this user
     */
    private $mTheme;
    /**
     * The nickname of this user
     */
    private $mNickname;
    /**
     * The next point in time when a message is allowed to prevent spam
     */
    private $mChatCooldown;

    public function __construct() {
      $this->mId = uniqid("p", true);
      $this->mTheme = "dark";
      $this->mNickname = "Meme".rand(10000, 99999);
      $this->mChatCooldown = 0;
    }

    /**
     * Fetches the theme loader, HTML that will initialize the user's theme
     */
    public function getThemeLoader() {
      $loader = '<link rel="stylesheet" type="text/css" href="/css/'.
        $this->mTheme.'.css" id="theme">';
      $loader .= '<script type="text/javascript"> var theme = "'.$this->mTheme.
        '"; </script>';
      return $loader;
    }

    /**
     * Theme setter
     */
    public function setTheme($theme) {
      $this->mTheme = $theme;
    }

    /**
     * Nick setter
     */
    public function setNickname($name) {
      $this->mNickname = $name;
    }

    /**
     * Nick getter
     */
    public function getNickname() {
      return $this->mNickname;
    }

    /**
     * ID getter
     */
    public function getId() {
      return $this->mId;
    }

    /**
     * Checks whether the anti spam prevents this user from chatting
     */
    public function mayChat() {
      return time() >= $this->mChatCooldown;
    }

    /**
     * Prevents chatting until the given point in time has passed
     */
    public function preventChatUntil($time) {
      $this->mChatCooldown = $time;
    }
  }
?>
