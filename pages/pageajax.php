<?php
  /**
   * This class handles AJAX requests that do not fit to a certain page but
   * rather might be used anywhere.
   */
  class PageAjax extends Page {
    /**
     * The action that was required
     */
    private $mAction;

    /**
     * Constructor
     */
    public function __construct($user) {
      parent::__construct($user);
      $this->mAction = isset($_GET["action"]) ? $_GET["action"] : "invalid";
    }

    /**
     * Displays this page. For the AJAX handler this is only dispatching
     * the request to handler methods.
     */
    public function display() {
      $this->processAction();
    }

    /**
     * Dispatcher for the more specific handler methods
     */
    private function processAction() {
      if ($this->mAction === "settheme") {
        $this->actionSetTheme();
      } else if ($this->mAction === "escalate") {
        $this->actionEscalate();
      } else if ($this->mAction === "rename") {
        $this->actionRename();
      }
    }

    /**
     * Renames the current user
     */
    private function actionRename() {
      // A name may not be empty and has to be shorter than 32 characters
      if (isset($_POST['name'])) {
        $name = htmlspecialchars($_POST['name']);
        if ($name !== "" && strlen($name) < 32) {
          $this->mUser->setNickname($name);
        }
      }
    }

    /**
     * Escalates user privileges to admin (manager) privileges when the correct
     * manager password is given.
     */
    private function actionEscalate() {
      if (isset($_POST['token'])) {
        $token = sha1($_POST['token']);
        $correct_token = trim(file_get_contents("config/mgr_password"));
        if ($token === $correct_token) {
          $this->mUser->escalatePrivileges();
        }
      }
    }

    /**
     * Sets the theme for the user
     */
    private function actionSetTheme() {
      if (isset($_POST["selection"])) {
        $new_theme = $_POST["selection"];
        if ($new_theme === "dark" || $new_theme === "light") {
          $this->mUser->setTheme($new_theme);
        }
      }
    }
  }
?>
